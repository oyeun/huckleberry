import os
from pypocketsphinx import Decoder, get_model_path


class Waker(object):

    def __init__(self, config):
        self.decoder_config = Decoder.default_config()
        self.decoder_config.set_string('-keyphrase', config['wakeword'])
        self.decoder_config.set_float('-kws_threshold', float(config['waker']['pocketsphinx']['kws_threshold']))  # this should be configurable realtime to adjust for noisy environments? if possible...
        self.decoder_config.set_string('-logfn', config['waker']['pocketsphinx']['logfn'])
        if 'model_dir' in config['waker']['pocketsphinx']:
            # custom
            modeldir = config['waker']['pocketsphinx']['model_dir']
            self.decoder_config.set_string('-hmm', os.path.join(modeldir, config['waker']['pocketsphinx']['hmm']))
            self.decoder_config.set_string('-dict', os.path.join(modeldir, config['waker']['pocketsphinx']['dict']))
            self.decoder_config.set_string('-lm', os.path.join(modeldir, config['waker']['pocketsphinx']['lm']))
        else:
            # default
            modeldir = get_model_path()
            self.decoder_config.set_string('-hmm', os.path.join(modeldir, 'en-us'))
            self.decoder_config.set_string('-dict', os.path.join(modeldir, 'cmudict-en-us.dict'))
            self.decoder_config.set_string('-lm', os.path.join(modeldir, 'en-us.lm.bin'))
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
