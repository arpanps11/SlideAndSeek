from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///songs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

PASSWORD = 'ebccni@2025'

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    key_note = db.Column(db.String(5))
    key_type = db.Column(db.String(5))
    song_number = db.Column(db.String(3))
    page_number = db.Column(db.String(3))

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    songs = Song.query.order_by(Song.title).all()
    return render_template('search.html', songs=songs, all_songs=[song.title for song in songs])

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['verified'] = True
            return redirect(request.args.get('next') or url_for('add_song'))
        else:
            return render_template('verify.html', error="Incorrect password.")
    return render_template('verify.html')

def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('verified'):
            return redirect(url_for('verify', next=request.path))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_song():
    message = ''
    if request.method == 'POST':
        title = request.form['title'].strip()
        lyrics = request.form['lyrics']
        song_number = request.form.get('song_number') or None
        page_number = request.form.get('page_number') or None
        key_note = request.form.get('key_root') or None
        key_type = request.form.get('key_type') or None

        # Prevent duplicate titles
        if Song.query.filter_by(title=title).first():
            message = "A song with this title already exists."
        else:
            try:
                new_song = Song(
                    title=title,
                    lyrics=lyrics,
                    key_note=key_note,
                    key_type=key_type,
                    song_number=song_number,
                    page_number=page_number
                )
                db.session.add(new_song)
                db.session.commit()
                message = "Song added successfully!"
            except IntegrityError:
                db.session.rollback()
                message = "A song with this title already exists."
            except Exception as e:
                db.session.rollback()
                message = "Something went wrong."

    return render_template('add.html', message=message)

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.form.get('query', '').strip()
    songs = []
    if query:
        songs = Song.query.filter(Song.title.ilike(f"%{query}%")).all()
    all_songs = [song.title for song in Song.query.order_by(Song.title).all()]
    return render_template('search.html', songs=songs, query=query, all_songs=all_songs)

@app.route('/edit/<int:song_id>', methods=['GET', 'POST'])
@login_required
def edit_song(song_id):
    song = Song.query.get_or_404(song_id)
    message = ''
    if request.method == 'POST':
        try:
            song.title = request.form['title'].strip()
            song.lyrics = request.form['lyrics']
            song.key_note = request.form.get('key_note') or None
            song.key_type = request.form.get('key_type') or None
            song.song_number = request.form.get('song_number') or None
            song.page_number = request.form.get('page_number') or None
            db.session.commit()
            message = "Song updated successfully!"
        except Exception as e:
            db.session.rollback()
            message = "Something went wrong while updating."
    return render_template('edit.html', song=[song.title, song.lyrics, song.key_note, song.key_type, song.song_number, song.page_number], message=message)

if __name__ == '__main__':
    app.run(debug=True)
