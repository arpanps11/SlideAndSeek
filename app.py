from flask import Flask, render_template, request, send_file, redirect
import json
import os
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt

app = Flask(__name__)

SONG_FILE = 'songs.json'

SECTIONS = [
    "Praise and Worship",
    "Opening Hymn",
    "Responsive Reading",
    "Offertory Hymn",
    "Communion Hymn",
    "Extra / Optional",
    "Benediction"
]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def add_song():
    if request.method == 'POST':
        title = request.form['title']
        lyrics = request.form['lyrics']
        key = request.form['key']

        new_song = {
            "title": title,
            "lyrics": lyrics,
            "key": key
        }

        if os.path.exists(SONG_FILE):
            with open(SONG_FILE, 'r') as f:
                songs = json.load(f)
        else:
            songs = []

        songs.append(new_song)

        with open(SONG_FILE, 'w') as f:
            json.dump(songs, f, indent=4)

        return redirect('/')

    return render_template('add.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        query = request.form['query'].lower()

        if os.path.exists(SONG_FILE):
            with open(SONG_FILE, 'r') as f:
                songs = json.load(f)

            for song in songs:
                if (query in song['title'].lower()
                    or query in song['lyrics'].lower()
                    or query in song['key'].lower()):
                    results.append(song)

    return render_template('search.html', results=results)

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        data = request.get_json()
        selected = data['sections']

        with open(SONG_FILE, 'r') as f:
            all_songs = json.load(f)

        song_lookup = {song['title']: song for song in all_songs}

        prs = Presentation()
        blank_layout = prs.slide_layouts[5]

        # Title Slide
        title_slide = prs.slides.add_slide(prs.slide_layouts[0])
        title_slide.shapes.title.text = "Sunday Worship"
        title_slide.placeholders[1].text = datetime.now().strftime("%A, %d %B %Y")

        for section in selected:
            section_title = section['name']
            song_titles = section['songs']

            # Section slide (optional)
            slide = prs.slides.add_slide(blank_layout)
            tf = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(1.5)).text_frame
            p = tf.paragraphs[0]
            p.text = section_title
            p.font.size = Pt(40)

            for title in song_titles:
                song = song_lookup.get(title)
                if not song:
                    continue
                # Split into stanzas
                stanzas = song['lyrics'].replace('\r', '').strip().split('\n\n')
                for stanza in stanzas:
                    lines = stanza.strip().split('\n')
                    slide = prs.slides.add_slide(blank_layout)
                    text_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(8.5), Inches(6))
                    tf = text_box.text_frame
                    for line in lines:
                        if line.strip():
                            para = tf.add_paragraph()
                            para.text = line.strip()
                            para.font.size = Pt(32)

        filename = f"SlideAndSeek_{datetime.now().strftime('%Y_%m_%d')}.pptx"
        prs.save(filename)
        return send_file(filename, as_attachment=True)

    return render_template('generate.html', sections=SECTIONS)

if __name__ == '__main__':
    app.run(debug=True)
