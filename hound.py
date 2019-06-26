from datetime import datetime
from houndify import houndify


class Hound(object):
    def __init__(self, config):
        CLIENT_ID = config['houndify']['primary_client']['client_id']
        CLIENT_KEY = config['houndify']['primary_client']['client_key']
        USER = config['houndify']['primary_client']['user']
        request_info = config['hound_client']
        self.client = houndify.StreamingHoundClient(
            CLIENT_ID,
            CLIENT_KEY,
            USER,
            sampleRate=config['audio']['sample_rate'],
            requestInfo=request_info,
            enableVAD=True)
        self.active = False

        self.finished = False
        self.listener = None

    def start(self):
        if not self.active:
            self.listener = MyListener()
            self.client.start(self.listener)
            self.active = True
            self.finished = False

    def listen(self, frame):
        if self.active and not self.finished:
            self.finished = self.client.fill(frame)
        return self.finished

    def finish(self, track_conversation=True):
        if self.active:
            self.active = False
            self.client.finish()
            if track_conversation:
                resp = self.listener.getState()['message']
                if resp and 'AllResults' in resp and 'ConversationState' in resp['AllResults'][0]:
                    self.client.HoundRequestInfo['ConversationState'] = resp['AllResults'][0]['ConversationState']

    def restart(self):
        # TODO
        return None

    def response(self):
        return self.listener.getState()

    def update_request_info(self, request_info):
        self.client.HoundRequestInfo.update(request_info)

    def text(self, query):
        # create text hound client
        print('implement me')


class MyListener(houndify.HoundListener):
    def __init__(self):
        self.status = 'initialized'
        self.messages = {}
        self.messages['initialized'] = f'initialized {datetime.now()}'

    def reset(self):
        self.status = 'initialized'
        self.messages = {}
        self.messages['initialized'] = f'initialized {datetime.now()}>'

    def onPartialTranscript(self, transcript):
        if transcript:
            self.status = 'partial'
            self.messages['partial'] = transcript

    def onFinalResponse(self, response):
        self.status = 'final'
        self.messages['final'] = response

    def onError(self, err):
        self.status = 'error'
        self.messages['error'] = str(err)

    def getState(self):
        #maybe: {status: -1|1, state: initialized|partial|final|error}
        return {
            'service': 'hound',
            'status': self.status,
            'message': self.messages[self.status]
        }
