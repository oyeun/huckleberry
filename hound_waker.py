import okhound

class HoundWaker(object):

    def __init__(self, config):
        okhound.setThreshold(0.4)

    def start(self):
        pass

    def listen(self, buf):
        phrase_spotted = okhound.processSamples(buf)
        if phrase_spotted:
            return True
        return False

    def finish(self):
        pass
