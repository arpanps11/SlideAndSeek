from flask import Flask, render_template, request, send_file, redirect, url_for
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
import io
import json
import os

app = Flask(__name__)

DATA_FILE = "songs.json"

# Load song data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        song_data = json.load(f)
else:
    song_data = []

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/add", methods=["GET", "POST"])
def add_song():
    if request.method == "POST":
        title = request.form["title"].strip()
        key = request.form["key"].strip()
        lyrics = request.form["lyrics"].strip()
        new_song = {"title": title, "key": key, "lyrics": lyrics}
        song_data.append(new_song)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(song_data, f, indent=2)
        return redirect(url_for("home"))
    return render_template("add_song.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    query = ""
    results = []
    all_songs = song_data
    if request.method == "POST":
        query = request.form["query"].lower()
        results = [
            song for song in song_data
            if query in song["title"].lower()
            or query in song["key"].lower()
            or query in song["lyrics"].lower()
        ]
    return render_template("search.html", results=results, all_songs=all_songs)

@app.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "POST":
        data = request.json
        sections = data["sections"]
        filename = f"{datetime.now().strftime('%Y_%m_%d')}_SlideAndSeek.pptx"

        prs = Presentation()
        blank_slide_layout = prs.slide_layouts[6]

        def add_lyrics_slide(section, title, lyrics):
            stanzas = [s.strip() for s in lyrics.split("\n\n") if s.strip()]
            for stanza in stanzas:
                slide = prs.slides.add_slide(blank_slide_layout)
                tf = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5)).text_frame
                tf.text = f"{section} - {title}"
                tf.paragraphs[0].font.size = Pt(20)
                tf.add_paragraph()  # spacing
                p = tf.add_paragraph()
                p.text = stanza.replace('\r', '').replace('\n', '\n')
                p.font.size = Pt(32)

        for section_block in sections:
            section_name = section_block["section"]
            songs = section_block["songs"]
            for song_title in songs:
                match = next((s for s in song_data if s["title"] == song_title), None)
                if match:
                    add_lyrics_slide(section_name, match["title"], match["lyrics"])

        ppt_io = io.BytesIO()
        prs.save(ppt_io)
        ppt_io.seek(0)

        return send_file(ppt_io, as_attachment=True, download_name=filename)

    return render_template("generate.html", all_songs=song_data)

if __name__ == "__main__":
    app.run(debug=True)
