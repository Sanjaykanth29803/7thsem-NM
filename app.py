from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__, template_folder='templates', static_folder='static')
DB_PATH = 'vaccination.db'

# Home route
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    data = conn.execute("SELECT * FROM vaccination").fetchall()
    conn.close()
    return render_template('index.html', data=data)

# Add new record
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        vaccine = request.form['vaccine']
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO vaccination (name, age, vaccine) VALUES (?, ?, ?)", (name, age, vaccine))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)
