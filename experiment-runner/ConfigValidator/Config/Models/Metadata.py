

class Metadata:

    def __init__(self, md5sum: bytes):
        self._md5sum = md5sum

    @property
    def md5sum(self):
        return self._md5sum

    @md5sum.setter
    def md5sum(self, md5sum: bytes):
        self._md5sum = md5sum
