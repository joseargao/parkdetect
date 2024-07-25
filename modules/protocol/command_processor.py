from typing import Tuple, Iterator, Any
from .park_detect_types import *
from .validators import *


class CommandProcessor():

    NO_PARAMETER_COMMANDS = [
        PwCommandCodes.Ping,
        PwCommandCodes.Pong,
        PwCommandCodes.ACK,
        PwCommandCodes.NAK,
        PwCommandCodes.RequestConfig,
        PwCommandCodes.Restart
    ]

    @classmethod
    def decode_int16(cls, itr: Iterator):
        b = [next(itr), next(itr)]
        return int.from_bytes(b, byteorder='little')

    @classmethod
    def encode_int16(cls, val: int):
        return val.to_bytes(2, byteorder='little')

    @classmethod
    def encode_payload(cls, command, parameters) -> bytes:
        if command in cls.NO_PARAMETER_COMMANDS:
            return [command.value]
        elif command == PwCommandCodes.ZoneConfig:
            return cls.encode_zone_config(parameters)
        elif command == PwCommandCodes.ZoneStatus:
            return cls.encode_zone_status(parameters)
        elif command == PwCommandCodes.Config:
            return cls.encode_config(parameters)
        elif command == PwCommandCodes.RequestZoneStatus:
            return cls.encode_req_zone_status(parameters)
        elif command == PwCommandCodes.RequestZoneConfig:
            return cls.encode_req_zone_config(parameters)

        raise RuntimeError(f"Unknown Command Code for Encoding: {command}")

    @classmethod
    def decode_payload(cls, payload) -> Tuple[PwCommandCodes, Any]:
        command = PwCommandCodes(payload[0])
        if command in cls.NO_PARAMETER_COMMANDS:
            return (command, None)
        elif command == PwCommandCodes.ZoneConfig:
            return cls.decode_zone_config(payload)
        elif command == PwCommandCodes.ZoneStatus:
            return cls.decode_zone_status(payload)
        elif command == PwCommandCodes.Config:
            return cls.decode_config(payload)
        elif command == PwCommandCodes.RequestZoneStatus:
            return cls.decode_req_zone_status(payload)
        elif command == PwCommandCodes.RequestZoneConfig:
            return cls.decode_req_zone_config(payload)

        raise RuntimeError(f"Unknown Command Code for Decoding: {command}")

    @classmethod
    def encode_zone_config(cls, parameters):
        frame = [PwCommandCodes.ZoneConfig.value]
        for zone in parameters:
            ValidateZone().validate(zone)
            frame += cls.encode_int16(zone.zoneId)
            frame += [len(zone.points)]
            for p in zone.points:
                frame += cls.encode_int16(p[0])
                frame += cls.encode_int16(p[1])

        return frame

    @classmethod
    def decode_zone_config(cls, payload):
        command = PwCommandCodes(payload[0])
        payload_iter = iter(payload[1:])
        parameters = []
        try:
            while True:
                zoneId = cls.decode_int16(payload_iter)
                zone = ZoneConfig(zoneId=zoneId, points=[])
                points_len = next(payload_iter)
                for i in range(points_len):
                    px = cls.decode_int16(payload_iter)
                    py = cls.decode_int16(payload_iter)
                    zone.points.append([px, py])

                parameters.append(zone)

        except StopIteration:
            return (command, parameters)

    @classmethod
    def encode_zone_status(cls, parameters):
        frame = [PwCommandCodes.ZoneStatus.value]
        for zone_status in parameters:
            frame += cls.encode_int16(zone_status.zoneId)
            frame += [zone_status.status.value]
            frame += cls.encode_int16(zone_status.count)

        return frame

    @classmethod
    def decode_zone_status(cls, payload):
        command = PwCommandCodes(payload[0])
        payload_iter = iter(payload[1:])
        parameters = []
        try:
            while True:
                zoneId = cls.decode_int16(payload_iter)
                status = PwZoneState(next(payload_iter))
                count = cls.decode_int16(payload_iter)
                zone = ZoneStatus(zoneId=zoneId, status=status, count=count)
                parameters.append(zone)

        except StopIteration:
            return (command, parameters)

    @classmethod
    def encode_config(cls, config):
        frame = [PwCommandCodes.Config.value]
        ValidateConfig().validate(config)
        frame += [config.confidence_threshold]
        frame += [config.inertia]
        frame += [config.tracking]
        frame += [config.notifications]

        return frame

    @classmethod
    def decode_config(cls, payload):
        command = PwCommandCodes(payload[0])
        payload_iter = iter(payload[1:])
        config = Config(confidence_threshold=next(payload_iter), inertia=next(payload_iter),
                        tracking=next(payload_iter), notifications=next(payload_iter))

        return (command, config)

    @classmethod
    def encode_req_zone_status(cls, parameters):
        zoneId = parameters
        frame = [PwCommandCodes.RequestZoneStatus.value]
        if type(zoneId) is not int or zoneId < 0:
            raise ValueError("Invalid Zone ID")

        frame += cls.encode_int16(zoneId)

        return frame

    @classmethod
    def decode_req_zone_status(cls, payload):
        command = PwCommandCodes(payload[0])
        payload_iter = iter(payload[1:])
        parameters = cls.decode_int16(payload_iter)

        return (command, parameters)

    @classmethod
    def encode_req_zone_config(cls, parameters):
        zoneId = parameters
        frame = [PwCommandCodes.RequestZoneConfig.value]
        if type(zoneId) is not int or zoneId < 0:
            raise ValueError("Invalid Zone ID")

        frame += cls.encode_int16(zoneId)

        return frame

    @classmethod
    def decode_req_zone_config(cls, payload):
        command = PwCommandCodes(payload[0])
        payload_iter = iter(payload[1:])
        parameters = cls.decode_int16(payload_iter)

        return (command, parameters)
