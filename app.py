from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "vaccination.db"

# ✅ Initialize Database
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


# ✅ Base CSS (Embedded)
base_css = """
<style>
body {
    font-family: Arial, sans-serif;
    background-color: #eef6f9;
    margin: 0;
    padding: 0;
}
.container {
    width: 80%;
    margin: 30px auto;
    background: #fff;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 0 10px #aaa;
}
h1 {
    text-align: center;
    color: #2b6777;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}
th, td {
    padding: 12px;
    border: 1px solid #ddd;
    text-align: center;
}
th {
    background-color: #52ab98;
    color: white;
}
tr:nth-child(even) {
    background-color: #f9f9f9;
}
.btn, .btn-back, .btn-secondary {
    display: inline-block;
    padding: 10px 20px;
    margin: 10px 5px;
    border-radius: 5px;
    text-decoration: none;
    color: white;
    background-color: #2b6777;
}
.btn:hover, .btn-back:hover, .btn-secondary:hover {
    background-color: #52ab98;
}
form {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
input {
    padding: 8px;
    border-radius: 5px;
    border: 1px solid #ccc;
}
</style>
"""

# ✅ Home Page
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children")
    data = cursor.fetchall()
    conn.close()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vaccination Records</title>
        {base_css}
    </head>
    <body>
        <div class="container">
            <h1>Child Vaccination Records</h1>
            <a href="{{{{ url_for('add') }}}}" class="btn">➕ Add New Record</a>
            <a href="{{{{ url_for('vaccine_schedule') }}}}" class="btn-secondary">📅 Vaccine Schedule</a>
            <table>
                <tr><th>ID</th><th>Name</th><th>DOB</th><th>Phone</th></tr>
                {''.join(f"<tr><td>{row['id']}</td><td>{row['name']}</td><td>{row['dob']}</td><td>{row['phone']}</td></tr>" for row in data)}
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


# ✅ Add Child Record
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

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Record</title>
        {base_css}
    </head>
    <body>
        <div class="container">
            <h1>Add Child Vaccination Record</h1>
            <form method="POST">
                <label>Child Name:</label>
                <input type="text" name="name" required>
                <label>Date of Birth:</label>
                <input type="date" name="dob" required>
                <label>Phone:</label>
                <input type="text" name="phone" required>
                <button type="submit" class="btn">Save</button>
                <a href="{{{{ url_for('index') }}}}" class="btn-back">Cancel</a>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


# ✅ Vaccine Schedule
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

    table_rows = ''.join(f"<tr><td>{s['age']}</td><td>{s['vaccine']}</td></tr>" for s in schedule)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vaccine Schedule</title>
        {base_css}
    </head>
    <body>
        <div class="container">
            <h1>Vaccine Schedule</h1>
            <table>
                <tr><th>Age</th><th>Vaccine</th></tr>
                {table_rows}
            </table>
            <a href="{{{{ url_for('index') }}}}" class="btn-back">🏠 Back</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


# ✅ Run app
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True)
