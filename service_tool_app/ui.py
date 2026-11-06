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
        self.btnRefreshPorts = self.findChild(QtWidgets.QPushButton, 'btnRefreshPorts')
        self.btnConnect = self.findChild(QtWidgets.QPushButton, 'btnConnect')
        self.progressBar = self.findChild(QtWidgets.QProgressBar, 'progressBarFlow')
        self.labelLogo = self.findChild(QtWidgets.QLabel, 'labelLogo')
        self.labelDateTime = self.findChild(QtWidgets.QLabel, 'labelDateTime')
        self.headerPanel = self.findChild(QtWidgets.QFrame, 'headerPanel')
        self.headerSeparator = self.findChild(QtWidgets.QFrame, 'headerSeparator')
        self.labelUin = self.findChild(QtWidgets.QLabel, 'labelUin')
        self.uinPanel = self.findChild(QtWidgets.QFrame, 'uinPanel')
        self.labelUinValue = self.findChild(QtWidgets.QLabel, 'labelUinValue')
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
        self.labelLogo.setPixmap(
            logoPixmap.scaled(
                self.labelLogo.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )
        self.logoPixmap = logoPixmap

        self.clockTimer = QtCore.QTimer(self)
        self.clockTimer.timeout.connect(self.updateDateTime)
        self.updateDateTime()
        self.clockTimer.start(1000)

        self.refreshPorts()
        self.btnRefreshPorts.clicked.connect(self.refreshPorts)
        self.btnConnect.clicked.connect(self.connectUart)

        self.progressResetTimer = QtCore.QTimer(self)
        self.progressResetTimer.setSingleShot(True)
        self.progressResetTimer.timeout.connect(lambda: self.progressBar.setValue(0))

        self.thread = QtCore.QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.work)
        self.worker.logMsg.connect(self.logAppend)
        self.worker.uinUpdated.connect(self.updateUin)
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
        headerHeight = max(112, min(150, int(height * 0.17)))
        rowHeight = max(34, int(height * 0.045))
        progressHeight = max(26, int(height * 0.035))
        buttonWidth = max(100, int(width * 0.09))
        refreshButtonWidth = max(100, int(width * 0.09))
        buttonGap = margin
        uinLabelWidth = 44
        logoWidth = min(int(width * 0.21), 300)
        dateTimeWidth = min(int(width * 0.23), 280)
        uinPanelWidth = min(max(int(width * 0.25), 280), 320)
        uinPanelHeight = max(30, rowHeight + 8)

        self.headerPanel.setGeometry(0, 0, width, headerHeight)
        self.labelLogo.setGeometry(
            margin,
            (headerHeight - min(64, headerHeight - 20)) // 2,
            logoWidth,
            min(64, headerHeight - 20),
        )
        self.labelVersion.setGeometry(
            (width - min(int(width * 0.42), 520)) // 2,
            0,
            min(int(width * 0.42), 520),
            headerHeight,
        )
        titleFont = self.labelVersion.font()
        titleFont.setPointSize(max(16, min(23, int(height * 0.024))))
        self.labelVersion.setFont(titleFont)
        self.labelVersion.setAlignment(QtCore.Qt.AlignCenter)
        self.labelDateTime.setGeometry(
            width - margin - dateTimeWidth,
            0,
            dateTimeWidth,
            headerHeight,
        )
        dateTimeFont = self.labelDateTime.font()
        dateTimeFont.setPointSize(max(9, min(12, int(height * 0.014))))
        self.labelDateTime.setFont(dateTimeFont)
        self.headerSeparator.setGeometry(margin, headerHeight, width - 2 * margin, 2)
        self.labelLogo.setPixmap(
            self.logoPixmap.scaled(
                self.labelLogo.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )

        uinY = headerHeight + margin
        self.uinPanel.setGeometry(
            margin + uinLabelWidth + buttonGap,
            uinY,
            uinPanelWidth,
            uinPanelHeight,
        )
        self.labelUin.setGeometry(
            margin,
            uinY,
            uinLabelWidth,
            uinPanelHeight,
        )
        self.labelUinValue.setGeometry(
            10,
            0,
            uinPanelWidth - 20,
            uinPanelHeight - 2,
        )
        controlsY = uinY + uinPanelHeight + margin
        self.btnConnect.setGeometry(
            width - margin - buttonWidth,
            controlsY,
            buttonWidth,
            rowHeight,
        )
        self.btnRefreshPorts.setGeometry(
            self.btnConnect.geometry().left() - buttonGap - refreshButtonWidth,
            controlsY,
            refreshButtonWidth,
            rowHeight,
        )
        self.comboBoxComPort.setGeometry(
            margin,
            controlsY,
            self.btnRefreshPorts.geometry().left() - margin - buttonGap,
            rowHeight,
        )
        controlsFont = self.comboBoxComPort.font()
        controlsFont.setPointSize(10)
        self.comboBoxComPort.setFont(controlsFont)
        self.btnConnect.setFont(controlsFont)
        self.btnRefreshPorts.setFont(controlsFont)
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

    def updateDateTime(self):
        currentTime = QtCore.QDateTime.currentDateTime()
        self.labelDateTime.setText(
            '{}\n    {} \n  '.format(
                currentTime.toString('dd MMM yyyy'),
                currentTime.toString('hh:mm:ss AP'),
            )
        )

    def updateUin(self, uin):
        self.labelUinValue.setText(uin)

    def refreshPorts(self):
        selectedPort = self.comboBoxComPort.currentText().split(':', 1)[0].strip()
        availablePorts = list(ports.comports())
        self.comboBoxComPort.clear()
        self.comboBoxComPort.addItem('Select Serial Port...')

        selectedIndex = 0
        for port in availablePorts:
            self.comboBoxComPort.addItem(
                '{}: {}'.format(port.device, port.description)
            )
            if port.device == selectedPort:
                selectedIndex = self.comboBoxComPort.count() - 1

        self.comboBoxComPort.setCurrentIndex(selectedIndex)
        self.logAppend('Serial ports refreshed. Found {} port(s).'.format(len(availablePorts)))

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
        self.btnRefreshPorts.setEnabled(False)
        self.btnConnect.setEnabled(False)
        self.btnConnect.setText('Connected')
        self.logAppend('Connected to {}. Starting device check and certificate flow...'.format(portName))

    def resetForNextCycle(self):
        self.log.clear()
        self.comboBoxComPort.setEnabled(True)
        self.btnRefreshPorts.setEnabled(True)
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
