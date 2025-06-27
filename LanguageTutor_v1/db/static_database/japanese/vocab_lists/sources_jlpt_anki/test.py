import sqlite3

DB_PATH = "LanguageTutor_v1/db/static_database/japanese/vocab_lists/sources_jlpt_anki/n4/collection.anki2"  # update this path

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT n.flds
        FROM notes n
        LIMIT 10
    """)
    
    for idx, (flds,) in enumerate(cur.fetchall(), start=1):
        fields = flds.split('\x1f')
        print(f"Note {idx}:")
        for i, field in enumerate(fields, start=1):
            print(f"  Field {i}: {field}")
        print("-" * 40)

    conn.close()

if __name__ == "__main__":
    main()
