import os

APP_DIR = os.path.join(os.getcwd(), "MusicLibrary")
DATA_FILE = os.path.join(APP_DIR, "music_data.json")
SONG_DIR = os.path.join(APP_DIR, "songs")

AUDIO_EXTS = (".mp3", ".m4a", ".wav", ".aac", ".flac")

DEFAULT_VOLUME = 80
