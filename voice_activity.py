"""Small RMS-based end-of-turn detector for mono signed-16-bit PCM at 16 kHz."""
from array import array
from math import sqrt


class EndOfTurn:
    def __init__(self, threshold=400, pause_seconds=1.35):
        self.threshold = threshold
        self.pause = int(pause_seconds * 16000)
        self.voiced = self.quiet = 0

    def feed(self, pcm):
        samples = array('h', pcm)
        if not samples:
            return False
        rms = sqrt(sum(x*x for x in samples) / len(samples))
        if rms >= self.threshold:
            self.voiced += len(samples)
            self.quiet = 0
        else:
            self.quiet += len(samples)
        return self.voiced >= 2400 and self.quiet >= self.pause
