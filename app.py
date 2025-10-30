from flask import Flask, render_template, request, redirect, url_for
import sqlite3, os

app = Flask(__name__)
DB_PATH = "vaccination.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS vaccination(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT, 
                        age INTEGER, 
                        vaccine TEXT, 
                        date TEXT)''')
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    data = conn.execute("SELECT * FROM vaccination").fetchall()
    conn.close()
    return render_template('index.html', data=data)

@app.route('/add', methods=['POST'])
def add():
    name, age, vaccine, date = request.form.values()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO vaccination(name, age, vaccine, date) VALUES(?, ?, ?, ?)",
                 (name, age, vaccine, date))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM vaccination WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

    
