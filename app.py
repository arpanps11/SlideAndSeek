from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DATABASE = 'songs.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                lyrics TEXT,
                key TEXT,
                song_number TEXT,
                page_number TEXT
            )
        ''')
        conn.commit()

def get_all_songs():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM songs")
        return [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]

def search_songs(query):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        query = f"%{query}%"
        cursor.execute('''
            SELECT title, lyrics, key FROM songs 
            WHERE title LIKE ? OR lyrics LIKE ? OR key LIKE ?
        ''', (query, query, query))
        return cursor.fetchall()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    message = ''
    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics'].strip()
        song_number = request.form.get('song_number', '').strip()
        page_number = request.form.get('page_number', '').strip()
        key_root = request.form.get('key_root', '').strip()
        key_type = request.form.get('key_type', '').strip()

        key = f"{key_root} {key_type}".strip() if key_root else ''

        if not title or not lyrics:
            message = 'Song title and lyrics are required.'
        else:
            try:
                with sqlite3.connect(DATABASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO songs (title, lyrics, key, song_number, page_number)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (title, lyrics, key, song_number, page_number))
                    conn.commit()
                message = 'Song added successfully!'
            except sqlite3.IntegrityError:
                message = 'A song with this title already exists.'

    return render_template('add.html', message=message)

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    query = ''
    searched = False

    if request.method == 'POST':
        query = request.form['query'].strip()
        results = search_songs(query)
        searched = True

    all_songs = get_all_songs()
    return render_template('search.html', results=results, query=query, searched=searched, all_songs=all_songs)

# Initialize database only if it doesn't exist
if not os.path.exists(DATABASE):
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
