import io
import os
import re
import psycopg2
from pypdf import PdfReader
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


def chunk_policy_file_from_db(conn, file_id):
    cur = conn.cursor()
    cur.execute("SELECT filename, content FROM policy_files WHERE file_id = %s", (file_id,))
    filename, content = cur.fetchone()

    reader = PdfReader(io.BytesIO(bytes(content)))
    full_text = "\n".join((page.extract_text() or "") for page in reader.pages)

    parts = re.split(r"===\s*(.+?)\s*===", full_text)
    rows = []
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip()
        if not body:
            continue
        slug = heading.lower().replace(" ", "_")
        doc_id = f"policy:{filename}:{i}:{slug}"
        rows.append((doc_id, filename, heading, body))

    execute_values(cur, """
        INSERT INTO policies (doc_id, title, section, body)
        VALUES %s
        ON CONFLICT (doc_id) DO UPDATE SET
            title = EXCLUDED.title, section = EXCLUDED.section, body = EXCLUDED.body, updated_at = now()
    """, rows)
    conn.commit()
    print(f"Chunked {len(rows)} sections from {filename}")


if __name__ == "__main__":
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()
    cur.execute("SELECT file_id FROM policy_files")
    file_ids = [r[0] for r in cur.fetchall()]
    print(f"Found {len(file_ids)} file(s) in policy_files: {file_ids}")
    for file_id in file_ids:
        chunk_policy_file_from_db(conn, file_id)
    conn.close()