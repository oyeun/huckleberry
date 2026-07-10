import base64
import logging
from pixel_ring import pixel_ring
from gpiozero import LED
from huckleberry.audio import AudioManager
from huckleberry.config import HoundifyHandlerConfig


# a copy of the default HoundifyHandler, with LED light management for my Raspberry Pi / Speaker Hat
class OyPiHandler(object):
  def __init__(self, config: HoundifyHandlerConfig):
    self.logger = logging.getLogger(__name__)
    self.power = LED(5)
    self.power.on()
    pixel_ring.set_brightness(10)
    pixel_ring.show([0, 53, 30, 70] * 12)
    self.audio_manager = AudioManager(output_device_index=config.output_device_index, frames_per_buffer=config.frames_per_buffer)
    self.ignore_bad_request = config.ignore_bad_request
    self.blocking_voice = config.blocking_voice
    if config.start_sound:
      with open(config.start_sound, 'rb') as file:
        self.activate_sound = file.read()
    if config.stop_sound:
      with open(config.stop_sound, 'rb') as file:
        self.deactivate_sound = file.read()

  def on_activate(self):
    self.logger.debug('hound activated')
    pixel_ring.show([0, 83, 60, 100] * 12)
    self.audio_manager.stop_voice()
    if self.activate_sound:
      self.audio_manager.play_alert(self.activate_sound)

  def on_deactivate(self):
    self.logger.debug('hound deactivated')
    pixel_ring.show([0, 53, 30, 70] * 12)
    if self.deactivate_sound:
      self.audio_manager.play_alert(self.deactivate_sound)

  def on_response(self, response):
    if 'AllResults' in response:
      if response['AllResults'][0]['CommandKind'] == 'NoResultCommand' and self.ignore_bad_request:
        self.logger.debug('no result, ignoring no result audio response')
      elif 'ResponseAudioBytes' in response['AllResults'][0]:
        self.audio_manager.play_voice(base64.b64decode(response['AllResults'][0]['ResponseAudioBytes']), block=self.blocking_voice)
      self.logger.debug(response['Disambiguation']['ChoiceData'][0]['Transcription'])
      self.logger.debug(response['AllResults'][0]['WrittenResponse'])

  def close(self):
    pixel_ring.off()
    self.audio_manager.close()
