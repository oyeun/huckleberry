import base64
import logging
from ..audio.audio_manager import AudioManager
from ..config import HoundifyHandlerConfig


class HoundifyHandler(object):
  """
  HoundifyHandler - example handler class

  Handler should implement on_activate(), on_deactivate(), on_response(), and close()

  on_activate() - what to do when Huckleberry is activated (user has spoken wakeword and activated Huckleberry)
  on_deactivate() - what to do when Huckleberry is deactivated (user has finished speaking)
  on_response() - what to do with the Houndify response, see (https://www.houndify.com/docs#server-response)
  close() - called when Huckleberry is stopped, clean up your active processes here
  """
  def __init__(self, config: HoundifyHandlerConfig):
    self.logger = logging.getLogger(__name__)
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
    self.audio_manager.stop_voice()
    if self.activate_sound:
      self.audio_manager.play_alert(self.activate_sound)

  def on_deactivate(self):
    self.logger.debug('hound deactivated')
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
    self.audio_manager.close()
