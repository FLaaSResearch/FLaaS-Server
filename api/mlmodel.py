import numpy as np

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


class MLModel:

    def __init__(self, size, state):

        self.devices = 0

        if state == "random":
            self.weights = np.random.rand(size)
        elif state == "zeros":
            self.weights = np.zeros(size)
        else:
            raise Exception("Unknown state:" + state)

    def accumulate_model(self, file_path):

        try:
            with default_storage.open(file_path) as data:
                weights = np.frombuffer(data.read(), dtype=np.float32)
                if len(weights) == len(self.weights):
                    self.weights += weights
                    self.devices += 1
                else:
                    print("Ignoring weights with incorrect length: %d" % len(weights))
        except (OSError, IOError) as ex:
            print("Something went wrong while accumulating model at '%s'" % file_path)
            print(ex)

    def aggregate(self):
        if self.devices > 1:
            self.weights /= self.devices
        self.devices = 0

    def write(self, filename):
        content = ContentFile(self.weights.astype('float32'))
        default_storage.save(filename, content)
