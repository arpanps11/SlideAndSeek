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
                key TEXT
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
        cursor.execute("SELECT title, lyrics, key FROM songs WHERE title LIKE ? OR lyrics LIKE ? OR key LIKE ?", (query, query, query))
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
        key = request.form['key'].strip()

        if not title or not lyrics or not key:
            message = 'All fields are required.'
        else:
            try:
                with sqlite3.connect(DATABASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO songs (title, lyrics, key) VALUES (?, ?, ?)", (title, lyrics, key))
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
