import wave
from bottle import Bottle
from huckleberry import Huckleberry


class BottledHuckleberry(Bottle):

    def __init__(self):
        super(BottledHuckleberry, self).__init__()
        self.huckleberry = None
        self.route_endpoints()

    def route_endpoints(self):
        self.route('/start', callback=self.start)
        self.route('/stop', callback=self.stop)
        self.route('/restart', callback=self.restart)
        self.route('/status', callback=self.status)
        self.route('/activate', callback=self.activate)
        self.route('/wav', callback=self.load_wav)

    def start(self):
        if not self.huckleberry:
            self.huckleberry = Huckleberry('config.yml')
            self.huckleberry.start()
            return 'started'

    def stop(self):
        if self.huckleberry:
            self.huckleberry.stop()
            return 'stopped'

    def restart(self):
        if self.huckleberry:
            self.huckleberry.stop()
            self.huckleberry = Huckleberry('config.yml')
            self.huckleberry.start()
            return 'restarted'

    def status(self):
        if self.huckleberry:
            return self.huckleberry.status()

    def activate(self):
        if self.huckleberry:
            self.huckleberry.activate_hound()

    def load_wav(self):
        if not self.huckleberry:
            return 'not started'

        audio = wave.open("time.wav")
        if audio.getsampwidth() != 2:
            return "wrong sample width (must be 16-bit)"
        if audio.getframerate() != self.huckleberry.sample_rate:
            return "unsupported sampling frequency (must be either 8 or 16 khz)"
        if audio.getnchannels() != 1:
            return "must be single channel (mono)"

        BUFFER_SIZE = self.huckleberry.encoding * self.huckleberry.frame_duration
        self.huckleberry.pause_input()
        self.huckleberry.clear_buffer()
        while True:
            samples = audio.readframes(BUFFER_SIZE)
            if len(samples) == 0:
                break
            self.huckleberry.load_buffer(samples)
        self.huckleberry.resume_input()
        return "loaded"

if __name__ == "__main__":
    oli = BottledHuckleberry()
    oli.run(host='localhost', port=8080)
