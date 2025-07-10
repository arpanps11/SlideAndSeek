from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management
DATABASE = 'songs.db'
PASSWORD = 'ebccni@2025'  # Shared password

# Utility to initialize DB if needed (optional)
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
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

# Verification route
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    next_page = request.args.get('next', '/')
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['verified'] = True
            return redirect(next_page)
        else:
            return render_template('verify.html', error='Incorrect password', next=next_page)
    return render_template('verify.html', next=next_page)

# Add song route
@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('verified'):
        return redirect(url_for('verify', next='/add'))

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
        return redirect('/')

    return render_template('add.html')

# Search function
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

# Autocomplete titles
def get_all_titles():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM songs")
        return [{'title': row[0]} for row in cursor.fetchall()]

# Search page
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

# Edit song
@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    if not session.get('verified'):
        return redirect(url_for('verify', next=url_for('edit_song', song_id=song_id)))

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

@app.route('/generate')
def generate():
    return "Coming soon"

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
