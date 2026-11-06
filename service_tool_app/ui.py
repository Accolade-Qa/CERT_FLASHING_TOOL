"""Qt user interface for the service tool."""

import os

import serial
import serial.tools.list_ports as ports
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QPixmap

from .config import CERT_FILE_NAMES, get_resource_path
from .device import Worker


class ServiceToolUi(QtWidgets.QMainWindow):
    def __init__(self):
        super(ServiceToolUi, self).__init__()
        uic.loadUi(self.get_resource_path(os.path.join('resources', 'service_tool.ui')), self)
        self.comboBoxComPort = self.findChild(QtWidgets.QComboBox, 'comboBoxComPort')
        self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')
        self.progressBar = self.findChild(QtWidgets.QProgressBar, 'progressBarFlow')
        self.labelLogo = self.findChild(QtWidgets.QLabel, 'labelLogo')
        self.headerSeparator = self.findChild(QtWidgets.QFrame, 'headerSeparator')
        self.log = self.findChild(QtWidgets.QTextBrowser, 'textBrowserLog')

        self.worker = Worker()
        self.worker.certificatePaths = [
            self.get_resource_path(os.path.join('resources', fileName))
            for fileName in CERT_FILE_NAMES
        ]
        logoPath = self.get_resource_path(os.path.join('resources', 'accolade-logo.png'))
        if not os.path.isfile(logoPath):
            raise FileNotFoundError('Logo image not found: {}'.format(logoPath))
        logoPixmap = QPixmap(logoPath)
        if logoPixmap.isNull():
            raise OSError('Could not load logo image: {}'.format(logoPath))
        samplePixmap = logoPixmap.scaled(256, 256, QtCore.Qt.IgnoreAspectRatio)
        sampleImage = samplePixmap.toImage()
        left, top = sampleImage.width(), sampleImage.height()
        right, bottom = -1, -1
        for y in range(sampleImage.height()):
            for x in range(sampleImage.width()):
                color = sampleImage.pixelColor(x, y)
                if color.alpha() and min(color.red(), color.green(), color.blue()) < 245:
                    left, top = min(left, x), min(top, y)
                    right, bottom = max(right, x), max(bottom, y)
        if right < left or bottom < top:
            raise OSError('Logo image contains no visible content: {}'.format(logoPath))
        sourceLeft = left * logoPixmap.width() // sampleImage.width()
        sourceTop = top * logoPixmap.height() // sampleImage.height()
        sourceRight = (right + 1) * logoPixmap.width() // sampleImage.width()
        sourceBottom = (bottom + 1) * logoPixmap.height() // sampleImage.height()
        visibleLogo = logoPixmap.copy(
            sourceLeft,
            sourceTop,
            sourceRight - sourceLeft,
            sourceBottom - sourceTop,
        )
        self.labelLogo.setPixmap(
            visibleLogo.scaled(
                self.labelLogo.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )
        self.logoPixmap = visibleLogo

        self.comboBoxComPort.addItems(
            '{}: {}'.format(port.device, port.description)
            for port in ports.comports()
        )
        self.btnConnect.clicked.connect(self.connectUart)

        self.progressResetTimer = QtCore.QTimer(self)
        self.progressResetTimer.setSingleShot(True)
        self.progressResetTimer.timeout.connect(lambda: self.progressBar.setValue(0))

        self.thread = QtCore.QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.work)
        self.worker.logMsg.connect(self.logAppend)
        self.worker.errorMsg.connect(self.showError)
        self.worker.popupMsg.connect(self.showPopup)
        self.worker.progressChanged.connect(self.progressBar.setValue)
        self.worker.flowFinished.connect(self.resetForNextCycle)
        self.thread.start()
        self.closing = False
        self.setMinimumSize(1024, 640)

    def resizeEvent(self, event):
        super(ServiceToolUi, self).resizeEvent(event)
        if not hasattr(self, 'comboBoxComPort') or not hasattr(self, 'logoPixmap'):
            return

        width = self.centralWidget().width()
        height = self.centralWidget().height()
        margin = max(16, int(width * 0.02))
        headerHeight = max(88, int(height * 0.15))
        rowHeight = max(34, int(height * 0.045))
        progressHeight = max(26, int(height * 0.035))
        buttonWidth = max(100, int(width * 0.09))
        gap = max(28, int(width * 0.025))

        self.labelLogo.setGeometry(
            margin,
            margin,
            min(int(width * 0.23), 340),
            headerHeight - 2 * margin,
        )
        self.labelVersion.setGeometry(
            self.labelLogo.geometry().right() + gap,
            margin,
            width - self.labelLogo.geometry().right() - gap - margin,
            headerHeight - 2 * margin,
        )
        titleFont = self.labelVersion.font()
        titleFont.setPointSize(max(16, min(23, int(height * 0.024))))
        self.labelVersion.setFont(titleFont)
        self.labelVersion.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.headerSeparator.setGeometry(margin, headerHeight, width - 2 * margin, 2)
        self.labelLogo.setPixmap(
            self.logoPixmap.scaled(
                self.labelLogo.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )

        controlsY = headerHeight + 2 * margin
        self.btnConnect.setGeometry(
            width - margin - buttonWidth,
            controlsY,
            buttonWidth,
            rowHeight,
        )
        self.comboBoxComPort.setGeometry(
            margin,
            controlsY,
            width - 3 * margin - buttonWidth,
            rowHeight,
        )
        controlsFont = self.comboBoxComPort.font()
        controlsFont.setPointSize(10)
        self.comboBoxComPort.setFont(controlsFont)
        self.btnConnect.setFont(controlsFont)
        progressY = controlsY + rowHeight + margin
        self.progressBar.setGeometry(
            margin,
            progressY,
            width - 2 * margin,
            progressHeight,
        )
        logY = progressY + progressHeight + margin
        self.log.setGeometry(
            margin,
            logY,
            width - 2 * margin,
            max(100, height - logY - margin),
        )
        progressFont = self.progressBar.font()
        progressFont.setPointSize(9)
        self.progressBar.setFont(progressFont)
        logFont = self.log.font()
        logFont.setPointSize(9)
        self.log.setFont(logFont)

    def connectUart(self):
        selectedPort = self.comboBoxComPort.currentText()
        portName = selectedPort.split(':', 1)[0].strip()
        if not portName or portName == 'Select Serial Port...':
            self.showError('Select a serial port before connecting.')
            return
        try:
            self.progressResetTimer.stop()
            self.progressBar.setValue(0)
            serialPort = serial.Serial(portName, 115200, timeout=0.1)
            self.worker.checksComplete = False
            self.worker.results = {}
            self.worker.scanRequested = True
            self.worker.serialPort = serialPort
        except (OSError, serial.SerialException) as error:
            self.worker.serialPort = None
            self.showError('Could not open {}: {}'.format(portName, error))
            return
        self.comboBoxComPort.setEnabled(False)
        self.btnConnect.setEnabled(False)
        self.btnConnect.setText('Connected')
        self.logAppend('Connected to {}. Starting device check and certificate flow...'.format(portName))

    def resetForNextCycle(self):
        self.log.clear()
        self.comboBoxComPort.setEnabled(True)
        self.btnConnect.setText('Connect')
        self.btnConnect.setEnabled(True)
        self.progressBar.setValue(100)
        self.progressResetTimer.start(1800)

    def get_resource_path(self, relativePath):
        return get_resource_path(relativePath)

    def logAppend(self, value):
        self.log.append(value)

    def showError(self, message):
        QtWidgets.QMessageBox.critical(self, 'Service Tool', message)

    def showPopup(self, title, message):
        QtWidgets.QMessageBox.warning(self, title, message)

    def closeEvent(self, event):
        if self.thread.isRunning():
            if not self.closing:
                self.closing = True
                self.setEnabled(False)
                self.worker.working = False
                self.thread.finished.connect(self.close)
            self.thread.quit()
            event.ignore()
            return
        event.accept()

