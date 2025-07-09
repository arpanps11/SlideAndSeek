from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "songs.db"

# --- Helper: initialize DB if not exists ---
def initialize_db():
    if not os.path.exists(DB_PATH):
        import import_songs  # This runs the import if DB is missing

# --- DB Access functions ---
def get_all_songs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs")
    songs = [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]
    conn.close()
    return songs

def search_songs(query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"%{query.lower()}%"
    cursor.execute("""
        SELECT title, key, lyrics FROM songs 
        WHERE LOWER(title) LIKE ? OR LOWER(key) LIKE ? OR LOWER(lyrics) LIKE ?
    """, (query, query, query))
    results = cursor.fetchall()
    conn.close()
    return [{"title": row[0], "key": row[1], "lyrics": row[2]} for row in results]

# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    initialize_db()  # Ensure DB is available
    results = []
    all_songs = get_all_songs()
    if request.method == 'POST':
        query = request.form.get('query', '')
        results = search_songs(query)
    return render_template('search.html', results=results, all_songs=all_songs)

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    initialize_db()
    if request.method == 'POST':
        title = request.form.get('title')
        key = request.form.get('key')
        lyrics = request.form.get('lyrics')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO songs (title, key, lyrics) VALUES (?, ?, ?)", (title, key, lyrics))
        conn.commit()
        conn.close()
        return redirect(url_for('search'))
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)
