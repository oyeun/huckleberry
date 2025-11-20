import numpy
import pyaudio
import wave
from io import BytesIO


# TODO parameters:
#   number of times to play (-1 infinite, default 1),
#   pause in between repeats (ms, default 1000),
#   delay start (ms, default 0, use time.sleep?)
#   pass in default mute volume - make better name for mute (its not mute)
class Stream(object):
    def __init__(self, pa, source, key=None, default_volume=100):
        self.done = False
        # add input validation
        self.default_volume = float(default_volume / 100)
        self.volume = self.default_volume
        if isinstance(source, bytes):
            self.b = BytesIO(source)
            self.wf = wave.open(self.b, 'rb')
        else:
            self.wf = wave.open(source, 'rb')
        self.stream = pa.open(format=pyaudio.get_format_from_width(self.wf.getsampwidth()),
                              channels=self.wf.getnchannels(),
                              rate=self.wf.getframerate(),
                              output=True,
                              stream_callback=self.callback)
        self.stream.start_stream()

    def callback(self, in_data, frame_count, time_info, status):
        if self.done:
            return None, pyaudio.paComplete
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
        return (data, pyaudio.paContinue)

    def is_active(self):
        #return self.stream.is_active()
        return not self.done

    def set_volume(self, volume):
        # add input validation
        self.volume = volume / 100

    def reset_volume(self):
        self.volume = self.default_volume

    def stop(self):
        self.done = True
        pass

    def pause(self):
        self.stream.stop_stream()

    def resume(self):
        self.stream.start_stream()
        pass

    def close(self):
        self.done = True
        self.stream.stop_stream()
        self.stream.close()
        if hasattr(self, 'b'):
            self.b.close()
        self.wf.close()
