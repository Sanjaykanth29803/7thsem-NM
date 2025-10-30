from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os

app = Flask(__name__)
app.secret_key = "secret-key"
DB_PATH = "vaccination.db"

# Create table if not exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS vaccination(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        age INTEGER,
                        vaccine TEXT,
                        date TEXT)''')
    conn.commit()
    conn.close()

# ✅ Always run at startup (even on Render)
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    data = conn.execute("SELECT * FROM vaccination").fetchall()
    conn.close()
    return render_template('index.html', data=data)

@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    age = request.form['age']
    vaccine = request.form['vaccine']
    date = request.form['date']

    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO vaccination (name, age, vaccine, date) VALUES (?, ?, ?, ?)",
                 (name, age, vaccine, date))
    conn.commit()
    conn.close()

    flash("Record added successfully!")
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM vaccination WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Record deleted!")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
