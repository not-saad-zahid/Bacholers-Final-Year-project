import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from ui.timetable_ui import TimetableWindow
from ui.datesheet_ui import DatesheetWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Automatic Scheduler for GIGCCL")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)

        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        # Main menu page
        self.menu_page = QWidget()
        menu_layout = QVBoxLayout(self.menu_page)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #2196F3; color: white;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("Automatic Scheduler for GIGCCL")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        menu_layout.addWidget(header)

        # Central content
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add a logo or illustration (optional)
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "icons", "gigccl_logo.png")
        logo_label.setPixmap(QPixmap(logo_path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        central_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Subtitle or welcome message
        subtitle = QLabel("Welcome to the Automatic Scheduler for GIGCCL!")
        subtitle.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        subtitle.setStyleSheet("color: #333; margin-bottom: 18px;")
        central_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Description
        desc = QLabel(
            "This application helps you manage and generate timetables and datesheets for your institution.\n"
            "You can add, edit, and organize class schedules, and export them as PDF or Excel.\n"
            "Get started by choosing an option below."
        )
        desc.setFont(QFont("Arial", 12))
        desc.setStyleSheet("color: #444; margin-bottom: 30px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        central_layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Buttons
        timetable_btn = QPushButton("Open Timetable")
        datesheet_btn = QPushButton("Open Datesheet")
        timetable_btn.setFixedSize(220, 60)
        datesheet_btn.setFixedSize(220, 60)
        timetable_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #2196F3;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        datesheet_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #17a2b8;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        timetable_btn.clicked.connect(self.open_timetable)
        datesheet_btn.clicked.connect(self.open_datesheet)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(30)
        btns_layout.addWidget(timetable_btn)
        btns_layout.addWidget(datesheet_btn)
        central_layout.addLayout(btns_layout)

        # Footer
        footer = QLabel("Developed by the Computer Science Department, GIGCCL")
        footer.setFont(QFont("Arial", 10, QFont.Weight.Normal))
        footer.setStyleSheet("color: #888; margin-top: 40px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        central_layout.addWidget(footer, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)

        menu_layout.addWidget(central_widget, stretch=1)

        # Timetable and Datesheet pages
        self.timetable_page = TimetableWindow(back_callback=self.show_menu)
        self.datesheet_page = DatesheetWindow(back_callback=self.show_menu)

        self.stacked.addWidget(self.menu_page)         # index 0
        self.stacked.addWidget(self.timetable_page)    # index 1
        self.stacked.addWidget(self.datesheet_page)    # index 2

        self.show_menu()

    def show_menu(self):
        self.stacked.setCurrentIndex(0)

    def open_timetable(self):
        self.stacked.setCurrentIndex(1)

    def open_datesheet(self):
        self.stacked.setCurrentIndex(2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  # Only call this here
    sys.exit(app.exec())