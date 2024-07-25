import logging
from typing import Any, List, Tuple
from .park_detect_types import *


class CommandHandler():
    def __init__(self, zones: List[ZoneStatus], config: Config) -> None:
        self.zones = zones
        self.config = config

    def handle(self, command: PwCommandCodes, params: Any) -> Tuple[PwCommandCodes, Any]:
        handler = f"_{self.__class__.__name__}__handle_{command.name}"
        try:
            return self.__getattribute__(handler)(params)
        except Exception:
            logging.error(f"unknown command code: {command}")
            return (PwCommandCodes.Nak, None)

    def __handle_Ping(self, params: Any) -> Tuple[PwCommandCodes, Any]:
        return (PwCommandCodes.Pong, None)

    def __handle_RequestZoneStatus(self, zoneId: Any) -> Tuple[PwCommandCodes, Any]:
        parameters = None
        if zoneId == 0:
            parameters = self.zones
        elif 0 < zoneId <= len(self.zones):
            parameters = [self.zones[zoneId - 1]]
        else:
            return (PwCommandCodes.NAK, None)

        return (PwCommandCodes.ZoneStatus, parameters)

    def __handle_RequestZoneConfig(self, zoneId: Any) -> Tuple[PwCommandCodes, Any]:
        parameters = None
        if zoneId == 0:
            parameters = self.zones
        elif 0 < zoneId <= len(self.zones):
            parameters = [self.zones[zoneId - 1]]
        else:
            return (PwCommandCodes.NAK, None)

        return (PwCommandCodes.ZoneConfig, parameters)

    def __handle_RequestConfig(self, params: Any) -> Tuple[PwCommandCodes, Any]:
        return (PwCommandCodes.Config, self.config)
