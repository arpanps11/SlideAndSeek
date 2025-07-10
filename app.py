from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'songs.db'

# Optional: Initialize DB (only runs if DB doesn't exist)
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                lyrics TEXT NOT NULL,
                key_root TEXT,
                key_type TEXT,
                song_number TEXT,
                page_number TEXT
            )
        ''')
        conn.commit()

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Add song route
@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics'].strip()
        key_root = request.form.get('key_root', '').strip() or None
        key_type = request.form.get('key_type', '').strip() or None
        song_number = request.form.get('song_number', '').strip() or None
        page_number = request.form.get('page_number', '').strip() or None

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO songs (title, lyrics, key_root, key_type, song_number, page_number)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, lyrics, key_root, key_type, song_number, page_number))
            conn.commit()

        return redirect('/')
    return render_template('add.html')

# Search logic
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

# Get all song titles for autocomplete
def get_all_titles():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM songs")
        return [{'title': row[0]} for row in cursor.fetchall()]

# Search route
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
    return render_template('search.html', query=query, results=results, searched=searched, all_songs=all_songs)

# Edit route
@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            title = request.form['title'].strip()
            lyrics = request.form['lyrics'].strip()
            key_root = request.form.get('key_root', '').strip() or None
            key_type = request.form.get('key_type', '').strip() or None
            song_number = request.form.get('song_number', '').strip() or None
            page_number = request.form.get('page_number', '').strip() or None

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

# Placeholder route
@app.route('/generate')
def generate():
    return "Coming soon"

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
