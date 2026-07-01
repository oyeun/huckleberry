from collections import deque
import math
import pyaudio
import threading
import time
import logging
from client import hound
from config import HuckleberryConfig, ActivationMethod
from handler import houndify_handler
from waker import hound_waker, vad, waker
from util.myque import Myque


class Huckleberry(object):
  def __init__(self, config: HuckleberryConfig):
    self.logger = logging.getLogger(__name__)
    self.config = config
    # states
    self.is_running = self.is_done = self.skip_to_activate = self.is_buffer_paused = False
    # audio processes
    self.frame_buffer_thread = self.listener_thread = self.pyaudio = self.stream = None

    # initialize frame buffer
    self.frame_buffer = Myque(maxsize=self.config.max_frames)
    # initialize houndify
    self.hound = hound.Hound(self.config.hound_config)
    # initialize VAD
    self.vad = vad.Vad(self.config.vad_config)
    # initialize waker
    if self.config.wakeword_config.wakeword.lower() in ['ok hound', 'okay hound']:
      self.waker = hound_waker.HoundWaker(self.config.hound_config)
    else:
      self.waker = waker.Waker(self.config.wakeword_config)
    # initialize response handler
    self.handler = houndify_handler.HoundifyHandler(self.config.hound_config)
    # activation method
    if self.config.activation_method == ActivationMethod.WAKEWORD.value:
      self.activation_loop = self.__kwd_loop
    elif self.config.activation_method == ActivationMethod.VAD.value:
      self.activation_loop = self.__vad_loop
    elif self.config.activation_method == ActivationMethod.METHOD.value:
      self.activation_loop = self.__conditional_loop
    else:
      raise ValueError('HuckleberryConfig.activation_method misconfigured')

  def start(self):
    if self.is_running:
      self.logger.info('unable to start huckleberry, it is already running')
      return
    self.logger.info('starting huckleberry')
    self.is_done = False
    self.pyaudio = pyaudio.PyAudio()
    self.stream = self.pyaudio.open(format=pyaudio.paInt16,
                                    channels=self.config.audio_channels,
                                    rate=self.config.audio_sample_rate,
                                    input=True,
                                    output=False,
                                    frames_per_buffer=self.config.chunk_size,
                                    input_device_index=self.config.input_device_index,
                                    stream_callback=self.callback)
    if not self.listener_thread:
      self.listener_thread = threading.Thread(target=self.__listener_loop)
      self.listener_thread.start()
    self.is_running = True
    self.logger.info('started huckleberry')

  def callback(self, in_data, frame_count, time_info, status):
    if self.is_done:
      self.logger.debug('ending stream callback')
      return None, pyaudio.paComplete
    if not self.is_buffer_paused:
      self.frame_buffer.append(in_data)
    return None, pyaudio.paContinue

  def stop(self):
    if not self.is_running:
      self.logger.info('unable to stop huckleberry, it is not running')
      return
    self.logger.info('stopping huckleberry')
    self.is_done = True
    if self.frame_buffer_thread:
      self.frame_buffer_thread.join()
    if self.listener_thread:
      self.listener_thread.join()
      self.listener_thread = None
    self.stream.stop_stream()
    self.stream.close()
    self.pyaudio.terminate()
    self.handler.close()
    self.is_running = False
    self.logger.info('stopped huckleberry')

  def __frame_buffer_loop(self):
    self.stream.start_stream()
    while not self.is_done:
      if not self.is_buffer_paused:
        frame = self.stream.read(self.config.chunk_size, False)
        self.frame_buffer.append(frame)
      else:
        time.sleep(0.1)
    self.stream.stop_stream()
    self.stream.close()

  def pause_input(self):
    self.is_buffer_paused = True

  def resume_input(self):
    self.is_buffer_paused = False

  def clear_buffer(self):
    self.frame_buffer.clear()

  def load_buffer(self, frames):
    self.frame_buffer.append(frames)

  def __kwd_loop(self):
    self.logger.debug('listening for wakephrase...')
    keyword_detected = False
    self.waker.start()
    while not keyword_detected and not self.is_done and not self.skip_to_activate:
      frame = self.frame_buffer.popleft()
      if frame:
       keyword_detected = self.waker.listen(frame)
    if keyword_detected:
      self.frame_buffer.appendleft(frame)
      self.logger.debug('wakephrase detected')
    self.waker.finish()

  def __conditional_loop(self):
    self.logger.debug('waiting for activation...')
    while not self.is_done and not self.skip_to_activate:
      time.sleep(0.1)
    self.logger.debug('activated')

  def __vad_loop(self, timeout=0):
    self.logger.debug('listening for voice activity...')
    max_queue_size = math.ceil(self.config.vad_config.window / self.config.frame_duration)
    vad_buffer = deque(maxlen=max_queue_size)
    vad_detected = False
    max_iterations = math.ceil(timeout / self.config.frame_duration)
    num_voice_frames = iteration = 0
    while not vad_detected and not self.is_done and not self.skip_to_activate:
      # when queue is full...
      if len(vad_buffer) >= max_queue_size:
        # ...break loop when voice activity is detected
        if float(num_voice_frames) / float(max_queue_size) >= self.config.vad_config.min_pass_ratio:
          vad_detected = True
          break
        # ...pop last frame from queue
        old_frame = vad_buffer.popleft()
        num_voice_frames -= old_frame['has_voice']
      # pop frame from buffer, check for voice and add to queue
      frame = self.frame_buffer.popleft()
      if frame:
        # break loop after timeout reached
        if timeout:
          iteration += 1
          if iteration > max_iterations:
            break
        frame_has_voice = self.vad.listen(frame)
        num_voice_frames += frame_has_voice
        vad_buffer.append({'has_voice': frame_has_voice, 'frame': frame})
    # post loop, return result
    if vad_detected:
      self.logger.debug('voice activity detected')
      frames = [d['frame'] for d in reversed(vad_buffer)]
      self.frame_buffer.extendleft(frames)
    return vad_detected

  def __hound_loop(self):
    self.logger.debug('sending to houndify...')
    hound_finished = False
    self.hound.start()
    while not hound_finished and not self.is_done:
      frame = self.frame_buffer.popleft()
      if frame:
        hound_finished = self.hound.listen(frame)
    self.hound.finish()
    self.logger.debug('houndify finished')
    return self.hound.get_response()

  def __listener_loop(self):
    while not self.is_done:
      self.logger.debug('starting new listener loop')
      self.skip_to_activate = False
      self.frame_buffer.clear()
      if not self.is_done:
        self.activation_loop()
        if not self.is_done:
          self.handler.on_activate()
          # secondary loop to cancel after no voice activity
          if self.config.activation_method == ActivationMethod.WAKEWORD.value and self.config.wakeword_config.timeout_after_wakeword > 0 and not self.skip_to_activate:
            detected = self.__vad_loop(timeout=self.config.wakeword_config.timeout_after_wakeword)
            if not detected:
              if not self.is_done:
                self.handler.on_deactivate()
              continue
          response = self.__hound_loop()
          if not self.is_done:
            self.handler.on_deactivate()
          self.handler.on_response(response)

  # activate hound, if WAKEWORD or VAD mode, will skip loops and start hound immediately
  def activate_hound(self):
    self.logger.debug('houndify manually activated')
    if self.is_running:
      self.skip_to_activate = True
    else:
      self.logger.debug('unable to activate, huckleberry os not running')

  def text_hound(self, query):
    self.logger.debug('sending text to textclient')
    response = self.hound.text(query)
    self.handler.on_response(response)

  def status(self):
    status = {
      'status': {
        'done': self.is_done,
        'running': self.is_running,
        'frameBufferSize': self.frame_buffer.size()
      }
    }
    self.logger.debug(status)
    return status
