from wave import Wave_write, open as wave_open
from typing import BinaryIO

from igipy.wav.models import WAV, SoundPack
from igipy.converters import FileConverter, ConversionError


class WAVFileConverter(FileConverter):
    """
        Convert IGI WAV model to WaveForm format.
    """

    def __init__(self, verbose: bool = False, force: bool = False):
        self.verbose = verbose
        self.force = force

    def convert(self, instance: WAV, file: BinaryIO):
        if instance.sound_pack in (SoundPack.ADPCM, SoundPack.ADPCM_RESIDENT) and not self.force:
            raise ConversionError(f"Can not unpack {SoundPack(instance.sound_pack).name}")

        with wave_open(file, 'w') as wave_file:
            wave_file: Wave_write = wave_file
            wave_file.setnchannels(instance.channels)
            wave_file.setsampwidth(instance.sample_width // 8)
            wave_file.setframerate(instance.frame_rate)
            wave_file.writeframesraw(instance.frames)
