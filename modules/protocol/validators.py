from .park_detect_types import *


class ValidateConfig():
    def validate(self, value):

        if value is None:
            value = Config()

        if isinstance(value, Config):
            value = value.__dict__

        if not isinstance(value, dict):
            raise ValueError("Specified config is not a dictionary")

        if "confidence_threshold" not in value or \
           type(value["confidence_threshold"]) is not int or \
           not (0 <= value["confidence_threshold"] <= 100):
            raise ValueError("Invalid confidence_threshold")

        if "inertia" not in value or not isinstance(value["inertia"], int) or value["inertia"] < 0:
            raise ValueError("Invalid inertia")

        if "tracking" not in value or not isinstance(value["tracking"], bool):
            raise ValueError("Invalid tracking")

        if "notifications" not in value or not isinstance(value["notifications"], bool):
            raise ValueError("Invalid notifications")

        return value


class ValidateZone():
    def validate(self, value):
        if isinstance(value, ZoneConfig):
            value = value.__dict__

        if not isinstance(value, dict):
            raise ValueError("Specified zone is not a dictionary")

        if "zoneId" not in value or type(value["zoneId"]) is not int or value["zoneId"] > 0xFFFF:
            raise ValueError("Specified zone contains an invalid zone id")

        if "points" not in value or not isinstance(value["points"], list) or len(value["points"]) < 3:
            raise ValueError("Specified zone does not contain valid points")

        for p in value["points"]:
            if not isinstance(p, list) or len(p) != 2 or type(p[0]) is not int or type(p[1]) is not int:
                raise ValueError("Specified zone contains invalid point")

        return value
