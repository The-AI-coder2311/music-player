import vlc

class PlayerEngine:
    def __init__(self):
        self.instance = vlc.Instance("--no-video", "--quiet")
        self.player = self.instance.media_player_new()

    def play(self, path):
        self.player.stop()
        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def set_volume(self, vol):
        self.player.audio_set_volume(int(vol))

    def get_time(self):
        return self.player.get_time()

    def get_length(self):
        return self.player.get_length()

    def set_time(self, t):
        self.player.set_time(int(t))

    def is_playing(self):
        return self.player.is_playing()
