import sys
import os
import csv

from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPen, QPainter
from PyQt5.QtCore import QUrl, Qt, QRect
from PyQt5.QtGui import QColor


class App(QMainWindow):

	def __init__(self):
		super().__init__()
		self.title = 'Colour Palette Picker'
		self.left = 100
		self.top = 100
		self.width = 400
		self.height = 300

		self.colours = []
		self.filename = ""

		self.initUI()

	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		oldPalette = QMessageBox.question(self, "Open previous palette?", "Open previous palette?")

		if oldPalette != 65536:
			self.filename = QFileDialog.getOpenFileUrl(self, "Which colour palette do you want to open?", QUrl(os.getcwd()), "*.csv")
			data = open(self.filename[0].toLocalFile())
			reader = csv.reader(data, delimiter=" ")
			for row in reader:
				self.colours.append(QColor(int(row[0]), int(row[1]), int(row[2])))

		button = QPushButton('Add New', self)
		button.move(150, 150)
		button.clicked.connect(self.on_new_colour_click)

		self.show()

	def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
		painter = QPainter(self)
		for i, colour in enumerate(self.colours):
			pen = QPen()
			pen.setWidth(5)

			painter.setPen(pen)
			painter.fillRect(QRect(10 + 30 * (i % 4), 10 + 30 * (i // 4), 20, 15), colour)

	def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
		for i, colour in enumerate(self.colours):
			if QRect(10 + 30 * (i % 4), 10 + 30 * (i // 4), 20, 15).contains(a0.pos()):
				if a0.button() == Qt.LeftButton:
					newColour = QColorDialog.getColor(colour)
					self.colours[i] = newColour
				elif a0.button() == Qt.RightButton:
					self.colours.remove(colour)

				break

		self.update()

	def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
		if self.filename == "":
			if QMessageBox.question(self, "Save palette?", "Save palette?") != 65536:
				self.filename = QFileDialog.getSaveFileUrl(self, "What do you want to save the file as?", QUrl(os.getcwd()), "*.csv")

		if self.filename != "":
			csvfile = open(self.filename[0].toLocalFile(), "w")
			writer = csv.writer(csvfile, delimiter=" ", lineterminator="\n")
			for colour in self.colours:
				writer.writerow([colour.getRgb()[0], colour.getRgb()[1], colour.getRgb()[2]])

	def on_new_colour_click(self):
		self.openColorDialog()

	def openColorDialog(self):
		colour = QColorDialog.getColor()

		if colour.isValid():
			self.colours.append(QColor(colour.getRgb()[0], colour.getRgb()[1], colour.getRgb()[2]))


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())