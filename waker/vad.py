from config import VadConfig
from _webrtcvad import Error
import webrtcvad


class Vad(object):
  def __init__(self, config: VadConfig):
    self.sample_rate = config.audio_sample_rate
    self.vad = webrtcvad.Vad()
    self.vad.set_mode(config.sensitivity)

  def listen(self, buf):
    try:
      return self.vad.is_speech(buf, self.sample_rate)
    except Error:
      return False
