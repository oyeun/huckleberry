import wave
import yaml
from io import BytesIO
from bottle import Bottle, request, response
import logging
import logging.config
from huckleberry import Huckleberry
from config import HuckleberryConfig


class BottledHuckleberry(Bottle):

  def __init__(self):
    super().__init__()

    # initialize logging
    with open('logging.yml', 'r') as f:
      log_config = yaml.safe_load(f)
      logging.config.dictConfig(log_config)
    self.logger = logging.getLogger(__name__)

    # read config file
    with open('config.yml', 'r') as f:
      try:
        huckleberry_config = yaml.safe_load(f)
      except yaml.YAMLError as exc:
        self.logger.error(exc)
        return

    self.huckleberry = Huckleberry(HuckleberryConfig(**huckleberry_config))
    self.route_endpoints()

  def route_endpoints(self):
    self.route('/start', callback=self.start)
    self.route('/stop', callback=self.stop)
    self.route('/status', callback=self.status)
    self.route('/activate', callback=self.activate)
    self.route('/wav', 'POST', self.load_wav)
    self.route('/text', 'POST', self.text)

  def start(self):
    if not self.huckleberry.is_running:
      self.huckleberry.start()
      return 'started'
    else:
      return 'already started'

  def stop(self):
    if self.huckleberry.is_running:
      self.huckleberry.stop()
      return 'stopped'
    else:
      return 'already stopped'

  def status(self):
    if self.huckleberry:
      return self.huckleberry.status()
    else:
      return 'not started'

  def activate(self):
    if self.huckleberry:
      self.huckleberry.activate_hound()

  # feeds a pre-recorded audio file (wav format) with voice into huckleberry
  # ex: curl -X POST --data-binary @time.wav localhost:8080/wav
  def load_wav(self):
    input_wav = BytesIO(request.body.read())

    if not self.huckleberry and not self.huckleberry.is_running:
      return 'not running'

    with wave.open(input_wav, 'rb') as audio:
      if audio.getsampwidth() != 2:
        response.status(400)
        return 'wrong sample width (must be 16-bit)'
      if audio.getframerate() != self.huckleberry.config.audio_sample_rate:
        response.status(400)
        return 'unsupported sampling frequency (must be either 8 or 16 khz)'
      if audio.getnchannels() != 1:
        response.status(400)
        return 'must be single channel (mono)'

      buffer_size = self.huckleberry.config.chunk_size
      self.huckleberry.pause_input()
      self.huckleberry.clear_buffer()
      while True:
        samples = audio.readframes(buffer_size)
        if len(samples) == 0:
          break
        self.huckleberry.load_buffer(samples)
      self.huckleberry.resume_input()
    return 'loaded'

  def text(self):
    query = request.forms.get('query')
    self.huckleberry.text_hound(query)
    return 'sent'

if __name__ == '__main__':
  bh = BottledHuckleberry()
  bh.run(host='localhost', port=8080)
