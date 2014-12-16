#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BLE SMURFS MONITOR
Plot realtime power comsumption of BLE SMURFS
"""

import sys
import serial
from serial.tools import list_ports
import time
from collections import deque
from PySide.QtCore import QThread, Signal, Slot, Qt
from PySide.QtGui import QApplication, QMainWindow, QWidget, QHBoxLayout, QMessageBox, QKeyEvent
import pyqtgraph as pg


class SerialThread(QThread):
    data = Signal(int)
    error = Signal(int)
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exit = False
        
    def run(self):
        print('--- serial thread started ---')
        port = None
        for p in list_ports.comports():
            print(p)
            if p[2].upper().startswith('USB VID:PID=0D28:0204'):
                port = p[0]
                break
                
        if port == None:
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
        while self.exit == False:
            try:
                line = device.readline()
                self.data.emit(int(line))
            except IOError as e:
                print('io error')
                self.error.emit(2)
                break
            except ValueError as e:
                self.error.emit(3)
                break
                
        device.close()
        print('--- serial thread finished')

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle('BLE SMURFS MONITOR')
        self.resize(800, 500)
        cwidget = QWidget()
        self.setCentralWidget(cwidget)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        cwidget.setLayout(layout)
        self.pwidget = pg.PlotWidget()
        layout.addWidget(self.pwidget)
        
        self.pwidget.setTitle(title="press 'space' to freeze/resume")
        self.pwidget.setLabel('left', 'I', units='mA')
        self.pwidget.setLabel('bottom', 't', units='s')
        self.pwidget.showButtons()
        self.pwidget.setXRange(0, 60)
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
        self.thread.error.connect(self.onError)
        self.thread.data.connect(self.update)
        self.thread.start()
        self.start_time = time.time()
        self.x = deque(maxlen=8196)
        self.y = deque(maxlen=8196)
        self.freeze = False
        
    @Slot(int)
    def onError(self, error):
        flags = QMessageBox.Abort | QMessageBox.StandardButton.Retry
        message = 'No device available!'
        if error > 1:
            message = 'Failed to read data!'
            
        result = QMessageBox.critical(self, 'ERROR', message, flags)
        if result == QMessageBox.StandardButton.Retry:
            self.thread.start()
        else:
            self.close()
        
    @Slot(int)
    def update(self, data):
        t = time.time() - self.start_time
        data = data / 1000.0
        print('%f: %f' % (t, data))
        self.x.append(t)
        self.y.append(data)
        
        if not self.freeze:
            range = self.pwidget.viewRange()
            if t >= range[0][1]:
                self.pwidget.setXRange(t, t + range[0][1] - range[0][0])
            self.plot.setData(x=list(self.x), y=list(self.y))
        
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.pwidget.setXRange(self.x[0], self.x[len(self.x) - 1] + 8)
            self.pwidget.enableAutoRange(axis=pg.ViewBox.YAxis)
        elif key == Qt.Key_Space:
            self.freeze = not self.freeze
            
        return True
        
    def closeEvent(self, event):
        if self.thread.isRunning():
            self.thread.exit = True;
            while self.thread.isRunning():
                pass

        event.accept()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
