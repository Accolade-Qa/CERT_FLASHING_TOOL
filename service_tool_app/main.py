"""Application entry point."""

import sys

from PyQt5 import QtWidgets

from .ui import ServiceToolUi


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ServiceToolUi()
    window.showMaximized()
    app.exec_()
