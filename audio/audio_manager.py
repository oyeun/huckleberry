import pyaudio
from audio.audio_stream import AudioStream


class AudioManager(object):
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.alert_stream = None
        self.voice_stream = None

    def play_alert(self, sound):
        self.stop_alert()
        self.alert_stream = AudioStream(self.p, sound)

    def play_voice(self, voice_audio):
        self.stop_voice()
        self.voice_stream = AudioStream(self.p, voice_audio)

    def stop_alert(self):
        if self.alert_stream and self.alert_stream.is_active():
            self.alert_stream.close()

    def stop_voice(self):
        if self.voice_stream and self.alert_stream.is_active():
            self.voice_stream.close()

    def close(self):
        self.p.terminate()
