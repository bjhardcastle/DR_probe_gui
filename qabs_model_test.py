# try:
#     from PySide6 import QtGui, QtCore, QtWidgets
# except:
from PyQt5 import QtGui, QtCore, QtWidgets
from pathlib import PureWindowsPath, Path, PurePath
import os
from datetime import timedelta
from time import time

root_pathlist = [
    # PureWindowsPath(r"\\allen\programs\mindscope\workgroups\np-exp"),
    PureWindowsPath(r"\\W10DTSM112719\neuropixels_data"),
    PureWindowsPath(r"\\W10DTSM18306\neuropixels_data"),
    # PureWindowsPath(r"C:\Users\ben.hardcastle"),
    PureWindowsPath(
        r"\\allen\programs\braintv\workgroups\nc-ophys\corbettb\NP_behavior_pipeline\QC"),
    PureWindowsPath(r"\\allen\programs"),
    PureWindowsPath(r"\\W10DT05515\A"),
    PureWindowsPath(r"\\W10DT05515\B"),
    PureWindowsPath(r"\\W10DT05515\P"),
    PureWindowsPath(r"\\W10DT05501\A"),
    PureWindowsPath(r"\\W10DT05501\B"),
    PureWindowsPath(r"\\W10dt05501\j"),
    PureWindowsPath(r"\\W10DT9I8QD3D\extraction"),
    PureWindowsPath(r"\\W10DTSM112721"),
    PureWindowsPath(r"\\allen\programs\mindscope\production"),
    PureWindowsPath(r"\\allen\programs\braintv\production"),
    PureWindowsPath(r"\\allen\programs\mindscope\workgroups\np-exp")
]

tempDir = QtCore.QTemporaryDir(os.path.join(QtCore.QDir.tempPath(), "X"*16))
tempDirPathObj = Path(tempDir.path())

for path in root_pathlist:
    tf = QtCore.QFile.link(str(path), str(
        tempDirPathObj / (str(path).replace("\\\\", "").replace("\\", "_").replace(":", "") + ".lnk")))

app = QtWidgets.QApplication([])

fileModel = QtWidgets.QFileSystemModel()
fileModel.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
# fileModel.setRootPath(QtCore.QDir.currentPath())
# fileModel.setRootPath()
# fileModel.setRootPath(root_path)
# doc_directory = QtCore.QStandardPaths.writableLocation(
#     QtCore.QStandardPaths.DocumentsLocation
# )
# root_idx = fileModel.index(doc_directory)

proxyModel = QtCore.QSortFilterProxyModel()
proxyModel.setSourceModel(fileModel)
# proxyModel.isSortLocaleAware()
# self.searchBox = QLineEdit(centralWidget)
session_reg_exp = "[0-9]{0,10}_[0-9]{0,6}_[0-9]{0,8}"
reg_exp = session_reg_exp
# proxyModel.setFilterRegularExpression(QtCore.QRegularExpression(reg_exp))
# proxyModel.setFilterRegularExpression(reg_exp)

proxyModel.setFilterKeyColumn(0)
# proxyModel.setFilterFixedString("1234567890_123456_12345678")
# auto applies filtering/sorting if source model changes
proxyModel.setDynamicSortFilter(True)
proxyModel.setRecursiveFilteringEnabled(True)
proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
# proxyModel.setFilterFixedString("A")

# proxyModel.setFilterWildcard("*123456*")
# proxyModel.setFilterFixedString("1234567890_123456_12345678")
# proxyModel.setFilterRegExp("1234567890_123456_12345678")
# proxyModel.filterRegularExpression()
# proxyModel.filterRegExp()
# layout = QtWidgets.QVBoxLayout()

#TODO add better expanding (See https://stackoverflow.com/questions/56781145/expand-specific-items-in-a-treeview-during-filtering)

treeView = QtWidgets.QTreeView()
treeView.setModel(proxyModel)
treeView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
# this enables the view to do some optimizations
treeView.setUniformRowHeights(True)
treeView.setFixedSize(1200, 800)

clipboard = QtGui.QGuiApplication.clipboard()


def copyPathToClipboard(proxyIndex):
    fileIndex = proxyModel.mapToSource(proxyIndex)
    filePath = Path(fileModel.filePath(fileIndex))
    clipboard.setText(str(filePath))


def openContainingFolder(proxyIndex):
    fileIndex = proxyModel.mapToSource(proxyIndex)
    filePath = Path(fileModel.filePath(fileIndex))
    folder = filePath.absolute() if filePath.is_dir() else filePath.parent.absolute()
    os.startfile(folder)


treeView.clicked.connect(copyPathToClipboard)
treeView.doubleClicked.connect(openContainingFolder)

filterStr = QtWidgets.QLineEdit(placeholderText="Enter mouseID")

# TODO - allow filtering for any string within session id match (filter with pattern first, then filter results with lookaround?)

lastUpdateTime = time()


def setViewFilter(input_text):
    global lastUpdateTime
    treeView.expandToDepth(3)
    if len(input_text) == 6:  # full mouseID
        rePattern = f"[0-9]{{0,10}}_{input_text}_[0-9]{{0,8}}"
    else:
        rePattern = input_text

    sinceLastUpdate = timedelta(seconds=(time()-lastUpdateTime)).seconds
    if sinceLastUpdate > 0:
        # treeView.collapseAll()
        proxyModel.setFilterRegularExpression("")
        lastUpdateTime = time()
    proxyModel.setFilterRegularExpression(rePattern)
    updateTreeView()


def expandTreeView():
    global lastUpdateTime
    sinceLastUpdate = timedelta(seconds=(time()-lastUpdateTime)).seconds
    if sinceLastUpdate > 2:
        # treeView.expandAll()
        # treeView.expandToDepth(4)
        # treeView.collapseAll()
        lastUpdateTime = time()


def updateTreeView():
    # global lastUpdateTime
    treeView.resizeColumnToContents(0)
    expandTreeView()
    # sinceLastUpdate = timedelta(seconds=(time()-lastUpdateTime)).seconds
    # if sinceLastUpdate > 0:
    # root_idx = fileModel.index(fileModel.rootPath())
    # proxy_root_idx = proxyModel.mapFromSource(root_idx)
    # treeView.setRootIndex(proxy_root_idx)
    # treeView.expandAll()


proxyModel.dataChanged.connect(updateTreeView)
proxyModel.rowsInserted.connect(updateTreeView)
filterStr.textChanged.connect(setViewFilter)

fileModel.setRootPath(tempDir.path())
root_idx = fileModel.index(fileModel.rootPath())
proxy_root_idx = proxyModel.mapFromSource(root_idx)
treeView.setRootIndex(proxy_root_idx)
treeView.setRootIsDecorated(True)
# treeView.expand(proxy_root_idx)

layout = QtWidgets.QVBoxLayout()
layout.addWidget(filterStr)
layout.addWidget(treeView)
mainWindow = QtWidgets.QWidget()
mainWindow.setLayout(layout)
mainWindow.show()


# treeView.show()

# mouse_id = 366122

# root_idx = fileModel.index(fileModel.rootPath())
# # proxy_root_idx = proxyModel.mapFromSource(root_idx)setViewFilter(input_text)
# treeView.expand(proxy_root_idx)
# treeView.expandAll()
# treeView.collapseAll()
# # proxyModel.setFilterRegularExpression("366122")
# treeView.setItemsExpandable(False)

app.exec()
