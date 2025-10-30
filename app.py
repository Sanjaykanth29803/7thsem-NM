from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "supersecretkey"
DB_PATH = 'vaccination.db'

# ---------- Helper Function ----------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Home Page ----------
@app.route('/')
def index():
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM vaccination").fetchall()
    conn.close()
    return render_template('index.html', data=data)

# ---------- Add New Record ----------
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        vaccine = request.form['vaccine']

        if not name or not age or not vaccine:
            flash("All fields are required!", "error")
            return redirect(url_for('add'))

        conn = get_db_connection()
        conn.execute("INSERT INTO vaccination (name, age, vaccine) VALUES (?, ?, ?)",
                     (name, age, vaccine))
        conn.commit()
        conn.close()
        flash("Child record added successfully!", "success")
        return redirect(url_for('index'))
    return render_template('add.html')

# ---------- Edit Record ----------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()
    record = conn.execute("SELECT * FROM vaccination WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        vaccine = request.form['vaccine']

        conn.execute("UPDATE vaccination SET name = ?, age = ?, vaccine = ? WHERE id = ?",
                     (name, age, vaccine, id))
        conn.commit()
        conn.close()
        flash("Record updated successfully!", "success")
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit.html', record=record)

# ---------- Delete Record ----------
@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM vaccination WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Record deleted successfully!", "success")
    return redirect(url_for('index'))

# ---------- Run Application ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render-compatible port
    app.run(host='0.0.0.0', port=port)
