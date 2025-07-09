from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_FILE = 'songs.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            lyrics TEXT NOT NULL,
            key TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_all_songs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs")
    songs = cursor.fetchall()
    conn.close()
    return [{'id': row[0], 'title': row[1]} for row in songs]

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
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM songs WHERE title = ?", (title,))
            existing_song = cursor.fetchone()
            if existing_song:
                message = f"A song with the title \"{title}\" already exists."
            else:
                cursor.execute("INSERT INTO songs (title, lyrics, key) VALUES (?, ?, ?)", (title, lyrics, key))
                conn.commit()
                message = 'Song added successfully.'
            conn.close()

    return render_template('add.html', message=message)

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    query = ""
    searched = False
    all_songs = get_all_songs()

    if request.method == 'POST':
        query = request.form['query'].strip()
        searched = True
        if query:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT title, lyrics, key FROM songs WHERE title LIKE ? OR lyrics LIKE ? OR key LIKE ?", 
                           ('%'+query+'%', '%'+query+'%', '%'+query+'%'))
            results = cursor.fetchall()
            conn.close()

    return render_template('search.html', results=results, query=query, searched=searched, all_songs=all_songs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
