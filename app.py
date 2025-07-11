from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey_root'

DB_FILE = 'songs.db'
PASSWORD = 'ebccni@2025'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

# ---------- Routes ----------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    error = None
    next_page = request.args.get('next', '/')
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['authenticated'] = True
            return redirect(next_page)
        else:
            error = "Incorrect password. Try again."
    return render_template('verify.html', error=error, next=next_page)

# ---------- Songs ----------

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if not session.get('authenticated'):
        return redirect(url_for('verify', next='/add'))

    error = None

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        lyrics = request.form.get('lyrics', '').strip()
        song_number = request.form.get('song_number')
        page_number = request.form.get('page_number')
        key_root = request.form.get('key_root')
        key_type = request.form.get('key_type')

        if not title or not lyrics:
            error = "Song Title and Lyrics are required."
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM songs WHERE LOWER(title) = LOWER(?)", (title.lower(),))
            existing = cursor.fetchone()

            if existing:
                error = "Song title already exists."
            else:
                cursor.execute("""
                    INSERT INTO songs (title, lyrics, song_number, page_number, key_root, key_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, lyrics, song_number, page_number, key_root, key_type))
                conn.commit()
                flash("Song added successfully.")
            conn.close()

    return render_template('add.html', error=error)

@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    if not session.get('authenticated'):
        return redirect(url_for('verify', next=f'/edit/{song_id}'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()

    if not song:
        conn.close()
        return "Song not found", 404

    error = None

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        lyrics = request.form.get('lyrics', '').strip()
        song_number = request.form.get('song_number')
        page_number = request.form.get('page_number')
        key_root = request.form.get('key_root')
        key_type = request.form.get('key_type')

        if not title or not lyrics:
            error = "Title and lyrics are required."
        else:
            cursor.execute("SELECT id FROM songs WHERE LOWER(title) = LOWER(?) AND id != ?", (title.lower(), song_id))
            duplicate = cursor.fetchone()
            if duplicate:
                error = "Another song with this title already exists."
            else:
                cursor.execute("""
                    UPDATE songs
                    SET title = ?, lyrics = ?, song_number = ?, page_number = ?, key_root = ?, key_type = ?
                    WHERE id = ?
                """, (title, lyrics, song_number, page_number, key_root, key_type, song_id))
                conn.commit()
                conn.close()
                flash("Song updated successfully.")
                return redirect(url_for('search', query=title))
    else:
        conn.close()

    return render_template('edit.html', song=song, error=error)

@app.route('/search', methods=['GET', 'POST'])
def search():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM songs")
    all_songs = [{'title': row[0]} for row in cursor.fetchall()]

    query = request.args.get('query', '').strip().lower()
    results = []
    searched = bool(query)

    if request.method == 'POST':
        query = request.form.get('query', '').strip().lower()
        searched = True

    if searched:
        cursor.execute("""
            SELECT title, lyrics, key_root, key_type, song_number, id FROM songs
            WHERE LOWER(title) LIKE ? 
               OR LOWER(lyrics) LIKE ? 
               OR LOWER(key_root || ' ' || IFNULL(key_type, '')) LIKE ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        results = cursor.fetchall()

    conn.close()
    return render_template('search.html', results=results, searched=searched, query=query, all_songs=all_songs)

# ---------- Responsive Readings ----------

@app.route('/rr_home')
def rr_home():
    return render_template('rr_home.html')

@app.route('/rr_add', methods=['GET', 'POST'])
def rr_add():
    if not session.get('authenticated'):
        return redirect(url_for('verify', next='/rr_add'))

    error = None
    if request.method == 'POST':
        rr_number = request.form.get('rr_number')
        psalm_number = request.form.get('psalm_number')
        page_number = request.form.get('page_number')
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not all([rr_number, psalm_number, page_number, title, content]):
            error = "All fields are required."
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO responsive_readings (rr_number, psalm_number, page_number, title, content)
                VALUES (?, ?, ?, ?, ?)
            """, (rr_number, psalm_number, page_number, title, content))
            conn.commit()
            conn.close()
            flash("Responsive Reading added successfully.")

    return render_template('rr_add.html', error=error)

@app.route('/rr_search', methods=['GET', 'POST'])
def rr_search():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, rr_number, psalm_number FROM responsive_readings ORDER BY rr_number ASC")
    rr_list = cursor.fetchall()

    selected_rr_id = request.form.get('rr_id') if request.method == 'POST' else None
    selected_rr = None

    if selected_rr_id:
        cursor.execute("SELECT * FROM responsive_readings WHERE id = ?", (selected_rr_id,))
        selected_rr = cursor.fetchone()

    conn.close()
    return render_template('rr_search.html', rr_list=rr_list, selected_rr=selected_rr)

@app.route('/rr_edit/<int:rr_id>', methods=['GET', 'POST'])
def rr_edit(rr_id):
    if not session.get('authenticated'):
        return redirect(url_for('verify', next=f'/rr_edit/{rr_id}'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM responsive_readings WHERE id = ?", (rr_id,))
    rr = cursor.fetchone()

    if not rr:
        conn.close()
        return "Responsive Reading not found", 404

    error = None

    if request.method == 'POST':
        rr_number = request.form.get('rr_number')
        psalm_number = request.form.get('psalm_number')
        page_number = request.form.get('page_number')
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not all([rr_number, psalm_number, page_number, title, content]):
            error = "All fields are required."
        else:
            cursor.execute("""
                UPDATE responsive_readings
                SET rr_number = ?, psalm_number = ?, page_number = ?, title = ?, content = ?
                WHERE id = ?
            """, (rr_number, psalm_number, page_number, title, content, rr_id))
            conn.commit()
            conn.close()
            flash("Responsive Reading updated successfully.")
            return redirect(url_for('rr_search'))

    conn.close()
    return render_template('rr_edit.html', rr=rr, error=error)

@app.route('/generate')
def generate():
    return "This is the generate worship slides page. Coming soon!"

# ---------- DB Initialization ----------

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                lyrics TEXT NOT NULL,
                song_number TEXT,
                page_number TEXT,
                key_root TEXT,
                key_type TEXT
            )
        ''')
        conn.commit()
        conn.close()

    # Ensure RR table exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responsive_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rr_number INTEGER NOT NULL,
            psalm_number INTEGER NOT NULL,
            page_number TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

    app.run(debug=True)
