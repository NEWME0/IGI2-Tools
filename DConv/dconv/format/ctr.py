import numpy as np


class CTR:
    __slots__ = ('items')

    def __init__(self):
        self.items = list()

    def load(self, fp):
        if isinstance(fp, str):
            fp = open(fp, 'rb')

        self.items = np.frombuffer(fp.read(), (np.uint8, 32))

        fp.close()