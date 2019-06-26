from collections import deque


# my deque wrapper
class Myque(object):

    def __init__(self, maxsize):
        self.deque = deque()
        self.maxsize = maxsize
        self.ignore_maxsize = False
        # change ignore_maxsize to extended_size (type int) instead of boolean to avoid queue getting too large
        # when its appending but not popping?

    # add single element to end of queue, if full pop element from front
    def append(self, o):
        if not self.ignore_maxsize and self.size() >= self.maxsize:
            self.deque.pop()
        self.deque.append(o)

    # add single element to front of queue
    def appendleft(self, o):
        self.ignore_maxsize = True
        self.deque.appendleft(o)

    def extend(self, q):
        self.ignore_maxsize = True
        self.deque.extend(q)

    # add several elements to front of queue
    def extendleft(self, i):
        self.ignore_maxsize = True
        #i.reverse()
        self.deque.extendleft(i)

    # remove from front of queue
    def popleft(self):
        if self.size() > 0:
            o = self.deque.popleft()
            if self.ignore_maxsize and self.size() < self.maxsize:
                self.ignore_maxsize = False
            return o

    def size(self):
        return len(self.deque)

    def resize(self, maxsize):
        self.maxsize = maxsize

    def clear(self):
        self.deque.clear()
        self.ignore_maxsize = False

    def is_empty(self):
        return len(self.deque) == 0
