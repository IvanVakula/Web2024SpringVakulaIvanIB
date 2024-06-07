from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from config import *

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Initialize the login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# User model
class User(UserMixin):
    def __init__(self, id, username, password_hash, last_name, first_name, middle_name, role_id):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        self.role_id = role_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role_id == 1

    @property
    def is_moderator(self):
        return self.role_id == 2

@login_manager.user_loader
def load_user(user_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    connection.close()
    if user_data:
        return User(**user_data)
    return None

# Book model
class Book:
    def __init__(self, id, title, description, year, publisher, author, pages, cover_id, cover_filename):
        self.id = id
        self.title = title
        self.description = description
        self.year = year
        self.publisher = publisher
        self.author = author
        self.pages = pages
        self.cover_id = cover_id
        self.cover_filename = cover_filename

# Decorator to check roles
def role_required(role):
    def wrapper(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Для выполнения данного действия необходимо пройти процедуру аутентификации")
                return redirect(url_for('login'))
            if role == 'admin' and not current_user.is_admin:
                flash("У вас недостаточно прав для выполнения данного действия")
                return redirect(url_for('index'))
            if role == 'moderator' and not (current_user.is_admin or current_user.is_moderator):
                flash("У вас недостаточно прав для выполнения данного действия")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__  # Добавляем имя функции
        return decorated_function
    return wrapper

@app.route('/')
@app.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
    SELECT b.id, b.title, b.description, b.year, b.publisher, b.author, b.pages, b.cover_id, c.filename AS cover_filename
    FROM books b
    JOIN covers c ON b.cover_id = c.id
    ORDER BY b.year DESC
    LIMIT %s OFFSET %s
    """
    cursor.execute(query, (10, (page-1)*10))
    books_data = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) as count FROM books")
    total_books = cursor.fetchone()['count']
    total_pages = (total_books + 9) // 10  # Calculate total pages
    cursor.close()
    connection.close()

    books = [Book(**book) for book in books_data]
    return render_template('index.html', books=books, page=page, total_pages=total_pages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(**user_data)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неправильный username или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Добавление книги
@app.route('/book/add', methods=['GET', 'POST'])
@role_required('admin')
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        year = request.form['year']
        publisher = request.form['publisher']
        author = request.form['author']
        pages = request.form['pages']
        cover_id = request.form['cover_id']

        connection = create_connection()
        cursor = connection.cursor()
        query = "INSERT INTO books (title, description, year, publisher, author, pages, cover_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (title, description, year, publisher, author, pages, cover_id))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Книга успешно добавлена')
        return redirect(url_for('index'))
    return render_template('add_book.html')

# Редактирование книги
@app.route('/book/edit/<int:book_id>', methods=['GET', 'POST'])
@role_required('moderator')
def edit_book_view(book_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        year = request.form['year']
        publisher = request.form['publisher']
        author = request.form['author']
        pages = request.form['pages']
        cover_id = request.form['cover_id']

        cursor = connection.cursor()
        query = "UPDATE books SET title = %s, description = %s, year = %s, publisher = %s, author = %s, pages = %s, cover_id = %s WHERE id = %s"
        cursor.execute(query, (title, description, year, publisher, author, pages, cover_id, book_id))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Книга успешно обновлена')
        return redirect(url_for('index'))
    return render_template('edit_book.html', book=book)

# Удаление книги
@app.route('/book/delete/<int:book_id>', methods=['POST'])
@role_required('admin')
def delete_book_view(book_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()
    flash('Книга успешно удалена')
    return redirect(url_for('index'))

# Просмотр книги
@app.route('/book/view/<int:book_id>', methods=['GET'])
def view_book(book_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT b.id, b.title, b.description, b.year, b.publisher, b.author, b.pages, b.cover_id, c.filename AS cover_filename FROM books b JOIN covers c ON b.cover_id = c.id WHERE b.id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    connection.close()
    if book:
        return render_template('view_book.html', book=book)
    else:
        flash("Book not found")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
