from PyQt5 import QtWidgets, QtCore, QtGui
import qrcode
from qrcode.image.pure import PyPNGImage
from random import randrange

qr = qrcode.QRCode(
    version=1,
    box_size=10,
    border=4,
)

qr.add_data('Some data')
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")

class Window(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.label = QtWidgets.QLabel(self)
        # self.edit = QtWidgets.QLineEdit(self)
        # self.edit.returnPressed.connect(self.handleTextEntered)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(img)
        # layout.addWidget(self.edit)

    # def handleTextEntered(self):
    #     text = self.edit.text()#text = unicode(self.edit.text())
    #     self.label.setPixmap(
    #         qrcode.make(text, image_factory=Image()).pixmap())

if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setGeometry(500, 300, 200, 200)
    window.show()
    sys.exit(app.exec_())
