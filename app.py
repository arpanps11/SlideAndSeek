from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey_root'

DB_FILE = 'songs.db'
PASSWORD = 'ebccni@2025'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
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

# ---------- Songs Routes Unchanged (add, edit, search) ----------
# ---------- Responsive Reading Routes Unchanged (rr_add, rr_search, rr_edit) ----------
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
               OR LOWER(COALESCE(key_root, '') || ' ' || COALESCE(key_type, '')) LIKE ?
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
            return redirect(url_for('rr_add'))  # 🔁 This resets the form

    return render_template('rr_add.html', error=error)

@app.route('/rr_search', methods=['GET', 'POST'])
def rr_search():
    conn = sqlite3.connect('songs.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Always fetch the dropdown list
    cursor.execute("SELECT id, rr_number, psalm_number FROM responsive_readings ORDER BY rr_number ASC")
    rr_list = cursor.fetchall()

    rr = None
    selected_id = None
    searched = False

    if request.method == 'POST' or request.args.get('selected_id'):
        selected_id = request.form.get('rr_id') or request.args.get('selected_id')
        searched = True
        if selected_id:
            cursor.execute("SELECT * FROM responsive_readings WHERE id = ?", (selected_id,))
            rr = cursor.fetchone()

    conn.close()

    return render_template('rr_search.html', rr_list=rr_list, rr=rr, selected_id=selected_id, searched=searched)


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
            return redirect(url_for('rr_search', selected_id=rr_id))

    conn.close()
    return render_template('rr_edit.html', rr=rr, error=error)


# ---------- Generate Slides Route ----------
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        form = request.form
        section_order = form.getlist('section_order[]')
        ppt = Presentation()

        conn = get_db_connection()
        cursor = conn.cursor()

        for section in section_order:
            if section == 'welcome':
                welcome_text = form.get('welcome_text', 'Welcome to the Sunday Worship Service')
                add_title_slide(ppt, welcome_text)

            elif section == 'praise':
                praise_ids = form.getlist('praise_ids[]')
                for song_id in praise_ids:
                    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
                    song = cursor.fetchone()
                    if song:
                        add_song_slides(ppt, song, include_title_slide=True)

            elif section in ['opening', 'offertory', 'communion']:
                song_id = form.get(f'{section}_id')
                if song_id:
                    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
                    song = cursor.fetchone()
                    if song:
                        title = section.capitalize() + " Hymn"
                        add_title_slide(ppt, f"{title}\n{song['title']}", subtitle=compose_song_meta(song))
                        add_song_slides(ppt, song)

            elif section == 'rr':
                rr_id = form.get('rr_id')
                if rr_id:
                    cursor.execute("SELECT * FROM responsive_readings WHERE id = ?", (rr_id,))
                    rr = cursor.fetchone()
                    if rr:
                        rr_title = f"Responsive Reading {rr['rr_number']}\nPsalm {rr['psalm_number']}\nPage Number {rr['page_number']}\n{rr['title']}"
                        add_title_slide(ppt, rr_title)
                        verses = split_into_paragraphs(rr['content'])
                        i = 0
                        while i < len(verses):
                            v1 = verses[i]
                            if i + 1 < len(verses) and count_lines(v1) <= 4 and count_lines(verses[i+1]) <= 4:
                                add_content_slide(ppt, f"{v1}\n\n{verses[i+1]}")
                                i += 2
                            else:
                                add_content_slide(ppt, v1)
                                i += 1

            elif section == 'extras':
                extra_title = form.get('extras_title', 'Special Number')
                extra_ids = form.getlist('extras_ids[]')
                for song_id in extra_ids:
                    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
                    song = cursor.fetchone()
                    if song:
                        title = f"{extra_title}\n{song['title']}"
                        add_title_slide(ppt, title, subtitle=compose_song_meta(song))
                        add_song_slides(ppt, song)

            elif section == 'benediction':
                add_title_slide(ppt, "Benediction")
                benedict_lyrics = (
                    "Praise God, from Whom all blessings flow;\n"
                    "Praise Him, all creatures here below;\n"
                    "Praise Him above, ye heavenly host;\n"
                    "Praise Father, Son, and Holy Ghost!\n"
                    "Amen"
                )
                add_content_slide(ppt, benedict_lyrics)

        conn.close()

        buffer = BytesIO()
        ppt.save(buffer)
        buffer.seek(0)

        today = datetime.today().strftime('%d_%m_%Y')
        filename = f'Worship_{today}.pptx'
        return send_file(buffer, as_attachment=True, download_name=filename)

    # GET request (just render form)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs ORDER BY title ASC")
    songs = cursor.fetchall()
    cursor.execute("SELECT id, rr_number, psalm_number FROM responsive_readings ORDER BY rr_number ASC")
    rrs = cursor.fetchall()
    conn.close()
    return render_template('generate.html', songs=songs, rrs=rrs)

# ---------- Slide Utility Functions ----------
def add_title_slide(ppt, title, subtitle=None):
    slide_layout = ppt.slide_layouts[0]
    slide = ppt.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    if subtitle:
        slide.placeholders[1].text = subtitle

def add_content_slide(ppt, content):
    slide_layout = ppt.slide_layouts[1]
    slide = ppt.slides.add_slide(slide_layout)
    title = slide.shapes.title
    body = slide.placeholders[1]
    title.text = ""
    body.text = content

def add_song_slides(ppt, song, include_title_slide=False):
    if include_title_slide:
        meta = compose_song_meta(song)
        add_title_slide(ppt, song['title'], meta)
    stanzas = split_into_paragraphs(song['lyrics'])
    for stanza in stanzas:
        add_content_slide(ppt, stanza)

def split_into_paragraphs(text):
    return [p.strip() for p in text.split('\n\n') if p.strip()]

def count_lines(text):
    return len(text.strip().split('\n'))

def compose_song_meta(song):
    parts = []
    if song['song_number']:
        parts.append(f"Song #{song['song_number']}")
    if song['page_number']:
        parts.append(f"Page {song['page_number']}")
    return " | ".join(parts) if parts else ""

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
