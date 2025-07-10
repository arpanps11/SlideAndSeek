from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change to a random string

DATABASE = 'songs.db'

# Ensure DB exists
def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE NOT NULL,
                lyrics TEXT NOT NULL,
                key TEXT,
                key_type TEXT,
                song_number TEXT,
                page_number TEXT
            )
        ''')
        conn.commit()
        conn.close()

init_db()

@app.route('/')
def home():
    return render_template('search.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query'].strip().lower()

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, title FROM songs WHERE LOWER(title) LIKE ?", ('%' + query + '%',))
    results = c.fetchall()
    conn.close()

    return render_template('search.html', results=results, query=query)

@app.route('/song/<int:song_id>')
def view_song(song_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT title, lyrics FROM songs WHERE id = ?", (song_id,))
    song = c.fetchone()
    conn.close()

    if song:
        return render_template('view.html', song=song)
    else:
        return redirect('/')

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if 'authenticated' not in session:
        return redirect('/verify')

    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics'].strip()
        key_root = request.form.get('key_root') or None
        key_type = request.form.get('key_type') or None
        song_number = request.form.get('song_number') or None
        page_number = request.form.get('page_number') or None

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # Check for duplicate title
        c.execute("SELECT COUNT(*) FROM songs WHERE LOWER(title) = LOWER(?)", (title,))
        count = c.fetchone()[0]

        if count > 0:
            conn.close()
            return render_template('add.html', error="A song with this title already exists.")

        try:
            c.execute("""
                INSERT INTO songs (title, lyrics, key, key_type, song_number, page_number)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, lyrics, key_root, key_type, song_number, page_number))
            conn.commit()
            conn.close()
            return render_template('add.html', message="Song added successfully!")
        except Exception as e:
            conn.close()
            return render_template('add.html', error="Something went wrong while saving the song.")

    return render_template('add.html')

@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics'].strip()
        key_note = request.form.get('key_note') or None
        key_type = request.form.get('key_type') or None
        song_number = request.form.get('song_number') or None
        page_number = request.form.get('page_number') or None

        try:
            c.execute("""
                UPDATE songs SET
                    title = ?, lyrics = ?, key = ?, key_type = ?, song_number = ?, page_number = ?
                WHERE id = ?
            """, (title, lyrics, key_note, key_type, song_number, page_number, song_id))
            conn.commit()
            conn.close()
            return render_template('edit.html', song=(title, lyrics, key_note, key_type, song_number, page_number), message="Song updated successfully.")
        except Exception as e:
            conn.close()
            return render_template('edit.html', song=(title, lyrics, key_note, key_type, song_number, page_number), error="Something went wrong while updating.")

    else:
        c.execute("SELECT title, lyrics, key, key_type, song_number, page_number FROM songs WHERE id = ?", (song_id,))
        song = c.fetchone()
        conn.close()
        if song:
            return render_template('edit.html', song=song)
        else:
            return redirect('/')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'ebccni@2025':
            session['authenticated'] = True
            return redirect('/add')
        else:
            return render_template('verify.html', error='Incorrect password.')
    return render_template('verify.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect('/')
