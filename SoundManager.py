
class SoundManager:

    def __init__(self, sounds={}):
        self.sounds = sounds
        self.enableSounds = True

    def addSound(self, name, sound):
        self.sounds[name] = sound

    def play(self, soundName):
        if self.enableSounds:
            self.sounds[soundName].play()

    def setEnableSounds(self, enable):
        self.enableSounds = enable
