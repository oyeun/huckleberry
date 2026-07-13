from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ActivationMethod(Enum):
  WAKEWORD = 'wakeword'
  VAD = 'vad'
  METHOD = 'method'


@dataclass
class VadConfig:
  """
  Voice activity detection (VAD) configuration

  VAD constantly scans a window of audio for voice activity, and if sufficient voice is detected (min_pass_ratio) it will
  pass. VAD is used when activation method is set to VAD (to determine if the incoming audio is someone speaking) and also
  after Huckleberry has been activated (as a timeout to cancel input if no voice detected after activation), both using
  the same configuration values.

  audio_sample_rate (hz) - not configurable, it is configured and inherited from HuckleberryConfig
  sensitivity (0-3) - 0 is the least aggressive about filtering out non-speech, 3 is the most aggressive. For more info: https://pypi.org/project/webrtcvad/
  window (ms) - how many ms of audio are monitored for voice activity
  min_pass_ratio (float) - in the configured window timeframe, what is the ratio of voice to non-voice frames to pass VAD
  """
  audio_sample_rate: int = None
  sensitivity: int = 3
  window: int = 1000
  min_pass_ratio: float = 0.5


@dataclass
class WakewordConfig:
  """
  Wakeword configuration

  Wakeword is the phrase you want to speak to activate Huckleberry. Wakeword detection is done offline, no audio is sent
  to the cloud until the wakeword has been spoken and Huckleberry is activated. It is powered by the pocketsphinx library.

  wakeword (str) - Your desired wakeword, it can be multiple words ie 'Hey Huckleberry'
  timeout_after_wakeword (ms) - If wakeword is spoken, don't immediately send audio to Houndify. Instead, wait for voice
                                activity and if no activity is detected after the elapsed time, deactivate Huckleberry.
  kws_threshold, logfn, model_dir, model_hmm, model_dict - The remaining configurations are passthrough configurations
                                                           to pocketsphinx, and are for advanced use.
  """
  wakeword: str = 'computer'
  timeout_after_wakeword: int = 5000
  kws_threshold: float = 1e-5
  logfn: str = '/dev/null'
  model_dir: str = None
  model_hmm: str = None
  model_dict: str = None


@dataclass
class HoundConfig:
  """
  Houndify configuration

  See Houndify documentation for more information - https://www.houndify.com/docs
  """
  client_id: str
  client_key: str
  user: str
  audio_sample_rate: int = None
  request_info: dict = field(default_factory=dict)


# default response handler config
@dataclass
class HoundifyHandlerConfig:
  """
  Default Handler configuration

  start_sound (path to wav file) - Sound to signal when Huckleberry is activated
  stop_sound (path to wav file) - Sound to signal Huckleberry has been deactivated
  ignore_bad_request (bool) - When True, ignore the Houndify bad request audio response
  blocking_voice (bool) - When set to True, make the audio response blocking. Set this if you don't want the response to be interrupted by another activation
  output_device_index (int) - pyaudio config
  frames_per_buffer (int) - pyaudio config
  """
  start_sound: str = None
  stop_sound: str = None
  ignore_bad_request: bool = False
  blocking_voice: bool = False
  output_device_index: Optional[int] = None
  frames_per_buffer: Optional[int] = 1024


@dataclass
class HuckleberryConfig:
  """
  Huckleberry configuration - primary config for Huckleberry

  input_device_index (int) - pyaudio config
  activation_method (str) - How you want to activate Huckleberry:
                            'wakeword' - by saying a keyword
                            'vad' - by speaking
                            'method' - by method call (activate_hound())
  audio_sample_rate (hz, 8000|16000) - pyaudio config
  frame_duration (ms, 10|20|30)- pyaudio config
  frame_buffer_size (ms) - buffer containing the last x ms of input audio
  audio_channels (int, 1) - this value is fixed to 1 (mono)
  audio_encoding (bits, 16) - this value is fixed to 16 (bits)
  chunk_size - calculated value (audio_encoding * frame_duration = chunk_size)
  max_frames - max number of frames in buffer; calculated (frame_buffer_size // frame_duration = max_frames)
  vad_config - VAD component config
  wakeword_config - wakeword component config
  hound_config - hound component config
  houndify_handler_config - default handler component config
  """
  input_device_index: Optional[int] = None
  activation_method: ActivationMethod = ActivationMethod.WAKEWORD
  audio_sample_rate: int = 16000  # 8000|16000, kHz
  frame_duration: int = 30  # 10|20|30, ms
  frame_buffer_size: int = 3000  # ms
  audio_channels: int = field(default=1, init=False)  # fixed - mono
  audio_encoding: int = field(default=16, init=False)  # fixed - 16-bit
  chunk_size: int = field(init=False)
  max_frames: int = field(init=False)
  vad_config: VadConfig = field(default_factory=VadConfig)
  wakeword_config: WakewordConfig = field(default_factory=WakewordConfig)
  hound_config: HoundConfig = field(default_factory=HoundConfig)
  houndify_handler_config: HoundifyHandlerConfig = field(default_factory=HoundifyHandlerConfig)

  def __post_init__(self):
    self.chunk_size = self.audio_encoding * self.frame_duration
    self.max_frames = self.frame_buffer_size // self.frame_duration
    if isinstance(self.vad_config, dict):
      self.vad_config = VadConfig(**self.vad_config, audio_sample_rate= self.audio_sample_rate)
    else:
      self.vad_config.audio_sample_rate = self.audio_sample_rate
    if isinstance(self.wakeword_config, dict):
      self.wakeword_config = WakewordConfig(**self.wakeword_config)
    if isinstance(self.hound_config, dict):
      self.hound_config = HoundConfig(**self.hound_config, audio_sample_rate=self.audio_sample_rate)
    else:
      self.hound_config.audio_sample_rate = self.audio_sample_rate
    if isinstance(self.houndify_handler_config, dict):
      self.houndify_handler_config = HoundifyHandlerConfig(**self.houndify_handler_config)
