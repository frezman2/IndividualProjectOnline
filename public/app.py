from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from avatar_generation import generate_avatar
import base64


app = Flask(__name__)
app.secret_key = 'supersecretkey'
ph = PasswordHasher()  # Инициализация Argon2   

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Создание таблицы пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL, picture BLOB NOT NULL)''')
    # Создание таблицы классов
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, school TEXT NOT NULL, user_id INTEGER NOT NULL, 
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = ph.hash(password)
        
        picture = generate_avatar(username, 40)

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            flash('Пользователь с таким именем уже существует.', 'danger')
            conn.close()
            return redirect(url_for('registration'))    
            

        # Добавление нового пользователя
        c.execute("INSERT INTO users (username, password, picture) VALUES (?, ?, ?)", (username, hashed_password, picture))
        conn.commit()
        conn.close()

        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('autorization'))

    return render_template('registration.html')
    
@app.route('/autorization', methods=['GET', 'POST'])
def autorization():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user:
            try:
                if ph.verify(user[2], password):
                    session['user_id'] = user[0]  # Сохранение ID пользователя в сессии
                    session['username'] = username  # Сохранение имени пользователя в сессии
                    session['picture'] = base64.b64encode(user[3]).decode('utf-8')
                    flash('Вход выполнен успешно!', 'success')
                    return redirect(url_for('main'))
            except VerifyMismatchError:
                flash('Неверное имя пользователя или пароль.', 'danger')
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('autorization.html')

@app.route('/main')
def main():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('autorization'))  # Перенаправление на страницу авторизации, если пользователь не авторизован

    username = session.get('username')  # Получение имени пользователя из сессии
    picture = session.get('picture')

    # Получение классов пользователя
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT name, school FROM classes WHERE user_id = ?", (user_id,))
    classes = c.fetchall()
    conn.close()

    return render_template('main.html', username=username, profile_icon=picture, classes=classes)

@app.route('/')
def index():
    return redirect(url_for('registration'))  # Перенаправление на страницу регистрации


@app.route('/add_class', methods=['POST'])
def add_class():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    class_name = data.get('name')
    school_year = data.get('school')

    if not class_name or not school_year:
        return jsonify({'error': 'Invalid data'}), 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO classes (name, school, user_id) VALUES (?, ?, ?)", (class_name, school_year, user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Class added successfully'})

@app.route('/logout')
def logout():
    session.clear()  # Очистка всех данных сессии
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('autorization'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    