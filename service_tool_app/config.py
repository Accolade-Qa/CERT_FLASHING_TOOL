"""Application paths and shared configuration."""

import os
import sys

BUILD_VERSION = '1.0.0'
EXCEL_FILENAME = 'cert_flashing_status.xlsx'
LEGACY_CSV_FILENAMES = (
    'cert_flashing_status.csv',
    'service_tool_device_checks.csv',
)
CERT_FILE_NAMES = ('ca.pem', 'cc.pem', 'ck.pem')


def get_app_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_excel_path():
    return os.path.join(get_app_directory(), EXCEL_FILENAME)


def get_resource_path(relative_path):
    base_directory = (
        sys._MEIPASS
        if getattr(sys, 'frozen', False)
        else get_app_directory()
    )
    return os.path.join(base_directory, relative_path)
