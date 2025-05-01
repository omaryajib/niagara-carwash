from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from forms import WashRecordForm, RegistrationForm, LoginForm
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key'  # bleibt privat
DATABASE = 'carwash.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()

def fetch_user(username):
    return query_db('SELECT * FROM users WHERE username = ?', [username], one=True)

@app.route('/')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('login'))
    try:
        total_washes = query_db('SELECT COUNT(*) as count FROM washes', one=True)['count']
        total_umsatz = query_db('SELECT SUM(normal_umsatz + subscription_card + subscription_lastschrift) as total FROM daily_sales', one=True)['total'] or 0
        total_profit = query_db('SELECT SUM(normal_umsatz + subscription_card + subscription_lastschrift - water_cost - energy_cost - product_cost) as total FROM daily_sales', one=True)['total'] or 0
        total_costs = query_db('SELECT SUM(water_cost + energy_cost + product_cost) as total FROM daily_sales', one=True)['total'] or 0
        avg_umsatz_per_wash = (total_umsatz / total_washes) if total_washes > 0 else 0

        washes_per_filiale = {}
        rows = query_db('SELECT filiale, COUNT(*) as count FROM washes GROUP BY filiale')
        for row in rows:
            washes_per_filiale[row['filiale']] = row['count']

        normal_umsatz = query_db('SELECT SUM(normal_umsatz) as total FROM daily_sales', one=True)['total'] or 0
        subscription_umsatz = query_db('SELECT SUM(subscription_card + subscription_lastschrift) as total FROM daily_sales', one=True)['total'] or 0

        daily_sales_data = {}
        sales_rows = query_db('SELECT filiale, SUM(normal_umsatz) as normal_umsatz, SUM(subscription_card) as subscription_card, SUM(subscription_lastschrift) as subscription_lastschrift FROM daily_sales GROUP BY filiale')
        for row in sales_rows:
            daily_sales_data[row['filiale']] = {
                'normal_umsatz': row['normal_umsatz'] or 0,
                'subscription_card': row['subscription_card'] or 0,
                'subscription_lastschrift': row['subscription_lastschrift'] or 0,
                'total_umsatz': (row['normal_umsatz'] or 0) + (row['subscription_card'] or 0) + (row['subscription_lastschrift'] or 0)
            }

        return render_template('dashboard.html',
                               total_washes=total_washes,
                               total_umsatz=total_umsatz,
                               total_profit=total_profit,
                               avg_umsatz_per_wash=avg_umsatz_per_wash,
                               washes_per_filiale=washes_per_filiale,
                               normal_umsatz=normal_umsatz,
                               subscription_umsatz=subscription_umsatz,
                               daily_sales=daily_sales_data,
                               username=session['user']['username'])
    except sqlite3.OperationalError as e:
        print(f"### DB Fehler im Dashboard: {e} ###")
        return render_template('error.html', error=str(e))

@app.route('/add_wash', methods=['GET', 'POST'])
def add_wash():
    if not session.get('user'):
        return redirect(url_for('login'))
    form = WashRecordForm()
    if form.validate_on_submit():
        filiale = form.filiale.data
        execute_db('INSERT INTO washes (filiale) VALUES (?)', [filiale])
        return redirect(url_for('dashboard'))
    return render_template('add_wash.html', form=form, username=session['user']['username'])

@app.route('/daily_entry', methods=['GET', 'POST'])
def daily_entry():
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        filiale = request.form['filiale']
        normal_umsatz = float(request.form['normal_umsatz'] or 0)
        subscription_card = float(request.form['subscription_card'] or 0)
        subscription_lastschrift = float(request.form['subscription_lastschrift'] or 0)
        water_cost = float(request.form['water_cost'] or 0)
        energy_cost = float(request.form['energy_cost'] or 0)
        product_cost = float(request.form['product_cost'] or 0)

        execute_db('''
            INSERT INTO daily_sales (filiale, normal_umsatz, subscription_card, subscription_lastschrift, water_cost, energy_cost, product_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [filiale, normal_umsatz, subscription_card, subscription_lastschrift, water_cost, energy_cost, product_cost])
        return redirect(url_for('dashboard'))
    return render_template('daily_entry.html', username=session['user']['username'])

@app.route('/stock')
def stock():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('stock.html', username=session['user']['username'])

@app.route('/wash_records')
def wash_records():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('wash_records.html', username=session['user']['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        existing_user = fetch_user(username)
        if existing_user:
            flash('Benutzername existiert bereits. Bitte anderen wählen.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            execute_db('INSERT INTO users (username, password) VALUES (?, ?)', [username, hashed_password])
            flash('Registrierung erfolgreich. Sie können sich jetzt anmelden.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = fetch_user(username)
        if user and check_password_hash(user['password'], password):
            session['user'] = {'id': user['id'], 'username': user['username']}
            return redirect(url_for('dashboard'))
        else:
            flash('Benutzername oder Passwort ist falsch.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("### Starte die App ###")
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS washes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filiale TEXT NOT NULL,
                wash_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filiale TEXT NOT NULL,
                sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                normal_umsatz REAL DEFAULT 0,
                subscription_card REAL DEFAULT 0,
                subscription_lastschrift REAL DEFAULT 0,
                water_cost REAL DEFAULT 0,
                energy_cost REAL DEFAULT 0,
                product_cost REAL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("### Datenbank und Tabellen wurden erstellt ###")

    app.run(debug=True)
