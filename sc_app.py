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
import tempfile

import ui
reload(ui)
import dialog_ui
reload(dialog_ui)
import maya_utils as mu
reload(mu)


from tool.utils import customLog, fileUtils
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

        # table column 
        self.fileTypeCol = 0 
        self.fileNameCol = 1 
        self.statusCol = 2
        self.noCol = 3
        self.sourcePathCol = 4
        self.copyDstCol = 5

        # list dir 
        self.user = os.environ.get('USERNAME')
        self.tmpDir = 'P:/Outsource/tmp/%s' % self.user
        self.listFile = '%s/%s_list.yml' % (self.tmpDir, self.user)


        # icons
        self.iconDir = '%s/icons'% os.path.dirname(moduleDir).replace('\\', '/')
        self.mayaIcon = '%s/%s' % (self.iconDir, 'maya_icon.png')
        self.textureIcon = '%s/%s' % (self.iconDir, 'texture_icon.png')
        self.alembicIcon = '%s/%s' % (self.iconDir, 'alembic_icon.png')

        self.okIcon = '%s/%s' % (self.iconDir, 'ok_icon.png')
        self.rdyIcon = '%s/%s' % (self.iconDir, 'rdy_icon.png')
        self.ipIcon = '%s/%s' % (self.iconDir, 'ip_icon.png')
        self.redIcon = '%s/%s' % (self.iconDir, 'red2_icon.png')



        # data 
        self.dstPath = str()
        self.shotList = []
        self.assetDict = dict()
        self.textureDict = dict()
        self.assemblyDict = dict()
        self.data = dict()

        self.initSignals()
        self.initFunctions()


    def initSignals(self) : 
        self.ui.addShot_lineEdit.returnPressed.connect(self.addShot)
        self.ui.loadMultipleShot_pushButton.clicked.connect(self.doAddMultipleShot)
        self.ui.loadAsset_pushButton.clicked.connect(self.doLoadAsset)
        self.ui.copy_pushButton.clicked.connect(self.doCopy)
        self.ui.checkPath_pushButton.clicked.connect(self.checkFile)
        self.ui.dst_lineEdit.textChanged.connect(self.checkFile)
        self.ui.loadShot_pushButton.clicked.connect(self.loadList)
        self.ui.removeList_pushButton.clicked.connect(self.removeList)


    def initFunctions(self) : 
        pass
        # self.loadList()


    def resizeColumn(self) : 
        self.ui.asset_tableWidget.resizeColumnToContents(self.fileNameCol)
        self.ui.asset_tableWidget.resizeColumnToContents(self.fileTypeCol)
        self.ui.asset_tableWidget.resizeColumnToContents(self.noCol)


    def loadList(self) : 
        if os.path.exists(self.listFile) : 
            data = fileUtils.ymlLoader(self.listFile)

            if data : 
                self.data = data
                self.shotList = data['shot']
                self.assetDict = data['asset']
                self.assemblyDict = data['assembly']
                self.dstPath = data['dstPath']
                self.textureDict = data['texture']

                self.loadShotList()
                self.setDisplayAssetTable()

    def removeList(self) : 
        items = self.ui.shot_listWidget.selectedItems()

        for item in items : 
            row = self.ui.shot_listWidget.row(item)
            self.ui.shot_listWidget.takeItem(row)

        self.saveList()
        # self.loadList()


    def addShot(self, strInput=None, multiMode=False) : 
        if not strInput : 
            strInput = str(self.ui.addShot_lineEdit.text()).replace('\\', '/').replace('"', '').replace(' ', '')

        self.ui.addShot_lineEdit.clear()
        listWidget = 'shot_listWidget'
        color = [200, 200, 200]
        allItems = self.getAllWidgetItem(listWidget)

        if strInput : 
            if os.path.exists(strInput) : 
                if not strInput in allItems : 
                    self.addListWidgetItem(listWidget, strInput, self.mayaIcon, color)
                    return 1

                else : 
                    if not multiMode : 
                        self.messageBox('Warning', 'File exists in the list')

                    else : 
                        return 2

            else : 
                if not multiMode : 
                    self.messageBox('Warning', 'File not exists. Please check path')

                else : 
                    return 0

            print strInput


    def loadShotList(self) : 
        shots = self.data['shot']
        dstPath = self.data['dstPath']
        
        for shot in shots : 
            self.addListWidgetItem('shot_listWidget', shot, self.mayaIcon, '')

        self.ui.dst_lineEdit.setText(dstPath)


    def doAddMultipleShot(self) : 
        dialog = MultipleListDialog()
        result = dialog.exec_()
        content = dialog.content()
        notExists = []
        duplicated = []
        
        if content : 
            lines = content.split('\n')
            lines = [a.strip() for a in lines]

            for line in lines : 
                addStr = line.replace('\\', '/').replace('"', '')
                result = self.addShot(strInput=addStr, multiMode=True)

                if result == 0 : 
                    notExists.append(addStr)

                if result == 2 : 
                    duplicated.append(addStr)

        if notExists : 
            self.messageBox('Warning', '%s files not exists' % len(notExists))

        if duplicated : 
            self.messageBox('Warning', '%s files already on the list' % len(duplicated))


    def doLoadAsset(self) : 
        sels = self.getShotList()

        if sels : 
            self.collectData()
            self.setDisplayAssetTable()

            if self.ui.autoCopy_checkBox.isChecked() : 
                self.doCopy(True)

        else : 
            self.messageBox('Error', 'Select atlease one shot')



    def doCopy(self, autoCopy = False) : 
        dst = str(self.ui.dst_lineEdit.text()).replace('\\', '/')
        counts = self.getSelectedRow(autoCopy)
        data = []

        if dst : 
            for i in xrange(counts[0], counts[1]) : 
                item = self.ui.asset_tableWidget.item(i, self.sourcePathCol)
                
                if item : 
                    srcPath = str(item.text())
                    drive = os.path.splitdrive(srcPath)[0]
                    dstPath = srcPath.replace(drive, dst)

                    statusItem = self.ui.asset_tableWidget.item(i, self.statusCol)
                    dstItem = self.ui.asset_tableWidget.item(i, self.copyDstCol)

                    if os.path.exists(dstPath) : 
                        # statusItem.setText('OK')
                        self.setItemIcon(statusItem, i, self.statusCol, self.okIcon, 'OK')

                    else : 
                        print 'Copying %s ...' % dstPath
                        self.setItemIcon(statusItem, i, self.statusCol, self.ipIcon, 'Copying ...')
                        
                        try : 
                            result = fileUtils.copy(srcPath, dstPath)

                            if os.path.exists(dstPath) : 
                                # statusItem.setText('OK')
                                self.setItemIcon(statusItem, i, self.statusCol, self.okIcon, 'OK')
                                dstItem.setText(dstPath)

                                QtGui.QApplication.processEvents()

                        except Exception as e : 
                            self.setItemIcon(statusItem, i, self.statusCol, self.redIcon, 'Error')
                            dstItem.setText(dstPath)

                            QtGui.QApplication.processEvents()

    def setDisplayAssetTable(self) : 
        shots = self.data['shot']
        assets = self.data['asset']
        assemblys = self.data['assembly']
        textures = self.data['texture']

        info = 'Shot (%s) Asset (%s) Texture (%s) Assembly (%s)' % (len(shots), len(assets), len(textures), len(assemblys))
        self.ui.info_label.setText(info)

        widget = 'asset_tableWidget'
        self.clearTable(widget)

        row = 0

        for shot in shots : 
            fileType = 'Shot'
            fileName = os.path.basename(shot)
            status = ''
            path = shot
            copyDst = ''
            color = ''
            no = 1
            
            self.addTableData(row, fileType, fileName, status, str(no), path, copyDst, color)

            row += 1

        for asset in assets : 
            fileType = self.getFileType(asset)
            fileName = os.path.basename(asset)
            status = ''
            path = asset
            copyDst = ''
            color = ''
            no = len(assets[asset])
            
            self.addTableData(row, fileType, fileName, status, str(no), path, copyDst, color)

            row += 1


        for assembly in assemblys : 
            fileType = self.getFileType(assembly)
            fileName = os.path.basename(assembly)
            status = ''
            path = assembly
            copyDst = ''
            color = ''
            no = len(assemblys[assembly])
            
            self.addTableData(row, fileType, fileName, status, str(no), path, copyDst, color)

            row += 1


        for texture in textures : 
            fileType = self.getFileType(texture)
            fileName = os.path.basename(texture)
            status = ''
            path = texture
            copyDst = ''
            color = ''
            no = len(textures[texture])
            
            self.addTableData(row, fileType, fileName, status, str(no), path, copyDst, color)

            row += 1

        self.checkFile()
        self.resizeColumn()


    def checkFile(self) : 
        widget = 'asset_tableWidget'
        dst = str(self.ui.dst_lineEdit.text()).replace('\\', '/')
        counts = self.ui.asset_tableWidget.rowCount()
        data = []

        if dst : 
            for i in range(counts) : 
                item = self.ui.asset_tableWidget.item(i, self.sourcePathCol)
                
                if item : 
                    path = str(item.text())
                    drive = os.path.splitdrive(path)[0]
                    dstPath = path.replace(drive, dst)
                    targetItem = self.ui.asset_tableWidget.item(i, self.statusCol)

                    if os.path.exists(dstPath) : 
                        # targetItem.setText('OK')
                        self.setItemIcon(targetItem, i, self.sourcePathCol, self.okIcon, 'OK')

                    else : 
                        # targetItem.setText('Not copy')
                        self.setItemIcon(targetItem, i, self.sourcePathCol, self.rdyIcon, 'Not copy')

            # save dst path 
            self.dstPath = dst
            self.data['dstPath'] = self.dstPath



    def collectData(self) : 
        sels = self.getShotList()
        widget = 'asset_tableWidget'
        row = 0 
        height = 20
        color = [255, 255, 255]
        
        if sels : 

            for each in sels : 
                shot = str(each)
                data = mu.getMayaSceneAssetAssembly(shot)
                files = data['files']
                assemblyFiles = data['assemblyFiles']

                if not shot in self.shotList : 
                    self.shotList.append(shot)

                for eachFile in files : 
                    if not eachFile == shot : 
                        fileType = self.getFileType(eachFile)

                        if fileType == 'Maya' : 
                            if not eachFile in self.assetDict.keys() : 
                                self.assetDict.update({str(eachFile): [shot]})

                            else : 
                                if not shot in self.assetDict[eachFile] : 
                                    self.assetDict[eachFile].append(shot)

                        else : 
                            if not eachFile in self.textureDict.keys() : 
                                self.textureDict.update({str(eachFile): [shot]})

                            else : 
                                if not shot in self.textureDict[eachFile] : 
                                    self.textureDict[eachFile].append(shot)

 
                if self.ui.assembly_checkBox.isChecked() : 
                    for eachFile in assemblyFiles : 
                        fileStatus = eachFile[1]
                        assemblyFile = eachFile[0]

                        if fileStatus : 
                            if not assemblyFile in self.assemblyDict.keys() : 
                                self.assemblyDict.update({str(assemblyFile): [shot]})

                            else : 
                                if not shot in self.assemblyDict[assemblyFile] : 
                                    self.assemblyDict[assemblyFile].append(shot)

            self.data = {'shot': self.shotList, 'asset': self.assetDict, 'assembly': self.assemblyDict, 'texture': self.textureDict, 'dstPath': self.dstPath}
            self.saveList()


    def saveList(self) : 
        
        if self.ui.autoSave_checkBox.isChecked() : 
            dirname = os.path.dirname(self.listFile) 

            if not os.path.exists(dirname) : 
                os.makedirs(dirname)

            result = fileUtils.ymlDumper(self.listFile, self.data)
            print 'Save list'



    def getSelectedRow(self, allRow = False) : 
        if allRow : 
            counts = self.ui.asset_tableWidget.rowCount()

            allRows = [0, counts + 1]
            return allRows

        else : 
            if self.ui.allShot_checkBox.isChecked() : 
                counts = self.ui.asset_tableWidget.rowCount()

                allRows = [0, counts + 1]
                return allRows

            else : 
                lists = self.ui.asset_tableWidget.selectedRanges()

                if lists : 
                    topRow = lists[0].topRow()
                    bottomRow = lists[0].bottomRow()

                    selectedRows = [topRow, bottomRow + 1]
                    return selectedRows

        




        # self.resizeColumn()

     #    getMayaSceneAssetAssemblyFiles = data['assemblyFiles']
     # P:/Lego_Pipeline/film/assembly/q0010/all/layout/scenes/work/ppl_asm_q0010_all_layout_v002_TA.ma

    def addTableData(self, row, fileType, fileName, status, no, srcPath, copyDst, color) : 
        height = 20
        widget = 'asset_tableWidget'
        iconPath = self.getIcon(fileName)
        self.insertRow(row, height, widget)
        self.fillInTable(row, self.fileTypeCol, fileType, widget, color)
        self.fillInTableIcon(row, self.fileNameCol, fileName, iconPath, widget, color)
        self.fillInTable(row, self.statusCol, status, widget, color)
        self.fillInTable(row, self.noCol, no, widget, color)
        self.fillInTable(row, self.sourcePathCol, srcPath, widget, color)
        self.fillInTable(row, self.copyDstCol, copyDst, widget, color)


    def getFileType(self, fileName) : 
        extMap = {'Maya': ['ma', 'mb'], 'Alembic': ['abc'], 'Texture': ['jpg', 'png', 'tif']}
        ext = fileName.split('.')[-1]
        fileType = str()

        for each in extMap : 
            exts = extMap[each]

            if ext in exts : 
                fileType = each

        if not fileType : 
            fileType = 'Unknown'

        return fileType


    def getIcon(self, fileName) : 
        iconMap = {'Maya': self.mayaIcon, 'Texture': self.textureIcon, 'Alembic': self.mayaIcon, 'Unknown': self.mayaIcon}
        result = self.getFileType(fileName)

        iconPath = iconMap[result]
        return iconPath


    def getShotList(self) : 
        sels = self.ui.shot_listWidget.selectedItems()

        if sels : 
            items = [str(a.text()) for a in sels]
            return items

        # return 'P:/Lego_Pipeline/film/assembly/q0010/all/layout/scenes/work/ppl_asm_q0010_all_layout_v002_TA.ma'

    def getAllWidgetItem(self, listWidget) : 
        cmd = 'self.ui.%s.count()' % (listWidget)
        count = int(eval(cmd))
        allItems = []

        for i in range(count) : 
            tmpCmd = 'self.ui.%s.item(%s).text()' % (listWidget, i)
            item = str(eval(tmpCmd))
            allItems.append(item)

        return allItems


    def addListWidgetItem(self, listWidget, text, iconPath, color) : 
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
        cmd = 'QtGui.QListWidgetItem(self.ui.%s)' % listWidget
        item = eval(cmd)
        item.setIcon(icon)
        item.setText(text)
        # item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
        size = 90

        cmd2 = 'self.ui.%s.setIconSize(QtCore.QSize(%s, %s))' % (listWidget, size, size)
        eval(cmd2)



    # widget area

    def insertRow(self, row, height, widget) : 
        cmd1 = 'self.ui.%s.insertRow(row)' % widget
        cmd2 = 'self.ui.%s.setRowHeight(row, height)' % widget

        eval(cmd1)
        eval(cmd2)


    def fillInTable(self, row, column, text, widget, color = [1, 1, 1]) : 
        item = QtGui.QTableWidgetItem()
        item.setText(text)
        # item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
        cmd = 'self.ui.%s.setItem(row, column, item)' % widget
        eval(cmd)

        QtGui.QApplication.processEvents()


    def fillInTableIcon(self, row, column, text, iconPath, widget, color = [1, 1, 1]) : 
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        item = QtGui.QTableWidgetItem()
        item.setText(str(text))
        item.setIcon(icon)
        # item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
        
        cmd = 'self.ui.%s.setItem(row, column, item)' % widget
        eval(cmd)

        QtGui.QApplication.processEvents()


    def setItemIcon(self, item, row, column, iconPath, text) : 
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        item.setText(str(text))
        item.setIcon(icon)
        # item.setBackground(QtGui.QColor(color[0], color[1], color[2]))

        QtGui.QApplication.processEvents()


    def clearTable(self, widget) : 
        cmd = 'self.ui.%s.rowCount()' % widget
        rows = eval(cmd)
        # self.ui.asset_tableWidget.clear()

        for each in range(rows) : 
            cmd2 = 'self.ui.%s.removeRow(0)' % widget
            eval(cmd2)



    def getColumnData(self, widget, column) : 
        counts = eval('self.ui.%s.rowCount()' % widget)
        data = []

        for i in range(counts) : 
            item = eval('self.ui.%s.item(i, column)' % widget)
            if item : 
                data.append(str(item.text()))

        return data 


    def getDataFromSelectedRange(self, widget, columnNumber) : 
        lists = eval('self.ui.%s.selectedRanges()' % widget)

        if lists : 
            topRow = lists[0].topRow()
            bottomRow = lists[0].bottomRow()
            leftColumn = lists[0].leftColumn()
            rightColumn = lists[0].rightColumn()

            items = []

            for i in range(topRow, bottomRow + 1) : 
                item = str(eval('self.ui.%s.item(i, columnNumber).text()' % widget))
                items.append(item)


            return items


    def setDataSelectedRow(self, widget, columnNumber, text) : 
        lists = eval('self.ui.%s.selectedRanges()' % widget)

        if lists : 
            topRow = lists[0].topRow()
            bottomRow = lists[0].bottomRow()
            leftColumn = lists[0].leftColumn()
            rightColumn = lists[0].rightColumn()

            items = []

            for i in range(topRow, bottomRow + 1) : 
                item = eval('self.ui.%s.item(i, %s)' % (widget, columnNumber))
                item.setText(text)


    def messageBox(self, title, description) : 
        result = QtGui.QMessageBox.question(self,title,description,QtGui.QMessageBox.Ok)

        return result

    def questionDialog(self, title, description) : 
        result = QtGui.QMessageBox.question(self,title,description,QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)

        return result

class MultipleListDialog(QtGui.QDialog, MyForm):

    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.ui = dialog_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.add_pushButton.clicked.connect(self.closeDialog)


    def content(self) : 
        value = str(self.ui.list_textEdit.toPlainText())

        return value

    def closeDialog(self) : 
        self.close()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())