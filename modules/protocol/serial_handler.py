
import serial
from threading import Thread, RLock
from typing import List, Any
from .park_detect_types import *
from .bytebeam import ByteBeamProtocol, ByteBeamHeader, SequenceType
from .command_handler import CommandHandler
from .command_processor import CommandProcessor


class SerialHandler():
    def __init__(self, zones: List[ZoneStatus], config: Config) -> None:
        self.__serial_port = serial.Serial ("/dev/ttyAMA0", 19200, parity="E")    # Open port with baud rate
        self.__codec = ByteBeamProtocol()
        self.__command_handler = CommandHandler(zones=zones, config=config)

    def start_rx_thread(self):
        self.__mutex = RLock()
        self.__is_running = True
        self.__thread = Thread(target=self.__handle_serial_port)
        self.__thread.start()

    def stop_rx_thread(self):
        self.__is_running = False
        self.__thread.join()

    def handle_command(self, rx_command: PwCommandCodes, rx_params: Any, index: int = 0) -> None:
        with self.__mutex:
            tx_command, tx_params = self.__command_handler.handle(rx_command, rx_params)
            tx_data = self.__encode_command(tx_command=tx_command, tx_params=tx_params, index=index)
            if tx_data:
                self.__serial_port.write(tx_data)

    def send_command(self, tx_command: PwCommandCodes, tx_params: Any, index: int = 0) -> None:
        with self.__mutex:
            tx_data = self.__encode_command(tx_command=tx_command, tx_params=tx_params, index=index)
            if tx_data:
                self.__serial_port.write(tx_data)

    def __handle_serial_port(self):
        while self.__is_running:
            with self.__mutex:
                rx_data = self.__serial_port.read_all()
                if rx_data:
                    tx_data = self.__handle_rx_data(rx_data=rx_data)
                    if tx_data:
                        self.__serial_port.write(tx_data)

    def __handle_rx_data(self, rx_data: bytes) -> None:
        result = self.__decode_command(rx_data=rx_data)
        if result:
            rx_command, rx_params, index = result
            print(rx_command, rx_params)
            self.handle_command(rx_command=rx_command, rx_params=rx_params, index=index)

    def __decode_command(self, rx_data):
        result = self.__codec.decode(rx_data)
        if result:
            rx_header: ByteBeamHeader = result["header"]
            rx_command, rx_params = CommandProcessor.decode_payload(result["payload"])
            return (rx_command, rx_params, rx_header.index)

    def __encode_command(self, tx_command: PwCommandCodes, tx_params: Any, index: int = 0) -> bytes | None:
        print(tx_command, tx_params)
        tx_payload = CommandProcessor.encode_payload(command=tx_command, parameters=tx_params)

        header = ByteBeamHeader(version=1, size=len(tx_payload), index=index, sequence=SequenceType.Last)
        tx_data = self.__codec.encode(header, tx_payload)
        return tx_data
