import numpy
import pyaudio
import wave
from io import BytesIO


class AudioStream(object):
    def __init__(self, pa, source, key=None, volume=100):
        self.done = False
        self.volume = float(volume / 100)
        if isinstance(source, bytes):
            self.b = BytesIO(source)
            self.wf = wave.open(self.b, 'rb')
        else:
            self.wf = wave.open(source, 'rb')
        self.stream = pa.open(format=pyaudio.get_format_from_width(self.wf.getsampwidth()),
                              channels=self.wf.getnchannels(),
                              rate=self.wf.getframerate(),
                              input=False,
                              output=True,
                              output_device_index=1,
                              frames_per_buffer= 1024,
                              stream_callback=self.callback)

    def callback(self, in_data, frame_count, time_info, status):
        if self.done:
            if hasattr(self, 'b'):
                self.b.close()
            self.wf.close()
            return None, pyaudio.paAbort
        data = self.wf.readframes(frame_count)

        # volume adjust
        if self.volume != 1.0:
            data = numpy.fromstring(data, numpy.int16)
            data = data * self.volume
            data = data.astype(numpy.int16)

        remaining = self.wf.getnframes() - self.wf.tell()
        if remaining <= 0:
            self.done = True
            if hasattr(self, 'b'):
                self.b.close()
            self.wf.close()
            return None, pyaudio.paComplete
        return data, pyaudio.paContinue

    def is_active(self):
        return not self.done

    def set_volume(self, volume: int):
        self.volume = float(volume / 100)

    def reset_volume(self):
        self.volume = self.default_volume

    def stop(self):
        self.done = True

    def pause(self):
        self.stream.stop_stream()

    def resume(self):
        self.stream.start_stream()

    def close(self):
        self.done = True
        self.stream.stop_stream()
        self.stream.close()
        if hasattr(self, 'b'):
            self.b.close()
        self.wf.close()
