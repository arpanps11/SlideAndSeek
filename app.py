from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'songs.db'
SONG_EDIT_PASSWORD = "ebccni@2025"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('authenticated'):
        return redirect(url_for('verify', next='/add'))

    message = None
    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics'].strip()
        key_root = request.form['key_root'].strip() or None
        key_type = request.form['key_type'].strip() or None
        song_number = request.form['song_number'].strip() or None
        page_number = request.form['page_number'].strip() or None

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO songs (title, lyrics, key_root, key_type, song_number, page_number) VALUES (?, ?, ?, ?, ?, ?)",
                           (title, lyrics, key_root, key_type, song_number, page_number))
            conn.commit()
        message = "Song added successfully!"

    return render_template('add.html', message=message)

def search_songs(query):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        query = f"%{query}%"
        cursor.execute("""
            SELECT title, lyrics, key_root, key_type, song_number, id
            FROM songs
            WHERE title LIKE ? OR lyrics LIKE ? OR key_root LIKE ? OR key_type LIKE ?
        """, (query, query, query, query))
        return cursor.fetchall()

def get_all_titles():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM songs")
        return [{'title': row[0]} for row in cursor.fetchall()]

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = ''
    results = []
    searched = False

    if request.method == 'POST':
        query = request.form['query'].strip()
        results = search_songs(query)
        searched = True

    all_songs = get_all_titles()
    authenticated = session.get('authenticated', False)
    return render_template('search.html', query=query, results=results, searched=searched, all_songs=all_songs, authenticated=authenticated)

@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    if not session.get('authenticated'):
        return redirect(url_for('verify', next=f'/edit/{song_id}'))

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            title = request.form['title'].strip()
            lyrics = request.form['lyrics'].strip()
            key_root = request.form['key_root'].strip() or None
            key_type = request.form['key_type'].strip() or None
            song_number = request.form['song_number'].strip() or None
            page_number = request.form['page_number'].strip() or None

            cursor.execute("""
                UPDATE songs
                SET title = ?, lyrics = ?, key_root = ?, key_type = ?, song_number = ?, page_number = ?
                WHERE id = ?
            """, (title, lyrics, key_root, key_type, song_number, page_number, song_id))
            conn.commit()
            return redirect('/search')

        cursor.execute("""
            SELECT title, lyrics, key_root, key_type, song_number, page_number
            FROM songs
            WHERE id = ?
        """, (song_id,))
        song = cursor.fetchone()

    return render_template('edit.html', song=song, song_id=song_id)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    next_page = request.args.get('next', '/')
    error = None

    if request.method == 'POST':
        password = request.form['password']
        if password == SONG_EDIT_PASSWORD:
            session['authenticated'] = True
            return redirect(next_page)
        else:
            error = "Incorrect password. Try again."

    return render_template('verify.html', next_page=next_page, error=error)

@app.route('/generate')
def generate():
    return "Coming soon"

if __name__ == '__main__':
    app.run(debug=True)
