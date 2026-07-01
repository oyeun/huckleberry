import logging
from datetime import datetime
from houndify import houndify
from config import HoundConfig


class Hound(object):
  def __init__(self, config: HoundConfig):
    self.logger = logging.getLogger(__name__)
    self.client = houndify.StreamingHoundClient(
      config.client_id,
      config.client_key,
      config.user,
      sampleRate=config.audio_sample_rate,
      requestInfo=config.request_info,
      enableVAD=True)
    self.textclient = self.text_client = houndify.TextHoundClient(
      config.client_id,
      config.client_key,
      config.user,
      requestInfo=config.request_info
    )
    self.active = False
    self.finished = False
    self.listener = None
    self.logger.debug('Hound initialized')

  def start(self):
    if not self.active:
      self.logger.debug('starting hound')
      self.listener = MyListener()
      self.client.start(self.listener)
      self.active = True
      self.finished = False
    else:
      self.logger.debug('hound is already running')

  def listen(self, frame):
    if self.active and not self.finished:
      self.finished = self.client.fill(frame)
    return self.finished

  def finish(self, track_conversation=True):
    if self.active:
      self.logger.debug('stopping hound')
      self.active = False
      self.client.finish()
      if track_conversation:
        resp = self.listener.getState()['message']
        if resp and 'AllResults' in resp and 'ConversationState' in resp['AllResults'][0]:
          self.client.HoundRequestInfo['ConversationState'] = resp['AllResults'][0]['ConversationState']
    else:
      self.logger.debug('hound is already stopped')

  def reset_state(self):
    self.listener.resetState()

  def get_response(self):
    state = self.listener.getState()
    if state['status'] == 'final' and state['message']['Status'] == 'OK':
      return state['message']
    return None

  def get_state(self):
    return self.listener.getState()

  def update_request_info(self, request_info):
    self.client.HoundRequestInfo.update(request_info)

  def set_request_info(self, key, value):
    self.client.setHoundRequestInfo(key, value)

  def remove_request_info(self, key):
    self.client.setHoundRequestInfo(key)

  def text(self, query):
    response = self.textclient.query(query)
    return response


class MyListener(houndify.HoundListener): # refactor this, store all states in a more readable structure
  def __init__(self):
    self.logger = logging.getLogger(__name__)
    self.status = 'initialized'
    self.messages = {}
    self.messages['initialized'] = f'initialized {datetime.now()}'

  def resetState(self):
    self.status = 'initialized'
    self.messages = {}
    self.messages['initialized'] = f'initialized {datetime.now()}>'

  def onPartialTranscript(self, transcript): # keep each partial message in a list?
    if transcript:
      self.status = 'partial'
      self.messages['partial'] = transcript

  def onFinalResponse(self, response):
    self.status = 'final'
    self.messages['final'] = response

  def onError(self, err):
    self.status = 'error'
    self.messages['error'] = str(err)
    self.logger.error(str(err))

  def getState(self):
    return {
      'status': self.status,
      'message': self.messages[self.status]
    }
