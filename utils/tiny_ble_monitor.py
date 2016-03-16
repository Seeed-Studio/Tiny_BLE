#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BLE SMURFS MONITOR
Plot realtime power comsumption of BLE SMURFS
"""

import sys
import serial
from serial.tools import list_ports
from PySide.QtCore import QThread, Signal, Slot, Qt
from PySide.QtGui import QApplication, QMainWindow, QWidget, QHBoxLayout, QMessageBox, QKeyEvent
import pyqtgraph as pg
import numpy as np

data = np.empty(1000)
data_index = 0

class SerialThread(QThread):
    error = Signal(int)
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exit = False
        
    def run(self):
        global data, data_index

        print('--- serial thread started ---')
        port = None
        for p in list_ports.comports():
            print(p)
            if p[2].upper().startswith('USB VID:PID=0D28:0204') or p[2].upper().startswith('USB VID:PID=D28:204'):
                port = p[0]
                break
                
        if not port:
            print('no device available')
            self.error.emit(1)
            return
            
        print('open %s' % port)
        device = serial.Serial(port=port,
                               baudrate=4000000,
                               bytesize=8,
                               parity='N',
                               stopbits=1,
                               timeout=1)
        while not self.exit:
            try:
                line = device.readline()
                data[data_index] = int(line) / 1000.0  # uA to mA
                data_index += 1
                if data_index >= data.shape[0]:
                    tmp = data
                    data = np.empty(data.shape[0] * 2)
                    data[:tmp.shape[0]] = tmp
            except IOError as e:
                print('io error: %s', e)
                self.error.emit(2)
                break
            except ValueError:
                print('invalid line')
                
        device.close()
        print('--- serial thread finished')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle('Tiny BLE Monitor')
        self.resize(800, 500)
        self.cwidget = QWidget()
        self.setCentralWidget(self.cwidget)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.cwidget.setLayout(layout)
        self.pwidget = pg.PlotWidget()
        layout.addWidget(self.pwidget)
        
        self.pwidget.setTitle(title="press 'space' to freeze/resume")
        self.pwidget.setLabel('left', 'I', units='mA')
        self.pwidget.setLabel('bottom', 't')
        self.pwidget.showButtons()
        self.pwidget.setXRange(0, 3000)
        self.pwidget.setYRange(0, 16)
        # self.pwidget.enableAutoRange(axis=pg.ViewBox.YAxis)
        line = pg.InfiniteLine(pos=1.0, angle=0, movable=True, bounds=[0, 200])
        self.pwidget.addItem(line)
        self.pwidget.showGrid(x=True, y=True, alpha=0.5)
        self.plot = self.pwidget.plot()
        self.plot.setPen((0, 255, 0))
        
        # plotitem = self.pwidget.getPlotItem()
        # plotitem.setLimits(xMin=-1, yMin=-1, minXRange=-1, minYRange=-1) # require pyqtgraph 0.9.9+
        
        self.thread = SerialThread()
        self.thread.error.connect(self.handle_error)
        self.thread.start()
        self.freeze = False
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        
    @Slot(int)
    def handle_error(self, error):
        flags = QMessageBox.Abort | QMessageBox.StandardButton.Retry
        message = 'No device available!'
        if error > 1:
            message = 'Failed to read data!'
            
        result = QMessageBox.critical(self, 'ERROR', message, flags)
        if result == QMessageBox.StandardButton.Retry:
            self.thread.start()
        else:
            self.close()

    def update(self):
        global data, data_index

        if not self.freeze:
            r = self.pwidget.viewRange()
            if data_index >= r[0][1]:
                self.pwidget.setXRange(data_index, data_index + r[0][1] - r[0][0])
            self.plot.setData(data[:data_index])
        
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.pwidget.setXRange(0, data_index + 1000)
            self.pwidget.enableAutoRange(axis=pg.ViewBox.YAxis)
        elif key == Qt.Key_Space:
            self.freeze = not self.freeze
            
        return True
        
    def closeEvent(self, event):
        if self.thread.isRunning():
            self.thread.exit = True
            while self.thread.isRunning():
                pass

        event.accept()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
