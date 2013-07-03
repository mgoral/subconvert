# Unfortunately unittest.mock is available in std from Python 3.3 and I don't want to create
# another dependency

class FrameTimeMock:
    def __init__(self, fps):
        self.fps = fps
        self._fps = fps
        self._full_seconds = 0

    def __eq__(self, other):
        return self.fps == other.fps

    def __ne__(self, other):
        return self.fps != other.fps

class SubtitleMock:
    def __init__(self, start = None, end = None, text = None):
        self.start = start
        self.end = end
        self.text = text
        self.fps = None

    def __eq__(self, other):
        return self.text == other.text

    def __ne__(self, other):
        return self.text != other.text

