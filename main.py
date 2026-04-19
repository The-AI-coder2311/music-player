import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import ttk
import vlc
from tkinterdnd2 import DND_FILES, TkinterDnD

# ---------------- INIT ----------------
APP_DIR = os.path.join(os.getcwd(), "MusicLibrary")
DATA_FILE = os.path.join(APP_DIR, "music_data.json")
SONG_DIR = os.path.join(APP_DIR, "songs")

os.makedirs(SONG_DIR, exist_ok=True)

AUDIO_EXTS = (".mp3", ".m4a", ".wav", ".aac", ".flac")

# ---------------- APP ----------------
class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Player Pro")
        self.root.geometry("1100x650")

        self.instance = vlc.Instance("--no-video", "--quiet")
        self.player = self.instance.media_player_new()

        self.playlists = {}
        self.current_playlist = None
        self.current_index = -1
        self.queue = []

        self.search_text = ""
        self.is_seeking = False

        self.load_data()

        if not self.playlists:
            self.playlists["Default"] = {}

        if self.current_playlist not in self.playlists:
            self.current_playlist = list(self.playlists.keys())[0]

        self.build_ui()
        self.refresh_ui()
        self.refresh_songs()
        self.poll_player()

    # ---------------- STORAGE ----------------
    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "playlists": self.playlists,
                "current_playlist": self.current_playlist
            }, f, indent=2)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
                self.playlists = data.get("playlists", {})
                self.current_playlist = data.get("current_playlist")

    # ---------------- UI ----------------
    def build_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # ================= LEFT =================
        left = ttk.Frame(main)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Playlists").pack(anchor="w")

        self.playlist_box = tk.Listbox(left, height=8)
        self.playlist_box.pack(fill="x")
        self.playlist_box.bind("<<ListboxSelect>>", lambda e: self.change_playlist())

        ttk.Button(left, text="Add Playlist", command=self.add_playlist).pack(fill="x")
        ttk.Button(left, text="Remove Playlist", command=self.remove_playlist).pack(fill="x")
        ttk.Button(left, text="Import Folder", command=self.import_folder).pack(fill="x")

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Label(left, text="Songs").pack(anchor="w")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_search)

        ttk.Entry(left, textvariable=self.search_var).pack(fill="x", pady=5)

        self.song_box = tk.Listbox(left, height=18)
        self.song_box.pack(fill="both", expand=True)

        self.song_box.bind("<Double-Button-1>", lambda e: self.play_song())
        self.song_box.bind("<Button-1>", self.drag_start)
        self.song_box.bind("<B1-Motion>", self.drag_motion)
        self.song_box.bind("<Button-3>", self.show_song_menu)

        self.song_box.drop_target_register(DND_FILES)
        self.song_box.dnd_bind("<<Drop>>", self.drop_files)

        ttk.Button(left, text="Remove Song", command=self.remove_song).pack(fill="x", pady=5)

        # ================= CENTER =================
        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True, padx=10)

        ttk.Label(center, text="Now Playing").pack(anchor="w")

        self.now_label = ttk.Label(center, text="None", font=("Arial", 14))
        self.now_label.pack(pady=10)

        # --- PROGRESS ---
        self.time_label = ttk.Label(center, text="00:00 / 00:00")
        self.time_label.pack()

        self.progress = ttk.Scale(center, from_=0, to=100, orient="horizontal")
        self.progress.pack(fill="x", pady=10)

        self.progress.bind("<Button-1>", self.start_seek)
        self.progress.bind("<ButtonRelease-1>", self.end_seek)

        # --- VOLUME ---
        ttk.Label(center, text="Volume").pack(anchor="w")

        self.volume = ttk.Scale(center, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.volume.set(80)
        self.volume.pack(fill="x")

        ttk.Label(center, text="Queue").pack(anchor="w")

        self.queue_box = tk.Listbox(center)
        self.queue_box.pack(fill="both", expand=True)

        # ================= RIGHT =================
        right = ttk.Frame(main)
        right.pack(side="left", fill="y")

        ttk.Button(right, text="Play", command=self.play_song).pack(fill="x", pady=2)
        ttk.Button(right, text="Pause", command=self.pause_song).pack(fill="x", pady=2)
        ttk.Button(right, text="Next", command=self.next_song).pack(fill="x", pady=2)

        ttk.Separator(right).pack(fill="x", pady=5)

        ttk.Button(right, text="Add to Queue", command=self.add_to_queue).pack(fill="x", pady=2)
        ttk.Button(right, text="Clear Queue", command=self.clear_queue).pack(fill="x", pady=2)

    # ---------------- RIGHT CLICK MENU ----------------
    def show_song_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Play", command=self.play_song)
        menu.add_command(label="Add to Queue", command=self.add_to_queue)
        menu.add_command(label="Remove Song", command=self.remove_song)

        try:
            self.song_box.selection_clear(0, tk.END)
            self.song_box.selection_set(self.song_box.nearest(event.y))
            self.song_box.activate(self.song_box.nearest(event.y))
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ---------------- SEARCH ----------------
    def update_search(self, *_):
        self.search_text = self.search_var.get().lower()
        self.refresh_songs()

    # ---------------- PLAYLISTS ----------------
    def add_playlist(self):
        name = simpledialog.askstring("Playlist", "Name:")
        if name:
            self.playlists[name] = []
            self.current_playlist = name
            self.save_data()
            self.refresh_ui()

    def remove_playlist(self):
        try:
            i = self.playlist_box.curselection()[0]
            name = list(self.playlists.keys())[i]

            if len(self.playlists) <= 1:
                return

            del self.playlists[name]

            if self.current_playlist == name:
                self.current_playlist = list(self.playlists.keys())[0]

            self.save_data()
            self.refresh_ui()
            self.refresh_songs()
        except:
            pass

    def change_playlist(self):
        try:
            i = self.playlist_box.curselection()[0]
            self.current_playlist = list(self.playlists.keys())[i]
            self.refresh_songs()
        except:
            pass

    def import_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        name = os.path.basename(folder)
        self.playlists[name] = []

        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(AUDIO_EXTS):
                    src = os.path.join(root, f)
                    dest = os.path.join(SONG_DIR, f)

                    if not os.path.exists(dest):
                        shutil.copy2(src, dest)

                    self.playlists[name].append(dest)

        self.current_playlist = name
        self.save_data()
        self.refresh_ui()
        self.refresh_songs()

    # ---------------- SONGS ----------------
    def add_songs(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio", "*.mp3 *.wav *.m4a")])

        for f in files:
            dest = os.path.join(SONG_DIR, os.path.basename(f))
            if not os.path.exists(dest):
                shutil.copy2(f, dest)

            self.playlists[self.current_playlist].append(dest)

        self.save_data()
        self.refresh_songs()

    def remove_song(self):
        try:
            i = self.song_box.curselection()[0]
            self.playlists[self.current_playlist].pop(i)
            self.refresh_songs()
        except:
            pass

    # ---------------- PLAYBACK ----------------
    def play_song(self):
        try:
            i = self.song_box.curselection()[0]
            song = self.filtered_list[i]

            self.player.stop()
            media = self.instance.media_new(song)
            self.player.set_media(media)
            self.player.play()

            self.now_label.config(text=os.path.basename(song))
        except:
            pass

    def pause_song(self):
        self.player.pause()

    def next_song(self):
        self.queue_box.delete(0, tk.END)

    # ---------------- QUEUE ----------------
    def add_to_queue(self):
        try:
            i = self.song_box.curselection()[0]
            song = self.filtered_list[i]
            self.queue.append(song)
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

    # ---------------- SEEK + VOLUME ----------------
    def start_seek(self, e):
        self.is_seeking = True

    def end_seek(self, e):
        self.is_seeking = False
        try:
            val = self.progress.get()
            length = self.player.get_length()
            if length > 0:
                self.player.set_time(int(length * val / 100))
        except:
            pass

    def set_volume(self, val):
        try:
            self.player.audio_set_volume(int(float(val)))
        except:
            pass

    # ---------------- DRAG REORDER ----------------
    def drag_start(self, e):
        self.drag_index = self.song_box.nearest(e.y)

    def drag_motion(self, e):
        new = self.song_box.nearest(e.y)
        playlist = self.playlists[self.current_playlist]

        if 0 <= self.drag_index < len(playlist) and 0 <= new < len(playlist):
            item = playlist.pop(self.drag_index)
            playlist.insert(new, item)
            self.drag_index = new
            self.refresh_songs()

    # ---------------- DROP ----------------
    def drop_files(self, e):
        files = self.root.tk.splitlist(e.data)

        for f in files:
            if f.lower().endswith(AUDIO_EXTS):
                dest = os.path.join(SONG_DIR, os.path.basename(f))
                if not os.path.exists(dest):
                    shutil.copy2(f, dest)
                self.playlists[self.current_playlist].append(dest)

        self.save_data()
        self.refresh_songs()

    # ---------------- UI REFRESH ----------------
    def refresh_ui(self):
        self.playlist_box.delete(0, tk.END)
        for p in self.playlists:
            self.playlist_box.insert(tk.END, p)

    def refresh_songs(self):
        self.song_box.delete(0, tk.END)

        playlist = self.playlists[self.current_playlist]

        self.filtered_list = [
            s for s in playlist
            if self.search_text in os.path.basename(s).lower()
        ]

        for s in self.filtered_list:
            self.song_box.insert(tk.END, os.path.basename(s))

    # ---------------- LOOP ----------------
    def poll_player(self):
        try:
            if self.player.is_playing():
                length = self.player.get_length()
                current = self.player.get_time()

                if length > 0 and not self.is_seeking:
                    self.progress.set(current / length * 100)

                self.time_label.config(
                    text=f"{self.format_time(current)} / {self.format_time(length)}"
                )
        except:
            pass

        self.root.after(500, self.poll_player)

    def format_time(self, ms):
        s = int(ms / 1000)
        return f"{s//60:02}:{s%60:02}"

# ---------------- RUN ----------------
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = MusicPlayer(root)
    root.mainloop()
