from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DATABASE = 'songs.db'
ACCESS_PASSWORD = 'ebccni@2025'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    conn = get_db_connection()
    songs = conn.execute('SELECT title FROM songs').fetchall()
    conn.close()
    all_songs = [song['title'] for song in songs]
    return render_template('search.html', all_songs=all_songs, searched=False)

@app.route('/', methods=['POST'])
def search():
    query = request.form['query'].strip()
    conn = get_db_connection()
    results = conn.execute("""
        SELECT title, lyrics, key, key_type, song_number, id
        FROM songs
        WHERE title LIKE ? OR lyrics LIKE ? OR key LIKE ?
    """, ('%' + query + '%', '%' + query + '%', '%' + query + '%')).fetchall()
    songs = conn.execute('SELECT title FROM songs').fetchall()
    conn.close()
    all_songs = [song['title'] for song in songs]
    return render_template('search.html', results=results, query=query, searched=True, all_songs=all_songs)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        password = request.form['password']
        if password == ACCESS_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('add_song'))
        else:
            flash('Incorrect password. Access denied.')
    return render_template('verify.html')

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('authenticated'):
        return redirect(url_for('verify'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics'].strip()
        key = request.form.get('key') or None
        key_type = request.form.get('key_type') or None
        song_number = request.form.get('song_number') or None
        page_number = request.form.get('page_number') or None

        if not title or not lyrics:
            flash('Song title and lyrics are required.', 'error')
            return render_template('add.html')

        try:
            conn = get_db_connection()
            existing = conn.execute("SELECT id FROM songs WHERE title = ?", (title,)).fetchone()
            if existing:
                flash('A song with this title already exists.', 'error')
                conn.close()
                return render_template('add.html')

            conn.execute("""
                INSERT INTO songs (title, lyrics, key, key_type, song_number, page_number)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, lyrics, key, key_type, song_number, page_number))
            conn.commit()
            conn.close()
            flash('Song added successfully!', 'success')
        except Exception as e:
            flash('Something went wrong while adding the song.', 'error')
    return render_template('add.html')

@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    if not session.get('authenticated'):
        return redirect(url_for('verify'))

    conn = get_db_connection()
    song = conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()

    if not song:
        conn.close()
        flash('Song not found.', 'error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics'].strip()
        key = request.form.get('key') or None
        key_type = request.form.get('key_type') or None
        song_number = request.form.get('song_number') or None
        page_number = request.form.get('page_number') or None

        if not title or not lyrics:
            flash('Song title and lyrics are required.', 'error')
            return render_template('edit.html', song=song)

        try:
            # Check for duplicate title (but allow current song)
            existing = conn.execute("SELECT id FROM songs WHERE title = ? AND id != ?", (title, song_id)).fetchone()
            if existing:
                flash('Another song with this title already exists.', 'error')
                return render_template('edit.html', song=song)

            conn.execute("""
                UPDATE songs SET title = ?, lyrics = ?, key = ?, key_type = ?, song_number = ?, page_number = ?
                WHERE id = ?
            """, (title, lyrics, key, key_type, song_number, page_number, song_id))
            conn.commit()
            flash('Song updated successfully!', 'success')
            conn.close()
            return redirect(url_for('home'))
        except:
            flash('Something went wrong while updating.', 'error')

    conn.close()
    return render_template('edit.html', song=song)

if __name__ == '__main__':
    app.run(debug=True)
