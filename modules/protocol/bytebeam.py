from enum import Enum
from typing import List, Tuple, Dict
from datetime import datetime

MULTI_FRAME_TIMEOUT = 0.5


class SequenceType(Enum):
    First = 0
    Continue = 1
    Last = 2


class ByteBeamHeader():
    def __init__(self, version: int = None, size: int = None, index: int = None,
                 sequence: SequenceType = None, frame_data: bytes = None) -> None:

        if frame_data:
            if version or size or index or sequence:
                raise ValueError("frame_data is exclusive")
            self.version = frame_data[0]
            self.size = frame_data[1]
            self.index = frame_data[2]
            self.sequence = SequenceType(frame_data[3])
        else:
            if version is None or size is None or index is None or sequence is None:
                raise ValueError("missing required parameters")
            self.version = version
            self.size = size
            self.index = index
            self.sequence = sequence

    def getBytes(self):
        return [self.version, self.size, self.index, self.sequence.value]

    def getSize(self):
        return 4

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, type(self)):
            return False
        return self.getBytes() == __o.getBytes()

    def __repr__(self) -> str:
        return f"version:{self.version}, size:{self.size}, index:{self.index}, type:{self.sequence.name}"


class ByteBeamProtocol():
    def __init__(self) -> None:
        self.__reset_inprogress_data()

    def __reset_inprogress_data(self):
        self.__inprogress_header = None
        self.__inprogress_data = None
        self.__last_inprogress_frame = datetime.now()

    def calculate_crc16(self, data):
        crc = 0xFFFF  # Initial CRC value
        poly = 0xA001  # CRC-16 polynomial

        for int_val in data:
            crc ^= int_val
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1

        return crc & 0xFFFF

    def encode(self, header: ByteBeamHeader, payload: List[int]) -> bytes:

        data = header.getBytes() + payload
        crc16 = self.calculate_crc16(data)
        data += list(crc16.to_bytes(2, byteorder='little'))

        return data

    def decode(self, data) -> Dict | None:
        if (datetime.now() - self.__last_inprogress_frame).total_seconds() >= MULTI_FRAME_TIMEOUT:
            self.__reset_inprogress_data()

        self.__last_inprogress_frame = datetime.now()
        if not self.__inprogress_header:
            self.__inprogress_header = ByteBeamHeader(frame_data=data)
            self.__inprogress_data = []
            data = data[self.__inprogress_header.getSize():]

        self.__inprogress_data += data
        if len(self.__inprogress_data) >= self.__inprogress_header.size + 2:
            if not self.calculate_crc16(self.__inprogress_header.getBytes() + self.__inprogress_data) == 0:
                self.__reset_inprogress_data()
                raise ValueError("Invalid CRC")

            result = {
                "header": self.__inprogress_header,
                "payload": self.__inprogress_data[:-2],
            }

            self.__reset_inprogress_data()

            return result
