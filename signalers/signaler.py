import base64
import pyaudio

from audio_handler.streams import Streams


class Signaler(object):

    def __init__(self, config):
        self.p = pyaudio.PyAudio()
        self.streams = Streams(self.p)
        #self.streams.play_music('sounds/liszt.wav')
        #pass

    def activate(self):
        self.streams.play_open_sound()
        self.streams.signal_hound_start()
        print('activated')

    def deactivate(self):
        self.streams.play_close_sound()
        self.streams.signal_hound_stop()
        print('deactivated')

    def handle_response_audio(self, audio):
        self.streams.play_voice(audio)
        #pass

    def process(self, response):
        if response['status'] == 'final' and response['message']['Status'] == 'OK':
            response_audio = base64.b64decode(response['message']['AllResults'][0]['ResponseAudioBytes'])
            self.handle_response_audio(response_audio)
            spokenResponse = response['message']['AllResults'][0]['SpokenResponseLong']
            #print(response)
            print(response['message']['Disambiguation']['ChoiceData'][0]['Transcription'])
            print(spokenResponse)

    def close(self):
        self.streams.close()
        self.p.terminate()
        #pass
