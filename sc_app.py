#!/usr/bin/env python
# -- coding: utf-8 --

#

import sys, os
sys.path.append('O:/studioTools/lib/pyqt')
sys.path.append('O:/studioTools/maya/python')

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

#Import python modules
import subprocess

import ui
reload(ui)


from tool.utils import customLog
logger = customLog.customLog()
logger.setLevel(customLog.DEBUG)

moduleDir = sys.modules[__name__].__file__

class MyForm(QtGui.QMainWindow):

	def __init__(self, parent=None):
		self.count = 0
		#Setup Window
		super(MyForm, self).__init__(parent)
		self.ui = ui.Ui_AssetCollectorWin()
		self.ui.setupUi(self)

		self.setWindowTitle('Asset Collector v.1.0')

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())