import operator
from pathlib import Path
from typing import Dict

import piexif
from PIL import Image


class Metadata:
    DESCRIPTION = {"0th": {270: bytes()}}
    ARTIST = {"0th": {315: bytes()}}
    COPYRIGHT = {"0th": {33432: bytes()}}
    TEMPERATURE = {"Exif": {37888: tuple()}}
    ATMOSPHERIC_PRESSURE = {"Exif": {37890: int()}}

    def __init__(self, file: Path):
        self.file = file
        self.image = Image.open(file)

    def metadata(self) -> Dict[str, object]:
        return piexif.load(self.image.info["exif"])

    @staticmethod
    def get(item: Dict[str, Dict[int, object]], metadata: Dict[str, object]):
        return {key: {index: metadata[key][index]}
                for key in item.keys()
                for index in item[key].keys()}

    @staticmethod
    def set(item: Dict[str, Dict[int, object]], value: object):
        for key in item.keys():
            for index in item[key].keys():
                item[key][index] = value
        return item

    @staticmethod
    def value(item: Dict[str, Dict[int, object]]) -> object:
        for key in item.keys():
            for index in item[key].keys():
                return item[key][index]
        return None

    @staticmethod
    def update(metadata: Dict[str, Dict[int, object]], entry: Dict[str, Dict[int, object]]):
        for key in entry.keys():
            for index in entry[key].keys():
                metadata[key][index] = entry[key][index]

    def save(self, metadata: Dict[str, Dict[int, object]], file: str = None):
        self.image.save(file if file else self.file, exif=piexif.dump(metadata))

    def export(self, prefix: str = ""):
        print(f"Processing {str(self.file)}...")
        metadata = self.metadata()

        artist = Metadata.set(Metadata.ARTIST,
                              bytes("Juan Rada-Vilela", "utf8"))
        copyright = Metadata.set(Metadata.COPYRIGHT,
                                 bytes("FuzzyLite Limited", "utf8"))

        temperature = operator.truediv(*(Metadata.value(Metadata.get(Metadata.TEMPERATURE, metadata))))

        hPa = Metadata.value(Metadata.get(Metadata.ATMOSPHERIC_PRESSURE, metadata))[0]
        p0 = 1013.25  # Sea-level pressure
        elevation = max(0, int(((pow(p0 / hPa, 1 / 5.257) - 1) * (temperature + 273.15)) / 0.0065))

        description = Metadata.set(Metadata.DESCRIPTION,
                                   bytes(f"Elevation: {elevation}m. Temperature: {temperature:0.1f}\u00B0C.", "utf8"))

        Metadata.update(metadata, artist)
        Metadata.update(metadata, copyright)
        Metadata.update(metadata, description)

        filename = str(self.file)
        ix_filename = filename.rfind(self.file.name)
        filename = filename[0:ix_filename] + prefix + filename[ix_filename:]

        self.save(metadata, filename)


if __name__ == "__main__":
    from multiprocessing.pool import ThreadPool

    pool = ThreadPool()
    pool.map(lambda file: Metadata(file).export("1/"), Path("/tmp/ap").glob("*.JPG"))
