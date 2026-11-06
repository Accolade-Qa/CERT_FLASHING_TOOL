"""Pure Python helpers for service-tool device logic."""

import re


def calculate_crc16(input_crc, data):
    crc = input_crc
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
    return crc & 0xFFFF


def is_default_uin(uin):
    return bool(re.fullmatch(r'ACON4NA[X]+', uin.strip(), re.IGNORECASE))
