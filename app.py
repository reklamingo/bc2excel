from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'bc2excel_secret'
DB_PATH = 'users.db'
UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            credit INTEGER DEFAULT 5,
            is_admin INTEGER DEFAULT 0
        )
        """)

def get_user(email):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

def get_user_by_id(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            return redirect('/login')
        except:
            return "Bu e-posta zaten kayıtlı."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user(email)
        if user and user[2] == password:
            session['user_id'] = user[0]
            return redirect('/')
        return "Giriş bilgileri hatalı"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    user = get_user_by_id(session['user_id'])
    if request.method == 'POST':
        if user[3] <= 0:
            return "Krediniz tükendi. Lütfen paket satın alın."
        files = request.files.getlist('files')
        if len(files) > 100:
            return "Bir işlemde maksimum 100 görsel yükleyebilirsiniz."
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE users SET credit = credit - 1 WHERE id = ?", (user[0],))
        return "Dosyalar başarıyla işlendi (simülasyon)."
    return render_template('dashboard.html', user_email=user[1], credit=user[3])

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session:
        return redirect('/login')
    user = get_user_by_id(session['user_id'])
    if not user or user[4] == 0:
        return "Erişim reddedildi"
    with sqlite3.connect(DB_PATH) as conn:
        users = conn.execute("SELECT * FROM users").fetchall()
    return render_template('admin.html', users=users)

@app.route('/admin/add_credit/<int:user_id>')
def add_credit(user_id):
    if 'user_id' not in session:
        return redirect('/login')
    admin = get_user_by_id(session['user_id'])
    if not admin or admin[4] == 0:
        return "Yetkiniz yok"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET credit = credit + 50 WHERE id = ?", (user_id,))
    return redirect('/admin')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
