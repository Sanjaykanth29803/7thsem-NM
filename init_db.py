import sqlite3

DB_PATH = 'vaccination.db'

# Connect to database (it will create the file if it doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create the vaccination table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vaccination (
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        vaccine TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

print("✅ Database initialized successfully — vaccination table is ready!")
