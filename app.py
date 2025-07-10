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
                key_note TEXT,
                key_type TEXT,
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
        cursor.execute("""
            SELECT id, title, lyrics, key_note, key_type 
            FROM songs 
            WHERE title LIKE ? OR lyrics LIKE ? OR key_note LIKE ? OR key_type LIKE ?
        """, (query, query, query, query))
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
        key_note = request.form.get('key_note', '').strip()
        key_type = request.form.get('key_type', '').strip()
        song_number = request.form.get('song_number', '').strip()
        page_number = request.form.get('page_number', '').strip()

        if not title or not lyrics or not key_note or not key_type:
            message = 'Song Title, Lyrics, Key, and Key Type are required.'
        else:
            try:
                with sqlite3.connect(DATABASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO songs (title, lyrics, key_note, key_type, song_number, page_number)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (title, lyrics, key_note, key_type, song_number, page_number))
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
        searched = True
        results = search_songs(query)

    all_songs = get_all_songs()
    return render_template('search.html', results=results, query=query, searched=searched, all_songs=all_songs)


@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            title = request.form['title'].strip()
            lyrics = request.form['lyrics'].strip()
            key_note = request.form.get('key_note', '').strip()
            key_type = request.form.get('key_type', '').strip()
            song_number = request.form.get('song_number', '').strip()
            page_number = request.form.get('page_number', '').strip()

            if not title or not lyrics or not key_note or not key_type:
                return "Missing required fields", 400

            try:
                cursor.execute("""
                    UPDATE songs
                    SET title = ?, lyrics = ?, key_note = ?, key_type = ?, song_number = ?, page_number = ?
                    WHERE id = ?
                """, (title, lyrics, key_note, key_type, song_number, page_number, song_id))
                conn.commit()
                return redirect(url_for('search'))
            except sqlite3.IntegrityError:
                return "A song with this title already exists", 400

        # GET method - fetch song to edit
        cursor.execute("SELECT id, title, lyrics, key_note, key_type, song_number, page_number FROM songs WHERE id = ?", (song_id,))
        song = cursor.fetchone()

    if not song:
        return "Song not found", 404

    song_dict = {
        'id': song[0],
        'title': song[1],
        'lyrics': song[2],
        'key_note': song[3],
        'key_type': song[4],
        'song_number': song[5],
        'page_number': song[6]
    }

    return render_template('edit.html', song=song_dict)

# Initialize database only if it doesn't exist
if not os.path.exists(DATABASE):
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
