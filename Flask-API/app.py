from collections import OrderedDict
from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)

@app.before_request
def method_override():
    if request.method == 'POST':
        override = request.form.get('_method')
        if override:
            request.environ['REQUEST_METHOD'] = override.upper()

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='perpus'
    )

def is_html_request():
    return 'text/html' in request.headers.get('Accept', '')

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()

    ordered_books = [
        OrderedDict([('id', book['id']), ('title', book['title']), ('author', book['author'])])
        for book in books
    ]

    if is_html_request():
        return render_template('index.html', books=books)
    else:
        return jsonify(ordered_books)
    
@app.route('/book/<int:book_id>', methods=['GET'])
def get_book_by_id(book_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    conn.close()

    if book:
        return jsonify(book)
    else:
        return jsonify({'error': 'Book not found'}), 404


@app.route('/add', methods=['POST'])
def add_book():
    if request.is_json:
        data = request.get_json()
        title = data['title']
        author = data['author']
    else:
        title = request.form['title']
        author = request.form['author']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
    conn.commit()
    conn.close()

    if is_html_request():
        return redirect(url_for('index'))
    else:
        return jsonify({'status': 'success'})

@app.route('/edit/<int:book_id>', methods=['GET', 'POST', 'PUT'])
def edit_book(book_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        conn.close()

        if is_html_request():
            return render_template('edit.html', book=book)
        else:
            return jsonify(book)

    if request.method == 'PUT' or request.form.get('_method', '').upper() == 'PUT':
        if request.is_json:
            data = request.get_json()
            title = data['title']
            author = data['author']
        else:
            title = request.form['title']
            author = request.form['author']

        cursor.execute("UPDATE books SET title=%s, author=%s WHERE id=%s", (title, author, book_id))
        conn.commit()
        conn.close()

        if is_html_request():
            return redirect(url_for('index'))
        else:
            return jsonify({'status': 'success'})

@app.route('/delete/<int:book_id>', methods=['POST', 'DELETE'])
def delete_book(book_id):
    method_override = request.form.get('_method', '').upper()

    if request.method == 'DELETE' or method_override == 'DELETE':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        conn.close()

        if is_html_request():
            return redirect(url_for('index'))
        else:
            return jsonify({'status': 'success'})

    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
