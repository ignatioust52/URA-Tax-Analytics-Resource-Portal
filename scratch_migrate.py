import os
from core.db import get_db_connection

sql = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='public_resources' AND column_name='youtube_url') THEN
        ALTER TABLE public_resources ADD COLUMN youtube_url TEXT;
    END IF;
END $$;
"""

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
print("Migration applied")
