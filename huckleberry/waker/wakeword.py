import os
from ..config import WakewordConfig
from pocketsphinx import Decoder, get_model_path


class Wakeword(object):
  def __init__(self, config: WakewordConfig):
    self.decoder_config = Decoder.default_config()
    self.decoder_config.set_string('-keyphrase', config.wakeword)
    self.decoder_config.set_float('-kws_threshold', float(config.kws_threshold))
    if config.model_dir is not None:
      # custom
      modeldir = config.model_dir
      self.decoder_config.set_string('-hmm', os.path.join(modeldir, config.model_hmm))
      self.decoder_config.set_string('-dict', os.path.join(modeldir, config.model_dict))
    else:
      # default
      modeldir = get_model_path()
      self.decoder_config.set_string('-hmm', os.path.join(modeldir, 'en-us/en-us'))
      self.decoder_config.set_string('-dict', os.path.join(modeldir, 'en-us/cmudict-en-us.dict'))
      self.decoder_config.set_string('-lm', None)
    self.decoder = Decoder(self.decoder_config)
    self.started = False

  def start(self):
    if not self.started:
      self.decoder.start_utt()
      self.started = True

  def listen(self, buf):
    if self.started:
      if buf:
        self.decoder.process_raw(buf, False, False)
      if self.decoder.hyp() is not None:
        return True
    return False

  def finish(self):
    if self.started:
      self.decoder.end_utt()
      self.started = False
