from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import json

app = Flask(__name__)

DB_PATH = 'songs.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_table_if_not_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            lyrics TEXT NOT NULL,
            key TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_songs_from_json():
    if not os.path.exists(DB_PATH) and os.path.exists('songs.json'):
        with open('songs.json', 'r', encoding='utf-8') as f:
            songs = json.load(f)

        conn = get_db_connection()
        cursor = conn.cursor()
        for song in songs:
            cursor.execute('INSERT INTO songs (title, lyrics, key) VALUES (?, ?, ?)',
                           (song.get('title'), song.get('lyrics'), song.get('key')))
        conn.commit()
        conn.close()

def get_all_songs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs")
    songs = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"]} for row in songs]

def search_songs(query):
    conn = get_db_connection()
    cursor = conn.cursor()

    like_query = f"%{query}%"
    cursor.execute("""
        SELECT id, title, lyrics, key FROM songs
        WHERE title LIKE ? OR key LIKE ? OR lyrics LIKE ?
    """, (like_query, like_query, like_query))

    rows = cursor.fetchall()
    conn.close()

    # Deduplicate by song ID
    unique_songs = {}
    for row in rows:
        unique_songs[row["id"]] = {
            "id": row["id"],
            "title": row["title"],
            "lyrics": row["lyrics"],
            "key": row["key"]
        }

    return list(unique_songs.values())

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = ""
    results = []
    searched = False

    if request.method == 'POST':
        query = request.form.get('query', '')
        if query:
            results = search_songs(query)
            searched = True

    all_songs = get_all_songs()
    return render_template("search.html", results=results, all_songs=all_songs, searched=searched, query=query)

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if request.method == 'POST':
        title = request.form.get('title')
        lyrics = request.form.get('lyrics')
        key = request.form.get('key')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO songs (title, lyrics, key) VALUES (?, ?, ?)',
                       (title, lyrics, key))
        conn.commit()
        conn.close()

        return redirect(url_for('add_song'))

    return render_template("add.html")

# Ensure DB is ready
create_table_if_not_exists()
load_songs_from_json()

if __name__ == '__main__':
    app.run(debug=True)
