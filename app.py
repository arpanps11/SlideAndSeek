from flask import Flask, render_template, request, send_file
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import os
import datetime
import sqlite3

app = Flask(__name__)
DB_FILE = 'songs.db'

# ✅ Step 1: Create songs table if it doesn’t exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            lyrics TEXT NOT NULL,
            key TEXT,
            song_number TEXT,
            page_number TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()  # Run it when app starts


# Helper: Get song details
def get_song_by_id(song_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, lyrics FROM songs WHERE id=?", (song_id,))
    song = cursor.fetchone()
    conn.close()
    return song

# Helper: Get all song titles for autocomplete
def get_all_songs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs")
    songs = [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]
    conn.close()
    return songs


# Route: Home page
@app.route('/')
def home():
    return render_template('home.html')


# Route: Add song
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        lyrics = request.form['lyrics']
        key = request.form['key']
        song_number = request.form.get('song_number', '')
        page_number = request.form.get('page_number', '')

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO songs (title, lyrics, key, song_number, page_number) VALUES (?, ?, ?, ?, ?)",
                       (title, lyrics, key, song_number, page_number))
        conn.commit()
        conn.close()
        return 'Song added successfully!'
    return render_template('add.html')


# ✅ Route: Search songs
@app.route('/search', methods=['GET', 'POST'])
def search():
    query = ''
    results = []
    searched = False  # Track whether a real search was performed

    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        searched = True
        if query:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT title, lyrics, key FROM songs WHERE title LIKE ? OR lyrics LIKE ?", 
                           (f'%{query}%', f'%{query}%'))
            results = cursor.fetchall()
            conn.close()

    # Get all songs for the autocomplete box
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM songs")
    all_songs = [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]
    conn.close()

    return render_template('search.html', results=results, query=query, searched=searched, all_songs=all_songs)


# Route: Generate presentation
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        sections = request.form.getlist('sections[]')
        prs = Presentation()

        for section in sections:
            add_slide(prs, section, title_slide=True)

            song_ids = request.form.getlist(f'{section}_songs[]')
            if song_ids:
                for i, song_id in enumerate(song_ids):
                    song = get_song_by_id(song_id)
                    if song:
                        title, lyrics = song
                        if section in ["Opening Hymn", "Offertory Hymn", "Communion Hymn"] and i == 0:
                            number = request.form.get(f'{section}_number', '')
                            page = request.form.get(f'{section}_page', '')
                            details = f"Song: {title}"
                            if number:
                                details += f"\nSong No: {number}"
                            if page:
                                details += f" | Page No: {page}"
                            add_slide(prs, details)

                        elif section == "Praise and Worship":
                            add_slide(prs, title, title_slide=True)

                        stanzas = lyrics.strip().split('\n\n')
                        for stanza in stanzas:
                            clean_lines = [line.replace('_x000D_', '').strip() for line in stanza.strip().split('\n') if line.strip()]
                            stanza_text = '\n'.join(clean_lines)
                            if stanza_text:
                                add_slide(prs, stanza_text)

        today = datetime.date.today().strftime("%Y_%m_%d")
        filename = f"{today}_church_service_slides.pptx"
        filepath = os.path.join("generated", filename)
        if not os.path.exists("generated"):
            os.makedirs("generated")
        prs.save(filepath)
        return send_file(filepath, as_attachment=True)

    return render_template('generate.html')


# Helper: Add slides
def add_slide(prs, text, title_slide=False):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1), Inches(9), Inches(5.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    font = run.font
    font.size = Pt(36 if title_slide else 32)
    font.name = 'Calibri'
    font.bold = True
    font.color.rgb = RGBColor(0, 0, 0)
    return slide


# Start the server
if __name__ == '__main__':
    app.run(debug=True)
