from flask import Flask, render_template, request, redirect, url_for, flash, session
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
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL, picture BLOB NOT NULL)''')
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
                    session['username'] = username  # Сохранение имени пользователя в сессии
                    session['picture'] = base64.b64encode(user[3]).decode('utf-8')
                    flash('Вход выполнен успешно!', 'success')
                    return redirect(url_for('main'))
            except VerifyMismatchError:
                flash('Неверное имя пользователя или пароль.', 'danger')
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('autorization.html')

@app.route('/')
def main():
    username = session.get('username')  # Получение имени пользователя из сессии
    picture = session.get('picture')
    return render_template('main.html', username=username, profile_icon=picture)

@app.route('/logout')
def logout():
    session.clear()  # Очистка всех данных сессии
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('autorization'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
