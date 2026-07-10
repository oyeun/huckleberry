from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ActivationMethod(Enum):
  WAKEWORD = 'wakeword'
  VAD = 'vad'
  METHOD = 'method'


@dataclass
class VadConfig:
  audio_sample_rate: int = None
  sensitivity: int = 3 # 0-3
  window: int = 1000
  min_pass_ratio: float = 0.5


@dataclass
class WakewordConfig:
  wakeword: str = 'computer'
  timeout_after_wakeword: int = 5000 #ms
  kws_threshold: float = 1e-5
  logfn: str = '/dev/null'
  model_dir: str = None
  model_hmm: str = None
  model_dict: str = None


@dataclass
class HoundConfig:
  client_id: str
  client_key: str
  user: str
  audio_sample_rate: int = None
  request_info: dict = field(default_factory=dict)


# default response handler config
@dataclass
class HoundifyHandlerConfig:
  start_sound: str = None
  stop_sound: str = None
  ignore_bad_request: bool = False
  blocking_voice: bool = False
  output_device_index: Optional[int] = None
  frames_per_buffer: Optional[int] = 1024


@dataclass
class HuckleberryConfig:
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
