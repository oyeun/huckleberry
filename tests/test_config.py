import unittest
from huckleberry.config import HuckleberryConfig, ActivationMethod, VadConfig, WakewordConfig, HoundConfig, \
  HoundifyHandlerConfig

class TestConfig(unittest.TestCase):
  def test_defaults(self):
    config = HuckleberryConfig(
      vad_config=VadConfig(),
      wakeword_config=WakewordConfig(
        wakeword='ok hound',
        timeout_after_wakeword=5000,
        kws_threshold=1e-5),
      hound_config=HoundConfig(
        client_id='clientId',
        client_key='clientKey',
        user='bob',
        request_info={
          'ResponseAudioShortOrLong': 'Long',
          'ResponseAudioVoice': 'QueenElizabeth'
        }),
      houndify_handler_config=HoundifyHandlerConfig(
        start_sound='startSound',
        stop_sound='stopSound'
      )
    )
    # test default config values in HuckleberryConfig:
    self.assertEqual(config.input_device_index, None)
    self.assertEqual(config.activation_method, ActivationMethod.WAKEWORD)
    self.assertEqual(config.audio_sample_rate, 16000)
    self.assertEqual(config.frame_duration, 30)
    self.assertEqual(config.frame_buffer_size, 3000)
    self.assertEqual(config.audio_channels, 1)
    self.assertEqual(config.audio_encoding, 16)
    # test calculated values
    self.assertEqual(config.chunk_size, config.audio_encoding * config.frame_duration)
    self.assertEqual(config.max_frames, config.frame_buffer_size // config.frame_duration)

if __name__ == '__main__':
    unittest.main()
