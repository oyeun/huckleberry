class ResponseProcessor(object):

    def __init__(self, config):
        pass

    def process(self, response):
        if response['status'] == 'final' and response['message']['Status'] == 'OK':
            spokenResponse = response['message']['AllResults'][0]['SpokenResponseLong']
            print(response)
            print(spokenResponse)