from collections import deque
import pyaudio
import threading
import time
import wave
import yaml
from scutils.log_factory import LogFactory

import hound
import response_processor
import vad
import waker
import hound_waker

from myque import Myque


class Huckleberry(object):

    def __init__(self, config_path):
        # initialize logging
        with open('logging.yml', 'r') as stream:
            try:
                logging_config = yaml.full_load(stream)
                self.logger = LogFactory.get_instance(**logging_config)
            except yaml.YAMLError as exc:
                self.logger = LogFactory.get_instance(stdout=True)
                self.logger.error('unable to load logging.yml config, using default stdout logger')

        # read config file
        self.config = None
        with open(config_path, 'r') as stream:
            try:
                self.config = yaml.full_load(stream)
            except yaml.YAMLError as exc:
                self.logger.error(exc)
                return

        # states
        self.done = False
        self.skip_activation = False
        self.buffer_paused = False

        self.frame_buffer_thread = None
        self.listener_thread = None
        self.pyaudio = None
        self.stream = None

        # audio config
        self.channels = 1 # mono, fixed
        self.encoding = 16 # 16-bit, fixed
        self.sample_rate = self.config['audio']['sample_rate'] # kHz
        self.frame_duration = self.config['audio']['frame_duration'] # ms
        self.chunk_size = self.encoding * self.frame_duration

        # misc configs
        self.activation_method = self.config['activation_method'].lower()
        if self.activation_method not in ['wakeword', 'vad', 'method']:
            raise Exception('invalid config: activation_method. must be [wakeword, vad, method]')
        self.activate_on_wakeword = self.activation_method == 'wakeword'
        self.activate_on_vad = self.activation_method == 'vad'
        self.activate_on_method = self.activation_method == 'method'

        if self.activate_on_wakeword:
            self.vad_after_ww = self.config['vad_after_wakeword']
            self.vad_after_ww_time = self.config['vad_after_wakeword_time']

        self.start_sound = self.config['start_sound']
        self.stop_sound = self.config['stop_sound']

        frame_buffer_max_size = int(self.config['frame_buffer_size'] / self.frame_duration)
        self.frame_buffer = Myque(maxsize=frame_buffer_max_size)

        # initialize houndify
        self.hound = hound.Hound(self.config)

        # initialize VAD
        self.vad = vad.Vad(self.config)

        # initialize waker
        wakeword = self.config['wakeword'].lower()
        if wakeword in ['ok hound', 'okay hound']:
            self.waker = hound_waker.HoundWaker(self.config)
        else:
            self.waker = waker.Waker(self.config)

        # initialize processor
        self.processor = response_processor.ResponseProcessor(self.config)

    def start(self):
        self.logger.info('starting huckleberry')
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(format=pyaudio.paInt16,
                                        channels=self.channels,
                                        rate=self.sample_rate,
                                        input=True,
                                        frames_per_buffer=self.chunk_size)
        if not self.frame_buffer_thread:
            self.frame_buffer_thread = threading.Thread(target=self.__frame_buffer)
            self.frame_buffer_thread.start()
        if not self.listener_thread:
            self.listener_thread = threading.Thread(target=self.__listener)
            self.listener_thread.start()
        else:
            error_msg = 'unable to start huckleberry, it is already running'
            self.logger.error(error_msg)
            raise Exception(error_msg)
        self.logger.info('started huckleberry')

    def stop(self):
        self.logger.info('stopping huckleberry')
        self.done = True
        if self.frame_buffer_thread:
            self.frame_buffer_thread.join()
        if self.listener_thread:
            self.listener_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()
        self.logger.info('stopped huckleberry, goodbye!')

    def __frame_buffer(self):
        self.stream.start_stream()
        while not self.done:
            if not self.buffer_paused:
                frame = self.stream.read(self.chunk_size, False)
                self.frame_buffer.append(frame)
        self.stream.stop_stream()
        self.stream.close()

    def pause_input(self):
        self.buffer_paused = True

    def resume_input(self):
        self.buffer_paused = False

    def clear_buffer(self):
        self.frame_buffer.clear()

    def load_buffer(self, frames):
        self.frame_buffer.append(frames)

    def __listener(self):
        while not self.done:
            self.logger.debug('starting new listener loop')
            self.skip_activation = False
            self.frame_buffer.clear()
            if not self.done:
                if self.activate_on_wakeword:
                    self.__kwd_loop()
                    self.play_audio(self.start_sound)
                    if self.vad_after_ww and not self.skip_activation:
                        detected = self.__vad_loop(timeout=self.vad_after_ww_time)
                        if not detected:
                            self.play_audio(self.stop_sound)
                            continue
                elif self.activate_on_vad:
                    self.__vad_loop()
                    self.play_audio(self.start_sound)
                elif self.activate_on_method:
                    while not self.done and not self.skip_activation:
                        pass
                    self.play_audio(self.start_sound)
                else:
                    self.logger.error('not supposed to reach here...')
                    self.done = True
            if not self.done:
                response = self.__hound()
                self.play_audio(self.stop_sound)
                self.processor.process(response)

    def __kwd_loop(self):
        self.logger.debug('wakephrase detection phase')
        keyword_detected = False
        self.waker.start()
        while not keyword_detected and not self.done and not self.skip_activation:
            frame = self.frame_buffer.popleft()
            if frame:
                keyword_detected = self.waker.listen(frame)
        if keyword_detected:
            self.frame_buffer.appendleft(frame)
            self.logger.debug('wakephrase detected')
        self.waker.finish()

    def __vad_loop(self, timeout=0):
        num_voice_frames = 0
        max_queue_size = int(self.config['vad']['window'] / self.frame_duration)
        vad_buffer = deque(maxlen=max_queue_size)
        vad_detected = False

        if timeout:
            self.num_iterations = timeout / self.frame_duration
        iteration = 0

        while not vad_detected and not self.done and not self.skip_activation:
            if len(vad_buffer) >= max_queue_size:
                # queue full
                if float(num_voice_frames) / float(max_queue_size) >= self.config['vad']['min_pass_ratio']:
                    # queue contains sufficient voice, end loop
                    vad_detected = True
                    break
                # dequeue
                old_frame = vad_buffer.popleft()
                if old_frame['vad']:
                    num_voice_frames -= 1
            # get frame
            frame = self.frame_buffer.popleft()
            if frame:
                if timeout:
                    iteration += 1
                    if iteration > self.num_iterations:
                        break
                # check if frame contains voice
                frame_has_voice = self.vad.listen(frame)
                if frame_has_voice:
                    num_voice_frames += 1
                # append to queue
                vad_buffer.append({'vad': frame_has_voice, 'frame': frame})

        if vad_detected:
            #frames = [d['frame'] for d in vad_buffer]
            frames = [d['frame'] for d in reversed(vad_buffer)]
            self.frame_buffer.extendleft(frames)
        return vad_detected

    def __hound(self):
        hound_finished = False
        message = None
        self.hound.start()
        while not hound_finished and not self.done:
            frame = self.frame_buffer.popleft()
            if frame:
                hound_finished = self.hound.listen(frame)
                if message != self.hound.response()['message']:
                    message = self.hound.response()['message']
                    print(message)
        self.hound.finish()
        return self.hound.response()

    def __play_audio(self, path):
        chunk = 1024
        f = wave.open(path, "rb")
        stream = self.pyaudio.open(format=self.pyaudio.get_format_from_width(f.getsampwidth()),
                                   channels=f.getnchannels(),
                                   rate=f.getframerate(),
                                   output=True)
        data = f.readframes(chunk)
        while data:
            stream.write(data)
            data = f.readframes(chunk)
        stream.stop_stream()
        stream.close()

    # activate hound, skipping wake phrase and vad
    def activate_hound(self):
        self.logger.debug('activate hound')
        if self.listener_thread:
            self.skip_activation = True
        else:
            self.logger.debug('not started, call start() first')

    def status(self):
        status = {
            'status': {
                'done': self.done,
                'frame buffer size': self.frame_buffer.size()
            }
        }
        self.logger.debug(status)
        return status

    def play_audio(self, path):
        if not self.done:
            self.listener_thread = threading.Thread(target=self.__play_audio(path))
            self.listener_thread.start()
            self.listener_thread.join()


if __name__ == '__main__':
    huckle = Huckleberry('config.yml')
    huckle.start()
    time.sleep(60)
    huckle.stop()