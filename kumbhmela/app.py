from flask import Flask, render_template, request, redirect, url_for, session,send_file
import sqlite3
import csv

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session
DB_NAME = "kumbhmela.db"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# ------------------ Admin Login ------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

# ------------------ Admin Logout ------------------
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ------------------ Admin Dashboard ------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        totals = {
            'parking_agents': cursor.execute("SELECT COUNT(*) FROM parking_agents").fetchone()[0],
            'travellers': cursor.execute("SELECT COUNT(*) FROM travellers").fetchone()[0],
            'vehicles': cursor.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0],
            'customers': cursor.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        }
        recent_travellers = cursor.execute("SELECT * FROM travellers ORDER BY id DESC LIMIT 5").fetchall()

    return render_template('admin_dashboard.html', totals=totals, recent_travellers=recent_travellers)

# ------------------ Initialize Database ------------------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Parking agents
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            contact TEXT NOT NULL,
            shift TEXT NOT NULL
        )
        """)
        # Travellers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS travellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            city TEXT,
            transport TEXT,
            purpose TEXT
        )
        """)
        # Vehicles
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_name TEXT,
            type TEXT,
            rent_amount REAL
        )
        """)
        # Customers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            visiting_place TEXT,
            purpose TEXT,
            family_members INTEGER
        )
        """)
        conn.commit()

# ------------------ Helper Functions ------------------
def save_to_db(table, columns, values):
    placeholders = ','.join('?' * len(values))
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})", values)
        conn.commit()

def fetch_from_db(table):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        data = cursor.fetchall()
        # Fetch column names
        cursor.execute(f"PRAGMA table_info({table})")
        headers = [col[1] for col in cursor.fetchall()]
        return [headers] + list(data) if data else [headers]

def export_csv(table, filename):
    data = fetch_from_db(table)
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)
    return filename

# ------------------ Routes ------------------

# Home
@app.route('/')
def home():
    return render_template('home.html')

# Parking Agent
@app.route('/parking_agent', methods=['GET','POST'])
def parking_agent():
    success = False
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        contact = request.form['contact']
        shift = request.form['shift']
        save_to_db("parking_agents", ["name","location","contact","shift"], [name, location, contact, shift])
        success = True
    return render_template('parking_agent.html',
                           success=success,
                           show_view_btn=True,
                           view_url='/view_parking_agents')

@app.route('/view_parking_agents')
def view_parking_agents():
    data = fetch_from_db("parking_agents")
    return render_template(
        'view_parking_agents.html', 
        data=data, 
        download_url='/download_parking_agents',
        show_download_btn=True   
    )


@app.route('/download_parking_agents')
def download_parking_agents():
    filepath = "parking_agents.csv"
    export_csv("parking_agents", filepath)
    return send_file(filepath, as_attachment=True)

# Traveller
@app.route('/traveller', methods=['GET','POST'])
def traveller():
    success = False
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        city = request.form['city']
        transport = request.form['transport']
        purpose = request.form['purpose']
        save_to_db("travellers", ["name","age","city","transport","purpose"], [name, age, city, transport, purpose])
        success = True
    return render_template('traveller.html',
                           success=success,
                           show_view_btn=True,
                           view_url='/view_travellers')

@app.route('/view_travellers')
def view_travellers():
    data = fetch_from_db("travellers")
    return render_template(
        'view_travellers.html', 
        data=data, 
        download_url='/download_travellers',
        show_download_btn=True
    )
@app.route('/download_travellers')
def download_travellers():
    filepath = "travellers.csv"
    export_csv("travellers", filepath)
    return send_file(filepath, as_attachment=True)

# Vehicle
@app.route('/vehicle', methods=['GET','POST'])
def vehicle():
    success = False
    if request.method == 'POST':
        vehicle_name = request.form['vehicle_name']
        type_ = request.form['type']
        rent_amount = request.form['rent_amount']
        save_to_db("vehicles", ["vehicle_name","type","rent_amount"], [vehicle_name, type_, rent_amount])
        success = True
    return render_template('vehicle.html',
                           success=success,
                           show_view_btn=True,
                           view_url='/view_vehicles')



@app.route('/view_vehicles')
def view_vehicles():
    data = fetch_from_db("vehicles")
    return render_template(
        'view_vehicles.html', 
        data=data, 
        download_url='/download_vehicles',
        show_download_btn=True
    )


@app.route('/download_vehicles')
def download_vehicles():
    filepath = "vehicles.csv"
    export_csv("vehicles", filepath)
    return send_file(filepath, as_attachment=True)

# Customer
@app.route('/customer', methods=['GET','POST'])
def customer():
    success = False
    if request.method == 'POST':
        name = request.form['name']
        visiting_place = request.form['visiting_place']
        purpose = request.form['purpose']
        family_members = request.form['family_members']
        save_to_db("customers", ["name","visiting_place","purpose","family_members"], [name, visiting_place, purpose, family_members])
        success = True
    return render_template('customer.html',
                           success=success,
                           show_view_btn=True,
                           view_url='/view_customers')
@app.route('/view_customers')
def view_customers():
    data = fetch_from_db("customers")
    return render_template(
        'view_customers.html', 
        data=data, 
        download_url='/download_customers',
        show_download_btn=True
    )
@app.route('/download_customers')
def download_customers():
    filepath = "customers.csv"
    export_csv("customers", filepath)
    return send_file(filepath, as_attachment=True)


def get_totals():
    totals = {}
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        tables = ["parking_agents", "travellers", "vehicles", "customers"]
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            totals[table] = cursor.fetchone()[0]
    return totals
@app.route('/dashboard')
def dashboard():
    totals = get_totals()
    return render_template('dashboard.html', totals=totals)


# ------------------ Run App ------------------
if __name__ == "__main__":
    init_db()  # Ensure all tables exist before starting
    app.run(debug=True)
