import hashlib

from flask import Flask, render_template, redirect, url_for, request, make_response, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from mysql_db import MySQL

login_manager = LoginManager()

app = Flask(__name__)

app.config.from_pyfile('config.py')

mysql = MySQL(app)

login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Доступ к данной странице есть только у авторизованных пользователей '
login_manager.login_message_category = 'warning'


class User(UserMixin):
    def __init__(self,user_id,login):
        self.id = user_id
        self.login = login
        

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection().cursor(named_tuple=True)
    cursor.execute('SELECT * FROM users WHERE id=%s',(user_id,))
    user = cursor.fetchone()
    if user:
        return User(user_id=user.id,login=user.login)
    return None

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/users/')
@login_required
def users():
    cursor = mysql.connection().cursor()
    cursor.execute('SELECT id, login, first_name, last_name FROM users')
    users = cursor.fetchall()
    return render_template('users/index.html', users=users)


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        login = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember')
        if login and password:
            cursor = mysql.connection().cursor(named_tuple=True)
            cursor.execute('SELECT * FROM users WHERE login=%s AND password_hash = SHA2(%s, 256)',(login,password))
            user = cursor.fetchone()
            if user:
                login_user(User(user_id=user.id,login=user.login),remember=remember)
                flash('Вы успешно прошли аутентификацию', 'success')
                next = request.args.get('next')
                return redirect(next or url_for('index'))
        flash('Неверные логин или пароль', 'danger')
    return render_template('login.html')


@app.route('/users/register', methods=['GET', 'POST'])
@login_required
def register():
    errors = {}
    if request.method == "GET":
        return render_template('users/register.html', errors=errors)

    login = request.form.get('loginInput')
    password = request.form.get('passwordInput')
    first_name = request.form.get('firstNameInput')
    last_name = request.form.get('lastNameInput')
    middle_name = request.form.get('middleNameInput')

    errors = {}

    if not login:
        errors['login'] = 'Поле не может быть пустым'
    else:
        if len(login) < 5:
            errors['login'] = 'Логин должен иметь длину не менее 5 символов'
        else:
            valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
            if not all(char in valid_chars for char in login):
                errors['login'] = 'Логин должен состоять только из латинских букв и цифр'


    if not password:
        errors['password'] = 'Поле не может быть пустым'
    else:
        password_status, password_error = check_password(password)
        if not password_status:
            errors['password'] = password_error

    if not first_name:
        errors['first_name'] = 'Поле не может быть пустым'

    if not last_name:
        errors['last_name'] = 'Поле не может быть пустым'

    if errors:
        return render_template('users/register.html', errors=errors, login=login, first_name=first_name, last_name=last_name, middle_name=middle_name)

    try:
        cursor = mysql.connection().cursor(named_tuple=True)
        query = """INSERT INTO users 
                   (login, password_hash, first_name, last_name, middle_name)
                   VALUES (%s, SHA2(%s, 256), %s, %s, %s)"""
        cursor.execute(query, (login, password, first_name, last_name, middle_name))
        mysql.connection().commit()
        cursor.close()
        flash('Успешная регистрация', 'success')
        return redirect(url_for('users'))
    except Exception as e:
        flash('Ошибка при регистрации пользователя', 'danger')
        return render_template('users/register.html', errors=errors, login=login, first_name=first_name, last_name=last_name, middle_name=middle_name)



@app.route('/users/<int:user_id>')
@login_required
def view_user(user_id):
    cursor = mysql.connection().cursor(named_tuple=True)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        return render_template('/users/view.html', user=user)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('index'))


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        middle_name = request.form.get('middle_name')
        try:
            with mysql.connection().cursor(named_tuple=True) as cursor:
                cursor.execute('UPDATE users SET first_name = %s, last_name = %s, middle_name = %s WHERE id = %s', (first_name, last_name, middle_name, user_id,))
                mysql.connection().commit()
                flash('Сведения о пользователи успешно сохранены', 'success')
                return redirect(url_for('view_user', user_id=user_id))
        except Exception as e:
             mysql.connection().rollback()
             flash('Ошибка', 'danger')
             cursor = mysql.connection().cursor(named_tuple=True)
             cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
             user = cursor.fetchone()
             return render_template('users/edit.html', user=user)
    else:
        cursor = mysql.connection().cursor(named_tuple=True)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if user:
            return render_template('users/edit.html', user=user)
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('index'))


@app.route('/users/<int:user_id>/delete', methods=['GET','POST'])
@login_required
def delete_user(user_id):
    cursor = mysql.connection().cursor(named_tuple=True)
    cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
    mysql.connection().commit()
    flash('Пользователь успешно удалён', 'success')
    return redirect(url_for('users'))
   

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/users/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user_id = current_user.get_id()
        current_password = request.form.get('currentPassword')
        new_password1 = request.form.get('newPassword1')
        new_password2 = request.form.get('newPassword2')

        cursor = mysql.connection().cursor(named_tuple=True)
        cursor.execute('SELECT password_hash FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if not user or not hashlib.sha256(current_password.encode()).hexdigest() == user.password_hash:
            flash('Неверный текущий пароль', 'danger')
            return render_template('users/change_password.html')

        # Проверка нового пароля
        if new_password1 != new_password2:
            flash('Новые пароли не совпадают', 'danger')
            return render_template('users/change_password.html')

        password_status, password_error = check_password(new_password1)
        if not password_status:
            flash(f'Ошибка: {password_error}', 'danger')
            return render_template('users/change_password.html')

        try:
            with mysql.connection().cursor(named_tuple=True) as cursor:
                cursor.execute('UPDATE users SET password_hash = SHA2(%s, 256) WHERE id = %s', (new_password1, user_id,))
                mysql.connection().commit()
                flash('Пароль успешно изменен', 'success')
                return redirect(url_for('view_user', user_id=user_id))
        except Exception as e:
            mysql.connection().rollback()
            flash('Ошибка при изменении пароля', 'danger')
            return render_template('users/change_password.html')
    else:
        return render_template('users/change_password.html')


def check_password(password):
    if len(password) < 8 or len(password) > 128:
        return False, 'Пароль должен быть не меньше 8 и не больше 128 символов'

    has_upper = False
    has_lower = False
    has_digit = False

    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя0123456789~!?@#$%^&*_-+()[]{}><\\/|\"'.,:;")

    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True

        if char not in valid_chars:
            return False, 'Разрешено использовать только латинские или кириллические буквы'

    if not has_upper:
        return False, 'Пароль должен содержать хотя бы одну заглавную букву'
    if not has_lower:
        return False, 'Пароль должен содержать хотя бы одну прописную букву'
    if not has_digit:
        return False, 'Пароль должен содержать хотя бы одну цифру'

    return True, ''


if __name__ == '__main__':
    app.run(debug=True)