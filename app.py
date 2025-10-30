from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "vaccination.db"


# ✅ Initialize database (for both production & test)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully — children table is ready!")


# ✅ Home Page - Show all children
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children")
    data = cursor.fetchall()
    conn.close()
    return render_template('index.html', data=data)


# ✅ Add Child Page
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        phone = request.form['phone']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO children (name, dob, phone) VALUES (?, ?, ?)", (name, dob, phone))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('add.html')


# ✅ Vaccine Schedule Page
@app.route('/vaccine_schedule')
def vaccine_schedule():
    schedule = [
        {"age": "At Birth", "vaccine": "BCG, Hepatitis B, OPV"},
        {"age": "6 Weeks", "vaccine": "DTP, IPV, Hib, Rotavirus"},
        {"age": "10 Weeks", "vaccine": "DTP, IPV, Hib, Rotavirus"},
        {"age": "14 Weeks", "vaccine": "DTP, IPV, Hib, PCV"},
        {"age": "9 Months", "vaccine": "Measles, MMR"},
        {"age": "15 Months", "vaccine": "Varicella, Hepatitis A"},
    ]
    return render_template('vaccine_schedule.html', schedule=schedule)


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True)
