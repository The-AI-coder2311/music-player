import os
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES

from config import *
from utils import format_time
from playlist_manager import PlaylistManager
from player_engine import PlayerEngine


class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Player Pro")
        self.root.geometry("1100x650")

        os.makedirs(SONG_DIR, exist_ok=True)

        self.pm = PlaylistManager()
        self.player = PlayerEngine()

        self.queue = []
        self.search_text = ""
        self.is_seeking = False

        if not self.pm.playlists:
            self.pm.playlists["Default"] = []

        if self.pm.current_playlist not in self.pm.playlists:
            self.pm.current_playlist = list(self.pm.playlists.keys())[0]

        self.build_ui()
        self.refresh_all()
        self.loop()

    # ---------------- UI ----------------
    def build_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT
        left = ttk.Frame(main)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Playlists").pack()

        self.playlist_box = tk.Listbox(left)
        self.playlist_box.pack(fill="x")
        self.playlist_box.bind("<<ListboxSelect>>", self.change_playlist)

        ttk.Button(left, text="Add Playlist", command=self.add_playlist).pack(fill="x")
        ttk.Button(left, text="Remove Playlist", command=self.remove_playlist).pack(fill="x")
        ttk.Button(left, text="Import Folder", command=self.import_folder).pack(fill="x")

        ttk.Separator(left).pack(fill="x", pady=5)

        ttk.Label(left, text="Songs").pack()

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_search)

        ttk.Entry(left, textvariable=self.search_var).pack(fill="x")

        self.song_box = tk.Listbox(left, height=20)
        self.song_box.pack(fill="both", expand=True)

        self.song_box.bind("<Double-Button-1>", lambda e: self.play_selected())

        ttk.Button(left, text="Remove Song", command=self.remove_song).pack(fill="x")

        # CENTER
        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True, padx=10)

        self.now = ttk.Label(center, text="None", font=("Arial", 14))
        self.now.pack()

        self.time_label = ttk.Label(center, text="00:00 / 00:00")
        self.time_label.pack()

        self.progress = ttk.Scale(center, from_=0, to=100, orient="horizontal")
        self.progress.pack(fill="x")
        self.progress.bind("<Button-1>", self.start_seek)
        self.progress.bind("<ButtonRelease-1>", self.end_seek)

        ttk.Label(center, text="Volume").pack()
        self.volume = ttk.Scale(center, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.volume.set(DEFAULT_VOLUME)
        self.volume.pack(fill="x")

        self.queue_box = tk.Listbox(center)
        self.queue_box.pack(fill="both", expand=True)

        # RIGHT
        right = ttk.Frame(main)
        right.pack(side="left", fill="y")

        ttk.Button(right, text="Play", command=self.play_selected).pack(fill="x")
        ttk.Button(right, text="Pause", command=self.player.pause).pack(fill="x")
        ttk.Button(right, text="Next", command=self.next_song).pack(fill="x")

        ttk.Button(right, text="Queue", command=self.add_queue).pack(fill="x")
        ttk.Button(right, text="Clear Queue", command=self.clear_queue).pack(fill="x")

    # ---------------- PLAY ----------------
    def play_selected(self):
        try:
            i = self.song_box.curselection()[0]
            song = self.filtered[i]
            self.player.play(song)
            self.now.config(text=os.path.basename(song))
        except:
            pass

    def next_song(self):
        if self.queue:
            song = self.queue.pop(0)
            self.player.play(song)
            self.refresh_queue()

    # ---------------- SEEK ----------------
    def start_seek(self, e):
        self.is_seeking = True

    def end_seek(self, e):
        self.is_seeking = False
        length = self.player.get_length()
        if length > 0:
            self.player.set_time(int(length * self.progress.get() / 100))

    # ---------------- VOLUME ----------------
    def set_volume(self, v):
        self.player.set_volume(v)

    # ---------------- SONGS ----------------
    def remove_song(self):
        try:
            i = self.song_box.curselection()[0]
            self.pm.playlists[self.pm.current_playlist].pop(i)
            self.pm.save()
            self.refresh_songs()
        except:
            pass

    # ---------------- QUEUE ----------------
    def add_queue(self):
        try:
            i = self.song_box.curselection()[0]
            self.queue.append(self.filtered[i])
            self.refresh_queue()
        except:
            pass

    def clear_queue(self):
        self.queue = []
        self.refresh_queue()

    def refresh_queue(self):
        self.queue_box.delete(0, tk.END)
        for q in self.queue:
            self.queue_box.insert(tk.END, os.path.basename(q))

    # ---------------- PLAYLISTS ----------------
    def add_playlist(self):
        name = simpledialog.askstring("Playlist", "Name:")
        if name:
            self.pm.add_playlist(name)
            self.refresh_all()

    def remove_playlist(self):
        try:
            i = self.playlist_box.curselection()[0]
            name = list(self.pm.playlists.keys())[i]
            self.pm.remove_playlist(name)
            self.refresh_all()
        except:
            pass

    def change_playlist(self, e=None):
        try:
            i = self.playlist_box.curselection()[0]
            self.pm.current_playlist = list(self.pm.playlists.keys())[i]
            self.refresh_songs()
        except:
            pass

    def import_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        name = os.path.basename(folder)
        self.pm.playlists[name] = []

        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(AUDIO_EXTS):
                    src = os.path.join(root, f)
                    dest = os.path.join(SONG_DIR, f)
                    if not os.path.exists(dest):
                        shutil.copy2(src, dest)
                    self.pm.playlists[name].append(dest)

        self.pm.save()
        self.refresh_all()

    # ---------------- UI ----------------
    def refresh_all(self):
        self.playlist_box.delete(0, tk.END)
        for p in self.pm.playlists:
            self.playlist_box.insert(tk.END, p)
        self.refresh_songs()

    def update_search(self, *_):
        self.refresh_songs()

    def refresh_songs(self):
        self.song_box.delete(0, tk.END)

        playlist = self.pm.get_current()
        self.filtered = [
            s for s in playlist
            if self.search_var.get().lower() in os.path.basename(s).lower()
        ]

        for s in self.filtered:
            self.song_box.insert(tk.END, os.path.basename(s))

    # ---------------- LOOP ----------------
    def loop(self):
        try:
            if self.player.is_playing():
                length = self.player.get_length()
                current = self.player.get_time()

                if length > 0 and not self.is_seeking:
                    self.progress.set(current / length * 100)

                self.time_label.config(text=f"{format_time(current)} / {format_time(length)}")
        except:
            pass

        self.root.after(500, self.loop)


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = MusicPlayer(root)
    root.mainloop()
