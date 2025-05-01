import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from forms import WashRecordForm, RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')

# PostgreSQL connection
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return (rows[0] if rows else None) if one else rows

def execute_db(query, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()
    conn.close()

def fetch_user(username):
    row = query_db('SELECT id, username, password FROM users WHERE username = %s', [username], one=True)
    if row:
        return {'id': row[0], 'username': row[1], 'password': row[2]}
    return None

@app.route('/')
def dashboard():
    if not session.get('user'):
        return redirect(url_for('login'))
    try:
        total_washes = query_db('SELECT COUNT(*) FROM washes', one=True)[0]
        total_umsatz = query_db('SELECT COALESCE(SUM(normal_umsatz + subscription_card + subscription_lastschrift), 0) FROM daily_sales', one=True)[0]
        total_profit = query_db('SELECT COALESCE(SUM(normal_umsatz + subscription_card + subscription_lastschrift - water_cost - energy_cost - product_cost), 0) FROM daily_sales', one=True)[0]
        avg_umsatz_per_wash = (total_umsatz / total_washes) if total_washes > 0 else 0

        washes_per_filiale = {}
        for filiale, count in query_db('SELECT filiale, COUNT(*) FROM washes GROUP BY filiale'):
            washes_per_filiale[filiale] = count

        normal_umsatz = query_db('SELECT COALESCE(SUM(normal_umsatz), 0) FROM daily_sales', one=True)[0]
        subscription_umsatz = query_db('SELECT COALESCE(SUM(subscription_card + subscription_lastschrift), 0) FROM daily_sales', one=True)[0]

        daily_sales_data = {}
        rows = query_db('''SELECT filiale, 
                                  COALESCE(SUM(normal_umsatz),0), 
                                  COALESCE(SUM(subscription_card),0), 
                                  COALESCE(SUM(subscription_lastschrift),0)
                           FROM daily_sales GROUP BY filiale''')
        for row in rows:
            filiale, norm, card, last = row
            daily_sales_data[filiale] = {
                'normal_umsatz': norm,
                'subscription_card': card,
                'subscription_lastschrift': last,
                'total_umsatz': norm + card + last
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
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        existing_user = fetch_user(username)
        if existing_user:
            flash('Benutzername existiert bereits.', 'danger')
        else:
            hashed = generate_password_hash(password)
            execute_db('INSERT INTO users (username, password) VALUES (%s, %s)', [username, hashed])
            flash('Registrierung erfolgreich.', 'success')
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
            flash('Falscher Benutzername oder Passwort.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
