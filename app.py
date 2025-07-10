from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'songs.db'
SONG_EDIT_PASSWORD = "ebccni@2025"

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Add song route
@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('authenticated'):
        return redirect(url_for('verify', next='/add'))

    message = None
    error = None

    if request.method == 'POST':
        try:
            title = request.form['title'].strip()
            lyrics = request.form['lyrics'].strip()
            key_root = request.form['key_root'].strip() or None
            key_type = request.form['key_type'].strip() or None
            song_number = request.form['song_number'].strip() or None
            page_number = request.form['page_number'].strip() or None

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM songs WHERE title = ?", (title,))
                if cursor.fetchone()[0] > 0:
                    error = "A song with this title already exists."
                else:
                    cursor.execute("""
                        INSERT INTO songs (title, lyrics, key_root, key_type, song_number, page_number)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (title, lyrics, key_root, key_type, song_number, page_number))
                    conn.commit()
                    message = "Song added successfully!"
        except Exception as e:
            error = "An error occurred while adding the song."

    return render_template('add.html', message=message, error=error)

# Search function
def search_songs(query):
    query = query.strip()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        like_query = f"%{query}%"
        cursor.execute("""
            SELECT title, lyrics, key_root, key_type, song_number, id
            FROM songs
            WHERE title LIKE ? OR lyrics LIKE ? OR key_root LIKE ? OR key_type LIKE ?
        """, (like_query, like_query, like_query, like_query))
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
    if not session.get('authenticated'):
        return redirect(url_for('verify', next=f'/edit/{song_id}'))

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            try:
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
            except Exception as e:
                return "Something went wrong while updating.", 400

        cursor.execute("""
            SELECT title, lyrics, key_root, key_type, song_number, page_number
            FROM songs
            WHERE id = ?
        """, (song_id,))
        song = cursor.fetchone()

    return render_template('edit.html', song=song, song_id=song_id)

# Password verification
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    next_page = request.args.get('next', '/')
    error = None

    if request.method == 'POST':
        password = request.form['password']
        if password == SONG_EDIT_PASSWORD:
            session['authenticated'] = True
            return redirect(next_page)
        else:
            error = "Incorrect password. Try again."

    return render_template('verify.html', next_page=next_page, error=error)

# Generate route (optional)
@app.route('/generate')
def generate():
    return "Coming soon"

if __name__ == '__main__':
    app.run(debug=True)
