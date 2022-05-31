import datetime
import os
import pathlib
import sys
import time

import numpy as np

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    from PyQt5 import QtCore, QtGui, QtWidgets

import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets


class FolderModel(QtWidgets.QFileSystemModel):

    def __init__(self, parent=None, *args, **kwargs):
        # * the QFileSystemModel has a rootPath that indicates the root
        # from where the files will be monitored *and the views have a rootIndex that tells them which part of the model to show.

        super().__init__(parent=parent, *args, **kwargs)
        self.setRootPath("c:/") # todo move outside to config
        self.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)

        #! move this to folder proxyfilter


class FileModel(QtWidgets.QFileSystemModel):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.setFilter(QtCore.QDir.Files | QtCore.QDir.NoDotAndDotDot)
        # TODO fix behavior: first click on folder shows files only - entering folder, leaving and re-clicking reveals directories


class FolderFilterProxyModel(QtCore.QSortFilterProxyModel):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.setSourceModel(FolderModel()) # todo move to controller

        session_reg_exp = "[0-9]{0,10}_[0-9]{0,6}_[0-9]{0,8}"
        # self.setFilterRegularExpression(QtCore.QRegularExpression(session_reg_exp))
        # self.setFilterRegularExpression(session_reg_exp)
        self.setFilterKeyColumn(0)
        # auto applies filtering/sorting if source model changes
        self.setDynamicSortFilter(True)
        self.setRecursiveFilteringEnabled(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)


class FileFilterProxyModel(QtCore.QSortFilterProxyModel):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.setSourceModel(FileModel()) # todo move to controller
        self.setSourceModel(FileModel()) # todo move to controller


class FolderTreeView(QtWidgets.QTreeView):

    def __init__(self, parent=None, label=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs) # t
        self.label = "folder tree viewer"

        self.expandToDepth(3)

        # todo move some of this to controller
        self.proxy = FolderFilterProxyModel()
        self.setModel(self.proxy)
        self.source = self.proxy.sourceModel()

        root_idx = self.source.index(self.source.rootPath())
        proxy_root_idx = self.proxy.mapFromSource(root_idx)
        self.setRootIndex(proxy_root_idx)

        self.setRootIsDecorated(True)
        self.setUniformRowHeights(True) # this enables the view to do some optimizations

        self.clipboard = QtGui.QGuiApplication.clipboard()
        self.doubleClicked.connect(self.open_folder)

    def selected_file_path(self, proxy_index):
        file_index = self.proxy.mapToSource(proxy_index)
        return pathlib.Path(self.source.filePath(file_index))

    def copy_path_to_clipboard(self, proxy_index):
        path = self.selected_file_path(proxy_index)
        self.clipboard.setText(str(path))

    def open_folder(self, proxy_index):
        path = self.selected_file_path(proxy_index)
        folder = path.absolute() if path.is_dir() else path.parent.absolute()
        os.startfile(folder)


class FolderSearchView(QtWidgets.QMainWindow):

    def __init__(self, parent=None, label=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.label = "search/fileview/folderview"

        self.add_widgets()

    def add_widgets(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.FolderContentsView = item = FolderContentsView(parent=self)
        item.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(item, stretch=0)

        self.LineEdit = item = QtWidgets.QLineEdit(placeholderText="Enter mouseID", parent=self)
        layout.addWidget(item)

        self.FolderTreeView = item = FolderTreeView(parent=self)
        item.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(item, stretch=1)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.FolderTreeView.selectionModel().selectionChanged.connect(self.updateFiles)

    def updateFiles(self, selected, deselected):
        # we've filtered for only folders, so apply a selection to a separate filemodel for display
        if len(selected) > 1:
            proxyIndex = self.FolderTreeView.selectedIndexes()
        else:
            proxyIndex = self.FolderTreeView.currentIndex()

        folderproxy = self.FolderTreeView.proxy
        foldersource = self.FolderTreeView.source

        sourceSelection = folderproxy.mapSelectionToSource(selected)
        sourceIndex = folderproxy.mapToSource(proxyIndex)

        fileproxy = self.FolderContentsView.proxy
        filesource = self.FolderContentsView.source

        #! for s in selection:
        path = foldersource.fileInfo(sourceIndex).absoluteFilePath()

        # root_idx = self.source.index(self.source.rootPath())
        # proxy_root_idx = self.proxy.mapFromSource(root_idx)
        # self.setRootIndex(proxy_root_idx)

        r = filesource.setRootPath(path)
        self.FolderContentsView.setRootIndex(fileproxy.mapFromSource(r))

        # path = self.dirModel.fileInfo(index).absoluteFilePath()
        # self.listview.setRootIndex(self.fileModel.setRootPath(path))


class FolderContentsView(QtWidgets.QListView):

    def __init__(self, parent=None, label=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.label = "folder contents viewer"
        self.model = FileFilterProxyModel()
        self.setModel(self.model) # todo move to controller

        # this enables the view to do some optimizations:
        self.setUniformItemSizes(True)

        # todo move some of this to controller
        self.proxy = FileFilterProxyModel()
        self.setModel(self.proxy)
        self.source = self.proxy.sourceModel()


class ProbeLocationViewer(pg.ImageView):

    def __init__(self, parent=None, label=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.label = "probe location viewer"
        #! temp
        self.setImage(np.random.normal(size=(100, 100)))
        self.ui.histogram.hide()
        self.ui.menuBtn.hide()
        self.ui.roiBtn.hide()


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None, label=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.title = "gui with docked modules"

        # self.MainLayout = pg.LayoutWidget()
        self.resize(1000, 500)
        self.default_docked_widget_list = [
            FolderSearchView(),
            ProbeLocationViewer(),
        ]

    def add_docked_widgets(self, docked_widget_list=None):
        if self.default_docked_widget_list and not docked_widget_list:
            docked_widget_list = self.default_docked_widget_list

        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.dock = []
        for dock in docked_widget_list:
            label = dock.label if hasattr(dock, "label") else ""
            label = "<drag to move> <double-click to undock>"
            self.dock.append(item := Dock(label, size=(200, 200), closable=False))
            self.area.addDock(item, "left")
            item.addWidget(dock)
            ## Test ability to move docks programatically after they have been placed
            if self.dock:
                self.area.moveDock(item, "right", self.dock[-1])


if __name__ == "__main__":
    app = pg.mkQApp("docked widget GUI")
    win = MainWindow()
    win.add_docked_widgets([]) # FolderTreeView()

    # app.exec()
    win.show()
    sys.exit(pg.exec())
