from typing import List, Any, Dict
from enum import Enum


class PwCommandCodes(Enum):
    Ping = 0x01
    Pong = 0x02
    ACK = 0x11
    NAK = 0xEE
    ZoneStatus = 0x20
    Config = 0x21
    ZoneConfig = 0x22
    RequestZoneStatus = 0x30
    RequestConfig = 0x31
    Restart = 0x32
    RequestZoneConfig = 0x33


class PwZoneState(Enum):
    Empty = 0x00
    Occupied = 0x01
    Unavailable = 0xFF


class Config():
    def __init__(self, confidence_threshold: int = 25, inertia: int = 3,
                 tracking: bool = False, notifications: bool = True) -> None:
        self.confidence_threshold = confidence_threshold
        self.inertia = inertia
        self.tracking = tracking
        self.notifications = notifications

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, type(self)):
            return False

        return self.confidence_threshold == __value.confidence_threshold and \
               self.inertia == __value.inertia and \
               self.tracking == __value.tracking and \
               self.notifications == __value.notifications

    def __repr__(self) -> str:
        return f"threshold:{self.confidence_threshold}, inertia:{self.inertia}" \
            f", track:{self.tracking}, notify:{self.notifications}"


class ZoneConfig():
    def __init__(self, zoneId: int, points: List[List[int]]) -> None:
        self.zoneId = zoneId
        self.points = points

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, type(self)):
            return False

        return self.zoneId == __value.zoneId and self.points == __value.points

    def __repr__(self) -> str:
        return f"zone:{self.zoneId}, points:{self.points}"


class ZoneStatus(ZoneConfig):
    def __init__(self, zoneId: int, status: PwZoneState, count: int, points: List[List[int]] = None) -> None:
        if not points:
            points = []
        super().__init__(zoneId, points)
        self.status = status
        self.count = count

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, type(self)):
            return False

        return self.zoneId == __value.zoneId and self.status == __value.status and self.count == __value.count

    def __repr__(self) -> str:
        pts = f", points:{self.points}" if self.points else ""
        return f"zone:{self.zoneId}, status:{self.status.name}, count:{self.count}{pts}"
