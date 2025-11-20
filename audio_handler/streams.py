import pyaudio
import threading
import time
from audio_handler.stream import Stream


def is_active(stream):
    if stream:
        return stream.is_active()
    else:
        return False


class Streams(object):

    def __init__(self, pyaudio):
        self.p = pyaudio
        self.done = False

        self.alert_stream = None
        self.voice_stream = None
        self.music_stream = None
        self.delayed_unmute_music_timer = None

        # TODO define default volume and pass into Stream
        self.mute_volume = 50 # TODO change this to a % and calculate mute volume 0-100

        with open('sounds/hound_start.wav', 'rb') as file:
            self.opensound = file.read()

        with open('sounds/hound_stop.wav', 'rb') as file:
            self.closesound = file.read()

        self.gc_thread = threading.Thread(target=self.__gc, args=(1.0,))
        self.gc_thread.start()

    def __gc(self, interval):
        while not self.done:
            if self.alert_stream and not is_active(self.alert_stream):
                self.alert_stream.close()
                self.alert_stream = None
            if self.voice_stream and not is_active(self.voice_stream):
                self.voice_stream.close()
                self.voice_stream = None
                if is_active(self.music_stream):
                    self.music_stream.reset_volume()
            if self.music_stream and not is_active(self.music_stream):
                self.music_stream.close()
                self.music_stream = None
            time.sleep(interval)

    def play_open_sound(self):
        if not is_active(self.alert_stream):
            self.alert_stream = Stream(self.p, self.opensound)

    def play_close_sound(self):
        if not is_active(self.alert_stream):
            self.alert_stream = Stream(self.p, self.closesound)

    def play_alert(self):
        pass

    def signal_hound_start(self):
        # quiet music for voice input
        if is_active(self.music_stream):
            self.music_stream.set_volume(self.mute_volume)
        # stop voice for voice input
        if is_active(self.voice_stream):
            self.voice_stream.close()
        # play hound_start?

    def signal_hound_stop(self):
        # unqiet music after voice input, unless voice output stream is active
        if self.delayed_unmute_music_timer:
            if self.delayed_unmute_music_timer.is_alive():
                # do nothing
                pass
            else:
                self.delayed_unmute_music_timer.join()
                self.delayed_unmute_music_timer = threading.Timer(1, self.delay)
                self.delayed_unmute_music_timer.start()
        else:
            self.delayed_unmute_music_timer = threading.Timer(1, self.delay)
            self.delayed_unmute_music_timer.start()

    def delay(self):
        if not is_active(self.voice_stream):
            self.music_stream.reset_volume()

    def play_music(self, filepath):
        if is_active(self.music_stream):
            self.music_stream.close()
        self.music_stream = Stream(self.p, filepath)

    def play_voice(self, voice_audio):
        # mute music
        if is_active(self.music_stream):
            self.music_stream.set_volume(self.mute_volume)
        # stop existing voice
        if is_active(self.voice_stream):
            self.voice_stream.close()
        # play voice
        self.voice_stream = Stream(self.p, voice_audio)
        # after voice stopped, unmute music
        # this is done by __gc thread

    def close(self):
        self.done = True
        self.gc_thread.join()
        #self.stop_all()

if __name__ == '__main__':
    p = pyaudio.PyAudio()
    basic = Streams(p)
    basic.play_open_sound()
    time.sleep(5.0)
    basic.close()
    p.terminate()