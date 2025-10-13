from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file, get_flashed_messages
import sqlite3
from datetime import datetime, timedelta
import io
import csv
app = Flask(__name__)
app.secret_key = "replace-this-with-a-secure-key" 
DB_PATH = "vaccinations.db"

vaccine_schedule = [
    {"vaccine": "BCG", "age_days": 0},
    {"vaccine": "Hepatitis B", "age_days": 0},
    {"vaccine": "OPV 0", "age_days": 0},
    {"vaccine": "DPT 1", "age_days": 42},
    {"vaccine": "OPV 1", "age_days": 42},
    {"vaccine": "DPT 2", "age_days": 70},
    {"vaccine": "OPV 2", "age_days": 70},
    {"vaccine": "DPT 3", "age_days": 98},
    {"vaccine": "OPV 3", "age_days": 98},
    {"vaccine": "Measles 1", "age_days": 270},
    {"vaccine": "Measles 2", "age_days": 450}
]
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT,
            parent TEXT,
            phone TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS vaccinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            vaccine TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Upcoming', -- 'Upcoming' or 'Done'
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(child_id) REFERENCES children(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def create_schedule_for_child(conn, child_id, dob_str):
    """
    Create vaccination rows for the child based on dob_str (YYYY-MM-DD).
    Deletes existing schedule first.
    """
    c = conn.cursor()
    c.execute('DELETE FROM vaccinations WHERE child_id=?', (child_id,))
    
    if not dob_str:
        conn.commit()
        return
        
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d')
    except Exception:
        conn.commit()
        return
        
    today = datetime.today()
    for v in vaccine_schedule:
        due = dob + timedelta(days=v['age_days'])
        # Check if the vaccine is already past due relative to today's date
        status = 'Done' if today.date() >= due.date() and v['age_days'] > 0 else 'Upcoming'
        # For vaccines due on day 0, assume upcoming until marked done
        if v['age_days'] == 0:
            status = 'Upcoming'

        c.execute('''
            INSERT INTO vaccinations (child_id, vaccine, due_date, status)
            VALUES (?,?,?,?)
        ''', (child_id, v['vaccine'], due.strftime('%Y-%m-%d'), status))
    conn.commit()

def get_next_vaccine_for_template(child_id):
    """
    Helper function to get the next upcoming vaccine for a child.
    """
    conn = get_conn()
    c = conn.cursor()
    row = c.execute('''
        SELECT id, vaccine, due_date, status 
        FROM vaccinations
        WHERE child_id=? AND status='Upcoming' 
        ORDER BY date(due_date) ASC
        LIMIT 1
    ''', (child_id,)).fetchone()
    conn.close()
    
    if row:
        try:
            due_date_fmt = datetime.strptime(row['due_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
        except Exception:
            due_date_fmt = row['due_date']
        return {'id': row['id'], 'vaccine': row['vaccine'], 'due_date': row['due_date'], 'due_date_fmt': due_date_fmt}
    return None

def get_vaccination_stats():
    """
    Calculates overall vaccination statistics for the reports page.
    """
    conn = get_conn()
    c = conn.cursor()

    status_counts = c.execute("SELECT status, COUNT(*) as count FROM vaccinations GROUP BY status").fetchall()
    stats = {row['status']: row['count'] for row in status_counts}
    
    total_vaccines = sum(stats.values())
    done_count = stats.get('Done', 0)
    upcoming_count = stats.get('Upcoming', 0)
    
    today = datetime.today().date().isoformat()
    overdue_count = c.execute("""
        SELECT COUNT(*) as count FROM vaccinations
        WHERE status='Upcoming' AND date(due_date) < date(?)
    """, (today,)).fetchone()['count']
    
    conn.close()
    
    completion_rate = (done_count / total_vaccines * 100) if total_vaccines > 0 else 0

    return {
        'total_vaccines': total_vaccines,
        'done_count': done_count,
        'upcoming_count': upcoming_count,
        'overdue_count': overdue_count,
        'completion_rate': f"{completion_rate:.1f}%"
    }

def send_mock_sms_reminder(child_name, phone, vaccine, due_date_fmt):
    """
    Mocks the process of sending an SMS reminder.
    In a real application, this is where a Twilio/Vonage API call would go.
    """
    if not phone:
        return (False, f"ERROR: No phone number registered for {child_name}.")

    message = (
        f"Reminder for {child_name}: "
        f"The next vaccine is {vaccine}, due on {due_date_fmt}. "
        "Please schedule your visit. Thank you!"
    )
    
    print("-" * 50)
    print(f"MOCK SMS SENT to: {phone}")
    print(f"Child: {child_name}")
    print(f"Message: {message}")
    print("-" * 50)


    return (True, f"SMS reminder for {vaccine} successfully 'sent' to {phone}.")



@app.route('/')
def home():
    def get_flashed_messages_py(with_categories=False, category_filter=[]):
        return get_flashed_messages(with_categories=with_categories, category_filter=category_filter)
        
    q = request.args.get('q', '').strip()
    conn = get_conn()
    if q:
        rows = conn.execute(
            "SELECT * FROM children WHERE name LIKE ? OR parent LIKE ? OR phone LIKE ? ORDER BY created_at DESC",
            (f'%{q}%', f'%{q}%', f'%{q}%')
        ).fetchall()
    else:
        rows = conn.execute('SELECT * FROM children ORDER BY created_at DESC').fetchall()
    conn.close()

    home_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width,initial-scale=1'>
      <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
      <style>
        /* Light and Calm Blue-Green Gradient Theme */
        body{font-family:'Poppins',sans-serif;padding:20px;background:linear-gradient(135deg,#a8dadc,#457b9d);color:#1d3557}
        .container{max-width:1100px;margin:auto}
        .card{background:rgba(255,255,255,0.7);padding:20px;border-radius:15px;margin-bottom:20px;box-shadow:0 8px 20px rgba(0,0,0,0.2);}
        h2{margin:0 0 10px 0}
        .top-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
        .search {margin-left:auto}
        input[type="search"]{padding:8px;border-radius:8px;border:1px solid #ccc;width:260px;color:#333}
        table{width:100%;border-collapse:collapse;margin-top:15px}
        th, td{padding:12px;text-align:left}
        th{border-bottom:1px solid rgba(0,0,0,0.15)}
        tr:hover{background:rgba(0,0,0,0.03)}
        .btn{color:#fff;background:#457b9d;padding:8px 12px;border-radius:8px;text-decoration:none;display:inline-block}
        .btn.danger{background:#e63946}
        .pill{background:rgba(0,0,0,0.08);color:#1d3557;padding:6px 8px;border-radius:999px}
        /* Flash messages remain distinct for visibility */
        .flash{padding:10px;margin-bottom:15px;border-radius:8px;color:#111;font-weight:600}
        .flash.success{background:#4CAF50}
        .flash.error{background:#f44336}
      </style>
    </head>
    <body>
      <div class='container'>
        {% for category, message in get_flashed_messages_py(with_categories=true) %}
          <div class='flash {{ category }}'>{{ message }}</div>
        {% endfor %}
        <div class='card'>
          <div style='display:flex;align-items:center'>
            <h2>Children Vaccination Management</h2>
            <div class='pill' style='margin-left:12px;font-size:0.9em'>Total: {{ rows|length }}</div>
          </div>
          <div class='top-actions'>
            <div>
              <a href='/add' class='btn'>+ Add Child</a>
              <a href='/admin' class='btn'>Admin Dashboard</a>
              <a href='/reminders' class='btn'>Reminders</a>
              <a href='/reports' class='btn' style='background:#1d3557'>Reports</a>
            </div>
            <form method='GET' class='search' action='/'>
              <input type='search' name='q' value='{{ request.args.get("q","") }}' placeholder='Search name, parent, phone'>
              <button class='btn' type='submit'>Search</button>
              <a href='/' class='btn' style='background:#6c757d'>Clear</a>
            </form>
          </div>

          <table>
            <tr><th>Name</th><th>DOB</th><th>Parent</th><th>Phone</th><th>Next Vaccine</th><th>Actions</th></tr>
            {% for r in rows %}
            {% set next_v_data = get_next_vaccine_for_template(r['id']) %}
            <tr>
              <td>{{ r['name'] }}</td>
              <td>{{ r['dob'] or '-' }}</td>
              <td>{{ r['parent'] or '-' }}</td>
              <td>{{ r['phone'] or '-' }}</td>
              <td>
                {% if next_v_data %}
                  {{ next_v_data['vaccine'] }} ({{ next_v_data['due_date_fmt'] }})
                {% else %}
                  -
                {% endif %}
              </td>
              <td>
                <a href='/child/{{ r["id"] }}' class='btn' style='background:#1d3557'>View</a>
                <a href='/edit/{{ r["id"] }}' class='btn'>Edit</a>
                <a href='/delete/{{ r["id"] }}' class='btn danger' onclick="return confirm('Delete record?');">Delete</a>
              </td>
            </tr>
            {% endfor %}
          </table>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(home_html, 
                                  rows=rows, 
                                  request=request, 
                                  get_next_vaccine_for_template=get_next_vaccine_for_template, 
                                  get_flashed_messages_py=get_flashed_messages_py)

@app.route('/add', methods=['GET', 'POST'])
def add_child():
    def get_flashed_messages_py(with_categories=False, category_filter=[]):
        return get_flashed_messages(with_categories=with_categories, category_filter=category_filter)

    if request.method == 'POST':
        name = request.form['name'].strip()
        dob = request.form['dob'].strip()
        parent = request.form['parent'].strip()
        phone = request.form['phone'].strip()
        notes = request.form['notes'].strip()

        conn = get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO children (name,dob,parent,phone,notes)
            VALUES (?,?,?,?,?)
        ''', (name or None, dob or None, parent or None, phone or None, notes or None))
        child_id = c.lastrowid
        conn.commit()
        create_schedule_for_child(conn, child_id, dob)
        conn.close()
        flash('Child added successfully', 'success')
        return redirect(url_for('home'))

    form_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width,initial-scale=1'>
      <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
      <style>
        body{font-family:'Poppins',sans-serif;padding:20px;background:linear-gradient(135deg,#a8dadc,#457b9d);color:#1d3557}
        .card{background:#fff;padding:20px;border-radius:10px;max-width:500px;margin:auto;box-shadow:0 8px 20px rgba(0,0,0,0.12);}
        input,textarea{width:100%;padding:8px;margin:6px 0;border-radius:8px;border:1px solid #ddd;color:#1d3557}
        button{padding:10px 15px;border:none;border-radius:10px;background:#457b9d;color:#fff;margin-top:10px;cursor:pointer}
        a.button{color:#fff;background:#6c757d;padding:8px;border-radius:8px;text-decoration:none;margin-right:8px;display:inline-block}
        .flash{padding:10px;margin-bottom:15px;border-radius:8px;font-weight:600;color:#111}
        .flash.success{background:#4CAF50}
        .flash.error{background:#f44336}
      </style>
    </head>
    <body>
      <div class='card'>
        {% for category, message in get_flashed_messages_py(with_categories=true) %}
          <div class='flash {{ category }}'>{{ message }}</div>
        {% endfor %}
        <h2>Add New Child</h2>
        <form method='POST'>
          <input type='text' name='name' placeholder='Child Name' required>
          <label>DOB (leave empty if unknown):</label>
          <input type='date' name='dob' placeholder='DOB'>
          <input type='text' name='parent' placeholder='Parent Name'>
          <input type='text' name='phone' placeholder='Phone'>
          <textarea name='notes' placeholder='Notes'></textarea>
          <button type='submit'>Add Child</button>
          <a href='/' class='button'>Back</a>
        </form>
      </div>
    </body>
    </html>
    """
    return render_template_string(form_html, get_flashed_messages_py=get_flashed_messages_py)

@app.route('/edit/<int:child_id>', methods=['GET', 'POST'])
def edit_child(child_id):
    def get_flashed_messages_py(with_categories=False, category_filter=[]):
        return get_flashed_messages(with_categories=with_categories, category_filter=category_filter)

    conn = get_conn()
    c = conn.cursor()
    r = c.execute('SELECT * FROM children WHERE id=?', (child_id,)).fetchone()
    
    if not r:
        conn.close()
        flash('Child not found', 'error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        dob = request.form['dob'].strip()
        parent = request.form['parent'].strip()
        phone = request.form['phone'].strip()
        notes = request.form['notes'].strip()

        c.execute('''
            UPDATE children SET name=?, dob=?, parent=?, phone=?, notes=? WHERE id=?
        ''', (name or None, dob or None, parent or None, phone or None, notes or None, child_id))
        conn.commit()

        create_schedule_for_child(conn, child_id, dob)
        conn.close()
        flash('Record updated', 'success')
        return redirect(url_for('view_child', child_id=child_id))

    edit_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width,initial-scale=1'>
      <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
      <style>
        body{font-family:'Poppins',sans-serif;padding:20px;background:linear-gradient(135deg,#a8dadc,#457b9d);color:#1d3557}
        .card{background:rgba(255,255,255,0.7);padding:20px;border-radius:15px;max-width:500px;margin:auto;box-shadow:0 8px 20px rgba(0,0,0,0.2);}
        input,textarea{width:100%;padding:8px;margin:6px 0;border-radius:8px;border:1px solid #ccc;background:#f1faee;color:#1d3557}
        label{font-size:0.9em;}
        button{padding:10px 15px;border:none;border-radius:10px;background:#457b9d;color:#fff;margin-top:10px;cursor:pointer}
        a.button{color:#fff;background:#6c757d;padding:8px;border-radius:8px;text-decoration:none;margin-right:8px;display:inline-block}
        .flash{padding:10px;margin-bottom:15px;border-radius:8px;font-weight:600;color:#111}
        .flash.success{background:#4CAF50}
        .flash.error{background:#f44336}
      </style>
    </head>
    <body>
      <div class='card'>
        {% for category, message in get_flashed_messages_py(with_categories=true) %}
          <div class='flash {{ category }}'>{{ message }}</div>
        {% endfor %}
        <h2>Edit Child</h2>
        <form method='POST'>
          <input type='text' name='name' placeholder='Child Name' value='{{ r["name"] }}' required>
          <label>DOB (YYYY-MM-DD):</label>
          <input type='date' name='dob' placeholder='DOB' value='{{ r["dob"] }}'>
          <input type='text' name='parent' placeholder='Parent Name' value='{{ r["parent"] }}'>
          <input type='text' name='phone' placeholder='Phone' value='{{ r["phone"] }}'>
          <textarea name='notes' placeholder='Notes'>{{ r["notes"] or '' }}</textarea>
          <button type='submit'>Save</button>
          <a href='/child/{{ r["id"] }}' class='button'>Back</a>
        </form>
      </div>
    </body>
    </html>
    """
    conn.close()
    return render_template_string(edit_html, r=r, get_flashed_messages_py=get_flashed_messages_py)

@app.route('/child/<int:child_id>')
def view_child(child_id):
    def get_flashed_messages_py(with_categories=False, category_filter=[]):
        return get_flashed_messages(with_categories=with_categories, category_filter=category_filter)

    conn = get_conn()
    r = conn.execute('SELECT * FROM children WHERE id=?', (child_id,)).fetchone()
    if not r:
        conn.close()
        flash('Child not found', 'error')
        return redirect(url_for('home'))

    vs = conn.execute('SELECT * FROM vaccinations WHERE child_id=? ORDER BY date(due_date) ASC', (child_id,)).fetchall()
    
    if not vs and r['dob']:
        create_schedule_for_child(conn, child_id, r['dob'])
        vs = conn.execute('SELECT * FROM vaccinations WHERE child_id=? ORDER BY date(due_date) ASC', (child_id,)).fetchall()

    schedule = []
    for v in vs:
        try:
            due_fmt = datetime.strptime(v['due_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
        except Exception:
            due_fmt = v['due_date'] or '-'
        schedule.append({"id": v['id'], "vaccine": v['vaccine'], "due_date": v['due_date'], "due_date_fmt": due_fmt, "status": v['status']})

    conn.close()

    view_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width,initial-scale=1'>
      <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
      <style>
        body{font-family:'Poppins',sans-serif;padding:20px;background:linear-gradient(135deg,#a8dadc,#457b9d);color:#1d3557}
        .card{background:rgba(255,255,255,0.7);padding:20px;border-radius:15px;max-width:900px;margin:auto;box-shadow:0 8px 20px rgba(0,0,0,0.2);}
        .flex{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
        .btn{color:#fff;background:#457b9d;padding:8px 12px;border-radius:8px;text-decoration:none;display:inline-block}
        .btn-dark{background:#1d3557}
        .done{background:#6c757d;color:#fff;padding:6px 8px;border-radius:8px;display:inline-block}
        table{width:100%;border-collapse:collapse;margin-top:15px;}
        th, td{padding:10px;text-align:left;border-bottom:1px solid rgba(0,0,0,0.12);}
        th{background:rgba(0,0,0,0.08);}
        .flash{padding:10px;margin-bottom:15px;border-radius:8px;font-weight:600;color:#111}
        .flash.success{background:#4CAF50}
        .flash.error{background:#f44336}
      </style>
    </head>
    <body>
      <div class='card'>
        {% for category, message in get_flashed_messages_py(with_categories=true) %}
          <div class='flash {{ category }}'>{{ message }}</div>
        {% endfor %}
        <div class='flex'>
          <h2>{{ r['name'] }}</h2>
          <div class='pill' style='background:rgba(0,0,0,0.06);padding:6px;border-radius:8px'>ID: {{ r['id'] }}</div>
        </div>
        <p><strong>DOB:</strong> {{ r['dob'] or '-' }}</p>
        <p><strong>Parent:</strong> {{ r['parent'] or '-' }}</p>
        <p><strong>Phone:</strong> {{ r['phone'] or '-' }}</p>
        <p><strong>Notes:</strong> {{ r['notes'] or '-' }}</p>

        {% if schedule %}
        <h3>Vaccination Schedule</h3>
        <table>
          <tr><th>Vaccine</th><th>Due Date</th><th>Status</th><th>Action</th></tr>
          {% for v in schedule %}
          <tr>
            <td>{{ v.vaccine }}</td>
            <td>{{ v.due_date_fmt }}</td>
            <td>{% if v.status == 'Done' %}<span class='done'>Done</span>{% else %}{{ v.status }}{% endif %}</td>
            <td>
              {% if v.status == 'Upcoming' %}
                <a href='/vaccine_toggle/{{ v.id }}' class='btn' onclick="return confirm('Mark as DONE?');">Mark Done</a>
              {% else %}
                <a href='/vaccine_toggle/{{ v.id }}' class='btn btn-dark' style='background:#1d3557' onclick="return confirm('Mark as UPCOMING?');">Mark Upcoming</a>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </table>
        {% else %}
          <p>No schedule available.</p>
        {% endif %}

        <div style='margin-top:12px'>
          <a href='{{ url_for("export_csv", child_id=r["id"]) }}' class='btn'>Export CSV</a>
          <a href='{{ url_for("print_schedule", child_id=r["id"]) }}' class='btn'>Printable (Save as PDF)</a>
          <a href='/edit/{{ r["id"] }}' class='btn'>Edit</a>
          <a href='/' class='btn btn-dark' style='background:#6c757d'>Back</a>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(view_html, r=r, schedule=schedule, get_flashed_messages_py=get_flashed_messages_py)

@app.route('/vaccine_toggle/<int:vaccine_id>')
def vaccine_toggle(vaccine_id):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute('SELECT * FROM vaccinations WHERE id=?', (vaccine_id,)).fetchone()
    if not row:
        conn.close()
        flash('Vaccine record not found', 'error')
        return redirect(url_for('home'))
        
    new_status = 'Done' if row['status'] != 'Done' else 'Upcoming'
    cur.execute('UPDATE vaccinations SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (new_status, vaccine_id))
    conn.commit()
    conn.close()
    flash(f"Vaccine '{row['vaccine']}' marked **{new_status}**", 'success')
    return redirect(url_for('view_child', child_id=row['child_id']))


@app.route('/send_sms/<int:child_id>/<int:vaccine_id>')
def send_sms_reminder_route(child_id, vaccine_id):
    conn = get_conn()

    child = conn.execute('SELECT name, phone FROM children WHERE id=?', (child_id,)).fetchone()
    vaccine_row = conn.execute('SELECT vaccine, due_date FROM vaccinations WHERE id=?', (vaccine_id,)).fetchone()
    conn.close()

    if not child or not vaccine_row:
        flash('Error: Child or vaccine record not found.', 'error')
        return redirect(url_for('reminders'))

    child_name = child['name']
    phone = child['phone']
    vaccine_name = vaccine_row['vaccine']
    
    try:
        due_date_fmt = datetime.strptime(vaccine_row['due_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
    except Exception:
        due_date_fmt = vaccine_row['due_date']
    
    success, message = send_mock_sms_reminder(child_name, phone, vaccine_name, due_date_fmt)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
        
    return redirect(url_for('reminders'))

@app.route('/delete/<int:child_id>')
def delete_child(child_id):
    conn = get_conn()
    conn.execute('DELETE FROM children WHERE id=?', (child_id,))
    conn.commit()
    conn.close()
    flash('Record deleted', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    def get_flashed_messages_py(with_categories=False, category_filter=[]):
        return get_flashed_messages(with_categories=with_categories, category_filter=category_filter)

    q = request.args.get('q', '').strip()
    conn = get_conn()
    if q:
        rows = conn.execute("SELECT * FROM children WHERE name LIKE ? OR parent LIKE ? ORDER BY created_at DESC",
                             (f'%{q}%', f'%{q}%')).fetchall()
    else:
        rows = conn.execute('SELECT * FROM children ORDER BY created_at DESC').fetchall()
    conn.close()

    admin_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width,initial-scale=1'>
      <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
      <style>
        body{font-family:'Poppins',sans-serif;padding:20px;background:linear-gradient(135deg,#a8dadc,#457b9d);color:#1d3557}
        .card{background:rgba(255,255,255,0.7);padding:20px;border-radius:15px;max-width:1000px;margin:auto;box-shadow:0 8px 20px rgba(0,0,0,0.2);}
        table{width:100%;border-collapse:collapse;margin-top:15px}
        th, td{padding:10px;text-align:left;border-bottom:1px solid rgba(0,0,0,0.12);}
        tr:hover{background:rgba(0,0,0,0.03);}
        .btn{color:#fff;background:#457b9d;padding:8px;border-radius:8px;text-decoration:none;margin-right:8px;}
        .danger{background:#e63946}
        input[type="search"]{padding:8px;border-radius:8px;border:1px solid #ccc;color:#333}
        .flash{padding:10px;margin-bottom:15px;border-radius:8px;font-weight:600;color:#111}
        .flash.success{background:#4CAF50}
        .flash.error{background:#f44336}
      </style>
    </head>
    <body>
      <div class='card'>
        {% for category, message in get_flashed_messages_py(with_categories=true) %}
          <div class='flash {{ category }}'>{{ message }}</div>
        {% endfor %}
        <h2>Admin Dashboard</h2>
        <form method='GET'>
          <input type='search' name='q' placeholder='Search' value='{{ request.args.get("q","") }}' style='padding:8px;border-radius:8px;border:none;margin-bottom:10px;width:260px'>
          <button class='btn' type='submit'>Search</button>
          <a href='/admin' class='btn' style='background:#6c757d'>Clear</a>
        </form>
        <table>
          <tr><th>Name</th><th>DOB</th><th>Parent</th><th>Phone</th><th>Next Vaccine</th><th>Actions</th></tr>
          {% for r in rows %}
          <tr>
            <td>{{ r['name'] }}</td>
            <td>{{ r['dob'] or '-' }}</td>
            <td>{{ r['parent'] or '-' }}</td>
            <td>{{ r['phone'] or '-' }}</td>
            <td>
              {% set next_v = find_next(r['id']) %}
              {% if next_v %}{{ next_v['vaccine'] }} ({{ next_v['due_date_fmt'] }}){% else %}-{% endif %}
            </td>
            <td>
              <a href='/child/{{ r["id"] }}' class='btn' style='background:#1d3557'>View</a>
              <a href='/delete/{{ r["id"] }}' class='btn danger' onclick="return confirm('Delete record?');">Delete</a>
            </td>
          </tr>
          {% endfor %}
        </table>
        <div style='margin-top:15px;'>
            <a href='/' class='btn' style='background:#6c757d; margin-right:8px;'>Back Home</a>
            <a href='/reports' class='btn' style='background:#1d3557'>View Reports</a>
        </div>
      </div>
    </body>
    </html>
    """
    def find_next_py(child_id):
        c = get_conn().cursor()
        row = c.execute('''
            SELECT vaccine, due_date FROM vaccinations
            WHERE child_id=? AND status='Upcoming' ORDER BY date(due_date) ASC LIMIT 1
        ''', (child_id,)).fetchone()
        c.connection.close()
        if not row:
            return None
        try:
            fmt = datetime.strptime(row['due_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
        except Exception:
            fmt = row['due_date']
        return {'vaccine': row['vaccine'], 'due_date_fmt': fmt}
        
    return render_template_string(admin_html, rows=rows, request=request, find_next=find_next_py, get_flashed_messages_py=get_flashed_messages_py)

@app.route('/reports')
def reports():
    def get_flashed_messages_py(with_categories=False, category_filter=[]):
        return get_flashed_messages(with_categories=with_categories, category_filter=category_filter)
    
    stats = get_vaccination_stats()
    
    reports_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width,initial-scale=1'>
      <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
      <style>
        body{font-family:'Poppins',sans-serif;padding:20px;background:linear-gradient(135deg,#a8dadc,#457b9d);color:#1d3557}
        .card{background:rgba(255,255,255,0.7);padding:20px;border-radius:15px;max-width:800px;margin:auto;box-shadow:0 8px 20px rgba(0,0,0,0.2);}
        .stats-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:15px;margin-top:20px}
        .stat-box{background:#f1faee;padding:15px;border-radius:10px;text-align:center;box-shadow:0 4px 8px rgba(0,0,0,0.1);}
        .stat-value{font-size:2.5em;font-weight:700;margin:0;color:#1d3557;}
        .stat-label{font-size:0.9em;color:#457b9d;margin-top:5px}
        .btn{color:#fff;background:#457b9d;padding:8px;border-radius:8px;text-decoration:none;margin-top:15px;display:inline-block}
        .flash{padding:10px;margin-bottom:15px;border-radius:8px;font-weight:600;color:#111}
        .flash.success{background:#4CAF50}
        .flash.error{background:#f44336}
      </style>
    </head>
    <body>
      <div class='card'>
        {% for category, message in get_flashed_messages_py(with_categories=true) %}
          <div class='flash {{ category }}'>{{ message }}</div>
        {% endfor %}
        <h2>System Vaccination Reports</h2>

        <div class='stats-grid'>
          <div class='stat-box'>
            <p class='stat-value'>{{ stats.completion_rate }}</p>
            <p class='stat-label'>Overall Completion Rate</p>
          </div>
          <div class='stat-box'>
            <p class='stat-value'>{{ stats.total_vaccines }}</p>
            <p class='stat-label'>Total Scheduled Vaccines</p>
          </div>
          <div class='stat-box' style='background:#e63946; color:white;'>
            <p class='stat-value' style='color:white;'>{{ stats.overdue_count }}</p>
            <p class='stat-label' style='color:white;'>Late/Overdue</p>
          </div>
          <div class='stat-box'>
            <p class='stat-value'>{{ stats.upcoming_count }}</p>
            <p class='stat-label'>Total Upcoming</p>
          </div>
        </div>

        <p style='margin-top:20px; font-size:0.9em; color:#6c757d;'>*Overdue counts vaccines that are 'Upcoming' but whose due date is today or earlier.</p>

        <a href='/admin' class='btn' style='background:#6c757d'>Back to Admin</a>
      </div>
    </body>
    </html>
    """
    return render_template_string(reports_html, stats=stats, get_flashed_messages_py=get_flashed_messages_py)

@app.route('/reminders')
def reminders():
    def get_flashed_messages_py(with_categories=False, category_filter=[]):
        return get_flashed_messages(with_categories=with_categories, category_filter=category_filter)

    """
    Shows upcoming vaccines within next N days (reminder list).
    """
    try:
        days = int(request.args.get('days', 14))
    except ValueError:
        days = 14
        
    today = datetime.today().date()
    limit_date = today + timedelta(days=days)
    conn = get_conn()
    rows = conn.execute('''
        SELECT c.id as child_id, c.name, c.parent, c.phone, v.id as vaccine_id, v.vaccine, v.due_date
        FROM vaccinations v JOIN children c ON v.child_id=c.id
        WHERE v.status='Upcoming' AND date(v.due_date) BETWEEN date(?) AND date(?)
        ORDER BY date(v.due_date) ASC
    ''', (today.isoformat(), limit_date.isoformat())).fetchall()
    conn.close()

    items = []
    for r in rows:
        try:
            due_fmt = datetime.strptime(r['due_date'], '%Y-%m-%d').strftime('%d-%m-%Y')
        except Exception:
            due_fmt = r['due_date']
        items.append({'child_id': r['child_id'], 'name': r['name'], 'parent': r['parent'],
                      'phone': r['phone'], 'vaccine_id': r['vaccine_id'], 'vaccine': r['vaccine'], 'due_date': r['due_date'], 'due_fmt': due_fmt})
    reminders_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <meta name='viewport' content='width=device-width,initial-scale=1'>
      <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
      <style>
        body{font-family:'Poppins',sans-serif;padding:20px;background:linear-gradient(135deg,#a8dadc,#457b9d);color:#1d3557}
        .card{background:rgba(255,255,255,0.7);padding:20px;border-radius:15px;max-width:1000px;margin:auto;box-shadow:0 8px 20px rgba(0,0,0,0.2);}
        table{width:100%;border-collapse:collapse;margin-top:15px}
        th, td{padding:10px;text-align:left;border-bottom:1px solid rgba(0,0,0,0.12);}
        .btn{color:#fff;background:#457b9d;padding:8px;border-radius:8px;text-decoration:none;margin-right:8px; display:inline-block;}
        .btn-sms{background:#38c353;} /* A nice green for SMS */
        input[type="number"]{color:#333;padding:6px;border-radius:6px;border:1px solid #ccc}
        .flash{padding:10px;margin-bottom:15px;border-radius:8px;font-weight:600;color:#111}
        .flash.success{background:#4CAF50}
        .flash.error{background:#f44336}
      </style>
    </head>
    <body>
      <div class='card'>
        {% for category, message in get_flashed_messages_py(with_categories=true) %}
          <div class='flash {{ category }}'>{{ message }}</div>
        {% endfor %}
        <h2>Reminders (Next {{ days }} days)</h2>
        <form method='GET'>
          <label>Window days:</label>
          <input type='number' name='days' value='{{ days }}' min='1'>
          <button class='btn' type='submit'>Update</button>
        </form>
        {% if items %}
        <table>
          <tr><th>Child</th><th>Parent</th><th>Phone</th><th>Vaccine</th><th>Due Date</th><th>Action</th><th>SMS</th></tr>
          {% for it in items %}
          <tr>
            <td>{{ it.name }}</td>
            <td>{{ it.parent or '-' }}</td>
            <td>{{ it.phone or '-' }}</td>
            <td>{{ it.vaccine }}</td>
            <td>{{ it.due_fmt }}</td>
            <td><a href='/child/{{ it.child_id }}' class='btn' style='background:#1d3557'>Open</a></td>
            <td>
              {% if it.phone %}
                <a href='{{ url_for("send_sms_reminder_route", child_id=it.child_id, vaccine_id=it.vaccine_id) }}' 
                   class='btn btn-sms' 
                   onclick="return confirm('Send MOCK SMS reminder for {{ it.vaccine }} to {{ it.phone }}?');">
                   Send SMS
                </a>
              {% else %}
                <span style='color:#e63946; font-size:0.8em;'>No Phone</span>
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </table>
        {% else %}
          <p>No upcoming vaccines in this window.</p>
        {% endif %}
        <div style='margin-top:15px;'>
            <a href='/' class='btn' style='background:#6c757d'>Back Home</a>
        </div>
      </div>
    </body>
    </html>
    """
    return render_template_string(reminders_html, items=items, days=days, get_flashed_messages_py=get_flashed_messages_py)

@app.route('/export/<int:child_id>/csv')
def export_csv(child_id):
    """
    Exports vaccination schedule for the child as CSV.
    """
    conn = get_conn()
    child = conn.execute('SELECT * FROM children WHERE id=?', (child_id,)).fetchone()
    if not child:
        conn.close()
        flash('Child not found', 'error')
        return redirect(url_for('home'))
    rows = conn.execute('SELECT * FROM vaccinations WHERE child_id=? ORDER BY date(due_date) ASC', (child_id,)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Child Name', child['name']])
    writer.writerow(['DOB', child['dob'] or ''])
    writer.writerow([])
    writer.writerow(['Vaccine', 'Due Date (YYYY-MM-DD)', 'Status'])
    for r in rows:
        writer.writerow([r['vaccine'], r['due_date'], r['status']])
    output.seek(0)
    
    mem = io.BytesIO(output.getvalue().encode('utf-8'))
    
    fname = f"schedule_{child['name'].replace(' ','_')}.csv"
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=fname)

@app.route('/print/<int:child_id>')
def print_schedule(child_id):
    """
    Simple printable HTML of the child's schedule.
    """
    conn = get_conn()
    r = conn.execute('SELECT * FROM children WHERE id=?', (child_id,)).fetchone()
    if not r:
        conn.close()
        flash('Child not found', 'error')
        return redirect(url_for('home'))
    vs = conn.execute('SELECT * FROM vaccinations WHERE child_id=? ORDER BY date(due_date) ASC', (child_id,)).fetchall()
    conn.close()

    printable_html = """
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8'>
      <title>Schedule for {{ r['name'] }}</title>
      <style>
        body{font-family:Arial, Helvetica, sans-serif;padding:20px;color:#111}
        h1{margin-bottom:4px}
        table{width:100%;border-collapse:collapse;margin-top:12px}
        th,td{padding:8px;border:1px solid #666;text-align:left}
        .actions{margin-top:12px}
        button, a{padding:8px 12px; border-radius:4px; text-decoration:none; margin-right:5px; border:1px solid #aaa;}
        button{background:#457b9d; color:white; border:none;}
        a{background:#f1f1f1; color:#333;}
        @media print {
          .no-print { display: none; }
        }
      </style>
    </head>
    <body>
      <h1>Vaccination Schedule</h1>
      <p><strong>Child:</strong> {{ r['name'] }} | <strong>DOB:</strong> {{ r['dob'] or '-' }}</p>
      <table>
        <tr><th>Vaccine</th><th>Due Date</th><th>Status</th></tr>
        {% for v in vs %}
          <tr>
            <td>{{ v['vaccine'] }}</td>
            <td>{{ v['due_date'] }}</td>
            <td>{{ v['status'] }}</td>
          </tr>
        {% endfor %}
      </table>

      <div class='actions no-print'>
        <button onclick='window.print()'>Print / Save as PDF</button>
        <a href='/child/{{ r["id"] }}' style='margin-left:8px'>Back to Child View</a>
      </div>
    </body>
    </html>
    """
    return render_template_string(printable_html, r=r, vs=vs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
