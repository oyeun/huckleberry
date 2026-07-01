import base64
import logging
from audio.audio_manager import AudioManager
from config import HoundConfig


class HoundifyHandler(object):

  def __init__(self, config: HoundConfig):
    self.logger = logging.getLogger(__name__)
    self.audio_manager = AudioManager()
    self.ignore_bad_request = config.ignore_bad_request
    with open(config.start_sound, 'rb') as file:
      self.activate_sound = file.read()
    with open(config.stop_sound, 'rb') as file:
      self.deactivate_sound = file.read()

  def on_activate(self):
    self.logger.debug('hound activated')
    self.audio_manager.stop_voice()
    self.audio_manager.play_alert(self.activate_sound)

  def on_deactivate(self):
    self.logger.debug('hound deactivated')
    self.audio_manager.play_alert(self.deactivate_sound)

  def on_response(self, response):
    if 'AllResults' in response:
      if response['AllResults'][0]['CommandKind'] == 'NoResultCommand' and self.ignore_bad_request:
        self.logger.debug('no result, ignoring no result audio response')
      elif 'ResponseAudioBytes' in response['AllResults'][0]:
        self.audio_manager.play_voice(base64.b64decode(response['AllResults'][0]['ResponseAudioBytes']))
      self.logger.debug(response['Disambiguation']['ChoiceData'][0]['Transcription'])
      self.logger.debug(response['AllResults'][0]['WrittenResponse'])

  def close(self):
    self.audio_manager.close()
