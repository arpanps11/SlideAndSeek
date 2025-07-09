import json
import sqlite3
import os

# Path to your JSON file
JSON_FILE = 'songs.json'  # Change if your filename is different
DB_FILE = 'songs.db'

# Make sure the DB doesn't already exist (optional safety)
if not os.path.exists(DB_FILE):
    print("Creating new database...")

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Step 1: Create the songs table
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

# Step 2: Read and parse the JSON file
with open(JSON_FILE, 'r', encoding='utf-8') as f:
    songs_data = json.load(f)

# Step 3: Insert each song into the database
for song in songs_data:
    title = song.get('title', '').strip()
    lyrics = song.get('lyrics', '').strip()
    key = song.get('key', '').strip()
    song_number = song.get('song_number', '').strip()
    page_number = song.get('page_number', '').strip()

    if title and lyrics:
        cursor.execute('''
            INSERT INTO songs (title, lyrics, key, song_number, page_number)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, lyrics, key, song_number, page_number))

conn.commit()
conn.close()

print("✅ All songs have been imported into the database!")
