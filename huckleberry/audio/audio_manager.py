import pyaudio
from ..audio import AudioStream


class AudioManager(object):
    def __init__(self, output_device_index, frames_per_buffer):
        self.p = pyaudio.PyAudio()
        self.output_device_index = output_device_index
        self.frames_per_buffer = frames_per_buffer
        self.alert_stream = None
        self.voice_stream = None

    def play_alert(self, sound):
        self.stop_alert()
        self.alert_stream = AudioStream(self.p, sound, output_device_index=self.output_device_index, frames_per_buffer=self.frames_per_buffer)

    def play_voice(self, voice_audio, block=False):
        self.stop_voice()
        self.voice_stream = AudioStream(self.p, voice_audio, block=block, output_device_index=self.output_device_index, frames_per_buffer=self.frames_per_buffer)

    def stop_alert(self):
        if self.alert_stream and self.alert_stream.is_active():
            self.alert_stream.close()

    def stop_voice(self):
        if self.voice_stream and self.alert_stream.is_active():
            self.voice_stream.close()

    def close(self):
        self.p.terminate()
