CREATE OR REPLACE FUNCTION notify_content_change() RETURNS trigger AS $$
DECLARE
  pk_value text;
BEGIN
  IF TG_OP = 'DELETE' THEN
    pk_value := (row_to_json(OLD)->>TG_ARGV[0]);
  ELSE
    pk_value := (row_to_json(NEW)->>TG_ARGV[0]);
  END IF;
  PERFORM pg_notify('content_changes', TG_ARGV[1] || ':' || TG_OP || ':' || pk_value);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER products_notify_change
AFTER INSERT OR UPDATE OR DELETE ON products
FOR EACH ROW EXECUTE FUNCTION notify_content_change('item_id', 'products');

CREATE TRIGGER reviews_notify_change
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION notify_content_change('id', 'reviews');

CREATE TRIGGER policies_notify_change
AFTER INSERT OR UPDATE OR DELETE ON policies
FOR EACH ROW EXECUTE FUNCTION notify_content_change('doc_id', 'policies');