from typing import List, Tuple, Union

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

app = pg.mkQApp("From InfiniteLine Example")
# win = pg.GraphicsLayoutWidget(show=True, title="Plotting items examples")

# Interpret image data as row-major instead of col-major
pg.setConfigOptions(imageAxisOrder='row-major')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Create window with ImageView widget
mw = QtWidgets.QMainWindow()
mw.resize(200, 200)
cw = QtWidgets.QWidget()
mw.setCentralWidget(cw)
l = QtWidgets.QVBoxLayout()
cw.setLayout(l)

imv = pg.ImageView()
l.addWidget(imv)

label = QtWidgets.QLabel("Probe notes")
l.addWidget(label)

g = QtWidgets.QGridLayout()
l.addLayout(g)

data = np.random.normal(size=(200, 200))
imv.setImage(data)
imv.ui.histogram.hide()
imv.ui.roiBtn.hide()
imv.ui.menuBtn.hide()

# TODO fix dangling pointer after remove
# QGraphicsScene::removeItem: item 0x1f0c7168720's scene (0x0) is different from this scene (0x1f0bfa7a490)


def probe_idx2chr_list(probe_idx: Union[int, List]) -> List:
    "convert probe index [0-5] to a character [A-F] - this version accepts and returns lists"
    if probe_idx is int:
        probe_idx = [probe_idx]
    if not all([idx in [*range(6)] for idx in probe_idx]):
        raise ValueError("Probe index must be 0 to 5 (A to F)")
    start_chr_idx = ord("A".upper()) # 65
    probe_chr_idx = np.array(start_chr_idx) + probe_idx
    return [chr(idx) for idx in probe_chr_idx]


def probe_idx2chr(probe_idx: int) -> chr:
    "convert probe index [0-5] to a character [A-F] - this version accepts an int and returns a single chr"
    if not probe_idx in range(6):
        raise ValueError("Probe index must be 0 to 5 (A to F)")
    start_chr_idx = ord("A".upper()) # 65
    probe_chr_idx = start_chr_idx + probe_idx
    return chr(probe_chr_idx)


def probe_chr2idx(probe_chr: chr) -> int:
    "convert probe index [0-5] to a character [A-F] - this version accepts an int and returns a single chr"
    if not probe_chr in probe_idx2chr_list(range(6)):
        raise ValueError("Probe index must be A to F (0 to 5)")
    start_chr_idx = ord("A".upper()) # 65
    probe_idx = ord(probe_chr) - start_chr_idx
    return probe_idx


def add_probe_marker(probe_idx: int = None):
    if probe_idx is None or bool:
        probe_idx = mw.sender().probe_idx
    if probe_marker_list[probe_idx] is None:
        probe_marker_list[probe_idx] = pg.TargetItem(symbol="x")
        probe_marker_list[probe_idx].probe_idx = probe_idx
        probe_marker_list[probe_idx].probe_label = probe_idx2chr(probe_idx)
        set_initial_probe_marker_properties(probe_marker_list[probe_idx])
        imv.addItem(probe_marker_list[probe_idx])
        # update_probe_button(probe_button_list[probe_idx])
    else:
        probe_marker_list[probe_idx].setVisible(True)


def remove_probe_marker(probe_idx: int = None):
    if probe_idx is None or bool:
        probe_idx = mw.sender().probe_idx
    # imv.removeItem(probe_marker_list[probe_idx])
    probe_marker_list[probe_idx].setVisible(False)
    # probe_marker_list[probe_idx] = None
    # update_probe_button(probe_button_list[probe_idx])

    # refactor https: // python.hotexamples.com/examples/pyqtgraph/PlotWidget/removeItem/python-plotwidget-removeitem-method-examples.html


def update_on_probe_button_toggle(probe_button):
    if probe_button is None or bool:
        probe_idx = mw.sender().probe_idx
        probe_button = probe_button_list[probe_idx]
    if not probe_button.isChecked():
        add_probe_marker(probe_button.probe_idx)
        probe_button.setText(f"Remove {probe_button.probe_label} marker")
        # probe_button.clicked.connect(
        #     remove_probe_marker)
    elif probe_button.isChecked():
        remove_probe_marker(probe_button.probe_idx)
        probe_button.setText(f"Add {probe_button.probe_label} marker")
        # probe_button.clicked.connect(
        #     add_probe_marker)


def set_initial_probe_marker_properties(probe_marker):
    probe_marker.setPos(
        get_probe_marker_start_pos_on_img(
            [imv.getImageItem().width(), imv.getImageItem().height()], probe_marker.probe_idx))
    # probe_marker.size = 10
    # probe_marker.setSymbol("x")
    probe_marker.setPen("#FF4444")
    probe_marker.setBrush("#FF4444", opacity=.5)
    probe_marker.setHoverBrush("#FFFFFF", opacity=0)
    probe_marker.setLabel(probe_marker.probe_label, {
        "anchor": QtCore.QPointF(0.5, 0.5),
        "offset": QtCore.QPointF(0, -10),
        "color": "#FF4444",
        "rotateAxis": (0, 0)
    })


def get_probe_marker_start_pos_on_img(parent_img_dim, probe_idx) -> Tuple:
    im_center = np.array([0.5 * parent_img_dim[0], 0.5 * parent_img_dim[1]])
    x, y = (im_center + np.array([
        min(im_center) * np.cos((probe_idx-1) * 2 * np.pi / 6),
        min(im_center) * np.sin((probe_idx-1) * 2 * np.pi / 6)
    ]))                                                         # x,y: 0,0 top left
    return (x, y)


probe_notes_list = []
probe_button_list = []
probe_marker_list = [None] * 6
for probe_idx, probe_label in enumerate(["A", "B", "C", "D", "E", "F"]):

    probe_notes_list.append(QtWidgets.QLineEdit(placeholderText=f"Notes on probe {probe_label}"))
    probe_notes_list[probe_idx].probe_idx = probe_idx
    probe_notes_list[probe_idx].probe_label = probe_label

    g.addWidget(probe_notes_list[probe_idx], probe_idx, 0)

    probe_button_list.append(QtWidgets.QPushButton())
    probe_button_list[probe_idx].probe_idx = probe_idx
    probe_button_list[probe_idx].probe_label = probe_label
    probe_button_list[probe_idx].setCheckable(True)
    # probe_button_list[probe_idx].isChecked(False)
    probe_button_list[probe_idx].toggled.connect(update_on_probe_button_toggle)

    g.addWidget(probe_button_list[probe_idx], probe_idx, 1)

mw.show()

# Create a plot with some random data
# p1 = win.addPlot(title="Plot Items example",
#                  y=np.random.normal(size=100, scale=10), pen=0.5)
# p1.setYRange(-40, 40)

if __name__ == '__main__':
    pg.exec()
