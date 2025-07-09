
from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
from pptx import Presentation
from pptx.util import Inches, Pt
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('songs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    lyrics TEXT NOT NULL,
                    key TEXT,
                    song_number TEXT,
                    page_number TEXT
                )''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        lyrics = request.form['lyrics']
        key = request.form['key']
        song_number = request.form.get('song_number')
        page_number = request.form.get('page_number')
        conn = sqlite3.connect('songs.db')
        c = conn.cursor()
        c.execute("INSERT INTO songs (title, lyrics, key, song_number, page_number) VALUES (?, ?, ?, ?, ?)",
                  (title, lyrics, key, song_number, page_number))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('add.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    conn = sqlite3.connect('songs.db')
    c = conn.cursor()
    c.execute("SELECT title, key, lyrics FROM songs WHERE title LIKE ? OR lyrics LIKE ?", (f'%{query}%', f'%{query}%'))
    results = c.fetchall()
    conn.close()
    return render_template('search.html', results=results, query=query)

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    conn = sqlite3.connect('songs.db')
    c = conn.cursor()
    c.execute("SELECT id, title FROM songs")
    all_songs = c.fetchall()

    if request.method == 'POST':
        data = request.form.to_dict(flat=False)
        prs = Presentation()
        blank_slide_layout = prs.slide_layouts[6]

        section_order = data['sections[]']
        for section in section_order:
            songs_in_section = data.get(f'{section}_songs[]', [])
            if not songs_in_section:
                continue

            if section in ['Opening Hymn', 'Offertory Hymn', 'Communion Hymn']:
                c.execute("SELECT title, song_number, page_number, lyrics FROM songs WHERE id = ?", (songs_in_section[0],))
                song = c.fetchone()
                if song:
                    title, number, page, lyrics = song
                    header_slide = prs.slides.add_slide(blank_slide_layout)
                    tf = header_slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1.5)).text_frame
                    header_text = f"{section}
{title}"
                    if number:
                        header_text += f"
Song No: {number}"
                    if page:
                        header_text += f"
Page No: {page}"
                    tf.text = header_text
                    tf.paragraphs[0].font.size = Pt(32)
                    for stanza in lyrics.strip().split('

'):
                        slide = prs.slides.add_slide(blank_slide_layout)
                        text_frame = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5)).text_frame
                        for line in stanza.strip().split('
'):
                            p = text_frame.add_paragraph()
                            p.text = line.strip()
                            p.font.size = Pt(24)
            else:  # Praise and Worship or others
                for song_id in songs_in_section:
                    c.execute("SELECT title, lyrics FROM songs WHERE id = ?", (song_id,))
                    song = c.fetchone()
                    if song:
                        title, lyrics = song
                        title_slide = prs.slides.add_slide(blank_slide_layout)
                        tf = title_slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1.5)).text_frame
                        tf.text = title
                        tf.paragraphs[0].font.size = Pt(36)
                        for stanza in lyrics.strip().split('

'):
                            slide = prs.slides.add_slide(blank_slide_layout)
                            text_frame = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5)).text_frame
                            for line in stanza.strip().split('
'):
                                p = text_frame.add_paragraph()
                                p.text = line.strip()
                                p.font.size = Pt(24)

        output = BytesIO()
        date_str = datetime.now().strftime('%Y_%m_%d')
        filename = f"{date_str}_Sunday_Service_Slides.pptx"
        prs.save(output)
        output.seek(0)
        conn.close()
        return send_file(output, as_attachment=True, download_name=filename)

    conn.close()
    return render_template('generate.html', songs=all_songs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
