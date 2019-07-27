from json_minify import json_minify
import json


class Conf:
    def __init__(self, confPath):
        conf = json.loads(json_minify(open(confPath).read()))
        self.__dict__.update(conf)

    def __getitem__(self, k):
        return self.__dict__.get(k, None)

    def save(self, file_name, data):
        with open(file_name, "r") as jsonFile:
            settings = json.load(jsonFile)

        settings.update(data)
        self.__dict__.update(settings)

        with open(file_name, "w") as jsonFile:
            json.dump(settings, jsonFile)



