import io
import re
from pypdf import PdfReader
from pyscopg2.extras import execute_values



def split_with_overlap(text, max_words=225, overlap_words=40):
    words = text.split()
    if len(words) <= max_words:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        start = end - overlap_words
    return chunks

def chunk_policy(conn,file_id):
    cur=conn.cursor()
    cur.execute("SELECT content FROM policy_files WHERE file_id=%s",(file_id,))
    file_name,content=cur.fetchone()
    reader=PdfReader(io.BytesIO(bytes(content)))
    full_text="\n".join(page.extract_text() for page in reader.pages)

    parts = re.split(r"===\s*(.+?)\s*===", full_text)
    rows=[]
    for i in range(1,len(parts),2):
        header=parts[i].strip()
        body=parts[i+1].strip()
        if not body:
            continue
        sub_bodies = split_with_overlap(body)
        sub_bodies = split_with_overlap(body)
        for j, sub_body in enumerate(sub_bodies):
            doc_id=f"{file_id}:{i//2+1}:{j+1}"
            rows.append((doc_id,header,sub_body))
   
    execute_values(cur, """
        INSERT INTO policies (doc_id, title, section, body)
        VALUES %s
        ON CONFLICT (doc_id) DO UPDATE SET
            title = EXCLUDED.title, section = EXCLUDED.section, body = EXCLUDED.body, updated_at = now()
    """, rows)
    conn.commit()
    print(f"Chunked {len(rows)} sections from {file_name}")
