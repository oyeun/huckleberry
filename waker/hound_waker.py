import logging
import okhound
from config import HoundConfig


class HoundWaker(object):
  def __init__(self, config: HoundConfig):
    self.logger = logging.getLogger(__name__)
    okhound.setThreshold(0.4)
    self.logger.debug('houndwaker initialized')

  def start(self):
    pass

  def listen(self, buf):
    phrase_spotted = okhound.processSamples(buf)
    if phrase_spotted:
      return True
    return False

  def finish(self):
    pass
