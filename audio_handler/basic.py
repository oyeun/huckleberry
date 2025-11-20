import pyaudio
import threading
import time
from collections import deque
from audio_handler.stream import Stream


# free for all audio playback
class Basic(object):

    def __init__(self, pyaudio, config):
        self.p = pyaudio
        self.streams = deque()
        self.done = False

        with open('../sounds/hound_start.wav', 'rb') as file:
            self.opensound = file.read()

        self.gc_thread = threading.Thread(target=self.__gc, args=(1.0,))
        self.gc_thread.start()

    def __gc(self, interval):
        while not self.done:
            if len(self.streams) > 0:
                stream = self.streams
                if not stream.is_active():
                    stream.close()
                    del stream
                else:
                    self.streams.append(stream)
            time.sleep(interval)

    def stop_all(self):
        while len(self.streams) > 0:
            stream = self.streams.pop()
            stream.close()
            del stream

    def play_open_sound(self):
        self.streams.append(Stream(self.p, self.opensound))

    def play_file(self, file):
        self.streams.append(Stream(self.p, file))

    def close(self):
        self.done = True
        self.gc_thread.join()
        self.stop_all()

if __name__ == '__main__':
    p = pyaudio.PyAudio()
    basic = Basic(p, 'config')
    basic.play_open_sound()
    time.sleep(0.1)
    basic.play_open_sound()
    #time.sleep(0.1)
    #basic.play_open_sound()
    #time.sleep(0.1)
    #basic.play_open_sound()
    time.sleep(5.0)
    basic.close()
    p.terminate()
    print(len(basic.streams))