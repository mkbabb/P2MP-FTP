import socket
import struct
from enum import Enum
from typing import *
from dataclasses import dataclass

PORT = 7735

CHUNK_SIZE = 1024

"""Packet format: 
!: Network format
I: 32-bit sequence number that is being ACKed
H: 16-bit checksum field
H: 16-bit data type field (value 0b1010101010101010, indicating that this is an ACK packet)
I: 32-bit data length field 
"""
UDP_HEADER_FMT = "!IHHI"
UDP_HEADER_SIZE = struct.calcsize(UDP_HEADER_FMT)


class UDPPacketType(Enum):
    ACK = 0b1010101010101010


@dataclass
class Packet:
    seq_num: int = 0
    checksum: int = 0
    dtype: UDPPacketType = UDPPacketType.ACK
    data_len: int = 0
    data: bytes = b""


def carry_add(a: int, b: int) -> int:
    c = a + b
    return (c & 0xFFFF) + (c >> 16)


def calc_checksum(data: bytes, invert: bool = True) -> int:
    if len(data) % 2 != 0:
        data += struct.pack("!B", 0)

    checksum = 0
    for i in range(0, len(data), 2):
        checksum = carry_add(data[i] << 8, data[i + 1])

    if invert:
        return ~checksum & 0xFFFF
    else:
        return checksum


def recv_message(
    peer_socket: socket.socket,
    chunk_size: int = CHUNK_SIZE,
) -> Optional[Packet]:
    header = peer_socket.recv(UDP_HEADER_SIZE)
    seq_num, datasum, dtype, data_len = struct.unpack(UDP_HEADER_FMT, header)

    data = b""
    t_data_len = data_len

    while t_data_len > 0:
        chunk_size = min(chunk_size, t_data_len)

        response = peer_socket.recv(chunk_size)
        data += response

        t_data_len -= chunk_size

    checksum = calc_checksum(data, False)

    if (datasum + checksum) == 0xFFFF:
        return Packet(seq_num, datasum, UDPPacketType(dtype), data_len, data)
    else:
        return None


def send_message(
    data: bytes,
    peer_socket: socket.socket,
    seq_number: int = 0,
    dtype: UDPPacketType = UDPPacketType.ACK,
) -> int:
    checksum = calc_checksum(data)
    header = struct.pack(UDP_HEADER_FMT, seq_number, checksum, dtype.value, len(data))

    peer_socket.send(header)
    peer_socket.send(data)
