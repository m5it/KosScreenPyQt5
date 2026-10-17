#!/usr/bin/env python3
"""
KosScreenPyQt5 - A tiny desktop screenshot utility.

Features:
- Capture the whole primary screen.
- Select a region on the screen and create a new cropped image from it.
- Save the captured image (full or cropped) to a file.
- Copy the captured image to the clipboard.
"""

import sys

from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QTimer
from PyQt5.QtGui import QKeySequence, QPixmap, QPainter
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRubberBand,
    QScrollArea,
    QShortcut,
    QVBoxLayout,
    QWidget,
)


class RegionSelector(QDialog):
    """A full-screen overlay used to pick a rectangular region of the screen."""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(
            parent,
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.original_pixmap = pixmap
        self.cropped_pixmap = QPixmap()
        self.selected_rect = QRect()
        self.rubber_band = None
        self.origin = QPoint()

        self.setWindowTitle("Select region")
        self.setGeometry(QApplication.primaryScreen().geometry())
        self.setStyleSheet("background-color: black;")

        # Hint label
        hint = QLabel(
            "Drag to select a region.  Enter = capture  |  Esc = cancel",
            self,
        )
        hint.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 160);"
            "padding: 6px; font-size: 14px;"
        )
        hint.adjustSize()
        hint.move(10, 10)
        hint.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw the screenshot filling the whole overlay.  The source rect is
        # the original pixmap; because the pixmap may have a device pixel ratio
        # (HiDPI), the target rectangle is the screen's logical geometry.
        painter.drawPixmap(self.rect(), self.original_pixmap, self.original_pixmap.rect())
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            if self.rubber_band is None:
                self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self.rubber_band.setGeometry(QRect(self.origin, QSize(0, 0)))
            self.rubber_band.show()
        elif event.button() == Qt.RightButton:
            self.reject()

    def mouseMoveEvent(self, event):
        if self.rubber_band is not None and event.buttons() == Qt.LeftButton:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rubber_band is not None:
            self.selected_rect = self.rubber_band.geometry().normalized()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def accept(self):
        if self.selected_rect.isEmpty():
            QMessageBox.information(self, "No selection", "Please select a region first.")
            return
        # Map overlay coordinates to original pixmap pixel coordinates.
        scale_x = self.original_pixmap.width() / self.width()
        scale_y = self.original_pixmap.height() / self.height()
        x = round(self.selected_rect.x() * scale_x)
        y = round(self.selected_rect.y() * scale_y)
        w = round(self.selected_rect.width() * scale_x)
        h = round(self.selected_rect.height() * scale_y)
        crop_rect = QRect(x, y, w, h)
        self.cropped_pixmap = self.original_pixmap.copy(crop_rect)
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_pixmap = QPixmap()
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        self.setWindowTitle("KosScreen")
        self.setMinimumSize(600, 450)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_full = QPushButton("Capture full screen")
        self.btn_full.setToolTip("Hide the window, take a full-screen screenshot, then show it again")
        self.btn_full.clicked.connect(self.capture_full_screen)
        toolbar.addWidget(self.btn_full)

        self.btn_select = QPushButton("Capture selection")
        self.btn_select.setToolTip("Hide the window, select a region on the screen, then show it again")
        self.btn_select.clicked.connect(self.capture_selection)
        toolbar.addWidget(self.btn_select)

        self.btn_save = QPushButton("Save image")
        self.btn_save.setToolTip("Save the currently displayed image to a file")
        self.btn_save.clicked.connect(self.save_image)
        toolbar.addWidget(self.btn_save)

        self.btn_copy = QPushButton("Copy to clipboard")
        self.btn_copy.setToolTip("Copy the currently displayed image to the clipboard")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        toolbar.addWidget(self.btn_copy)

        self.chk_hide = QCheckBox("Hide window on capture")
        self.chk_hide.setToolTip("When checked, the main window hides while capturing and returns afterwards")
        self.chk_hide.setChecked(True)
        toolbar.addWidget(self.chk_hide)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Image view
        self.image_label = QLabel("No image captured yet")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #2b2b2b; color: #aaaaaa;")

        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        layout.addWidget(scroll, 1)

        # Status bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_image)
        QShortcut(QKeySequence("Ctrl+C"), self, self.copy_to_clipboard)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.capture_selection)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self.capture_full_screen)

    def _primary_screen_pixmap(self) -> QPixmap:
        screen = QApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("No primary screen available")
        return screen.grabWindow(0)

    def _hide_and_capture(self, capture_callback, *, selection=False):
        """Optionally hide the main window, run a capture, then restore the window."""
        hide_window = self.chk_hide.isChecked()
        if hide_window:
            self.hide()
            self.setEnabled(False)
            # Pump the event loop so the hide request is processed immediately.
            QApplication.processEvents()

        def do_capture():
            try:
                if selection:
                    full_pixmap = self._primary_screen_pixmap()
                    if hide_window:
                        self.setEnabled(True)
                    selector = RegionSelector(full_pixmap, self)
                    if selector.exec_() == QDialog.Accepted:
                        self.current_pixmap = selector.cropped_pixmap
                        self._show_current_pixmap()
                        self.status_label.setText(
                            f"Cropped image: {self.current_pixmap.width()}x{self.current_pixmap.height()}"
                        )
                    if hide_window:
                        self.show()
                else:
                    self.current_pixmap = self._primary_screen_pixmap()
                    self._show_current_pixmap()
                    self.status_label.setText(
                        f"Full screen captured: {self.current_pixmap.width()}x{self.current_pixmap.height()}"
                    )
                    if hide_window:
                        self.setEnabled(True)
                        self.show()
                        self.raise_()
                        self.activateWindow()
            except Exception as exc:
                if hide_window:
                    self.setEnabled(True)
                    self.show()
                    self.raise_()
                    self.activateWindow()
                QMessageBox.critical(self, "Error", f"Could not capture screen:\n{exc}")

        if hide_window:
            # Give the window manager a short moment to fully hide the window.
            QTimer.singleShot(300, do_capture)
        else:
            do_capture()

    def capture_full_screen(self):
        self._hide_and_capture(None)

    def capture_selection(self):
        self._hide_and_capture(None, selection=True)

    def _show_current_pixmap(self):
        if self.current_pixmap.isNull():
            self.image_label.setText("No image captured yet")
            self.image_label.setPixmap(QPixmap())
            return
        self.image_label.setPixmap(self.current_pixmap)
        self.image_label.adjustSize()

    def save_image(self):
        if self.current_pixmap.isNull():
            QMessageBox.information(self, "No image", "There is no image to save.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save screenshot",
            "screenshot.png",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;Bitmap Image (*.bmp);;All Files (*)",
        )
        if not path:
            return

        ok = self.current_pixmap.save(path)
        if ok:
            self.status_label.setText(f"Saved to {path}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save image:\n{path}")

    def copy_to_clipboard(self):
        if self.current_pixmap.isNull():
            QMessageBox.information(self, "No image", "There is no image to copy.")
            return
        QApplication.clipboard().setPixmap(self.current_pixmap)
        self.status_label.setText("Image copied to clipboard")


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
