import sqlite3

conn = sqlite3.connect('vaccination.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS vaccination (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    vaccine TEXT
);
''')
conn.close()

print("Database initialized successfully!")
