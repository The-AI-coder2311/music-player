import json
import os
from config import DATA_FILE

class PlaylistManager:
    def __init__(self):
        self.playlists = {}
        self.current_playlist = None
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.playlists = data.get("playlists", {})
                self.current_playlist = data.get("current_playlist")

    def save(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump({
                "playlists": self.playlists,
                "current_playlist": self.current_playlist
            }, f, indent=2)

    def add_playlist(self, name):
        if name not in self.playlists:
            self.playlists[name] = []
            self.current_playlist = name
            self.save()

    def remove_playlist(self, name):
        if name in self.playlists:
            del self.playlists[name]

            if not self.playlists:
                self.playlists["Default"] = []

            if self.current_playlist == name:
                self.current_playlist = list(self.playlists.keys())[0]

            self.save()

    def get_current(self):
        return self.playlists.get(self.current_playlist, [])
