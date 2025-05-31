from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QInputDialog, QCheckBox, QTableWidgetItem, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class TimetableWindow(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(10)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Tab widget for semester frames
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_semester_tab)
        main_layout.addWidget(self.tab_widget)

        # Bottom buttons (always visible)
        bottom_buttons = self.create_bottom_buttons()
        main_layout.addWidget(bottom_buttons)

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #2196F3; color: white;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("Timetable Data Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        home_btn = QPushButton("Home")
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)
        if self.back_callback:
            home_btn.clicked.connect(self.back_callback)
        # Add "Add Semester" button
        add_semester_btn = QPushButton("Add Semester and class/section")
        add_semester_btn.setStyleSheet(self.get_button_style("#007bff", min_width="150px"))
        add_semester_btn.clicked.connect(self.add_new_semester_dialog)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_semester_btn)
        header_layout.addWidget(home_btn)
        return header

    def add_new_semester_dialog(self):
        name, ok = QInputDialog.getText(self, "New Semester and class/section Frame", "Enter semester and class/section name:")
        if ok and name.strip():
            self.add_semester_tab(name.strip())

    def add_semester_tab(self, semester_name):
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QComboBox, QCheckBox, QTableWidgetItem, QHeaderView
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_header_layout = QHBoxLayout()
        title = QLabel("Timetable Entries")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #333; margin-bottom: 15px;")
        add_row_btn = QPushButton("Add New Entry")
        add_row_btn.setStyleSheet(self.get_button_style("#007bff", min_width="150px"))
        table = QTableWidget()
        table.setColumnCount(10)
        table.horizontalHeader().setVisible(True)
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(40)
        header_view = table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 50)
        table.setColumnWidth(1, 40)

        def add_row():
            row_position = table.rowCount()
            table.insertRow(row_position)

            # --- Copy data from previous row if exists ---
            prev_data = {}
            if row_position > 0:
                # Shift (QComboBox)
                prev_shift = table.cellWidget(row_position - 1, 2)
                if prev_shift:
                    prev_data['shift'] = prev_shift.currentText()
                # Semester, Class/Section, Room (QTableWidgetItem)
                for col, key in zip([3, 4, 5], ['semester', 'class_section', 'room']):
                    prev_item = table.item(row_position - 1, col)
                    if prev_item:
                        prev_data[key] = prev_item.text()
            # ---------------------------------------------

            checkbox = QCheckBox()
            cell_widget_container = QWidget()
            layout = QHBoxLayout(cell_widget_container)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            table.setCellWidget(row_position, 0, cell_widget_container)

            row_num_item = QTableWidgetItem(str(row_position + 1))
            row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_position, 1, row_num_item)

            shift_combo = QComboBox()
            shift_combo.addItems(["Morning", "Evening"])
            shift_combo.setStyleSheet(self.get_combo_style())
            shift_combo.setCurrentText(prev_data.get('shift', "Select Shift"))
            table.setCellWidget(row_position, 2, shift_combo)

            placeholders = {
                3: "Semester",
                4: "Class/Section",
                5: "Room",
                6: "Teacher Name",
                7: "Course Code",
                8: "Course Name",
                9: "Lab"
            }
            for col in range(3, table.columnCount()):
                if col == 3:
                    text = prev_data.get('semester', placeholders[col])
                elif col == 4:
                    text = prev_data.get('class_section', placeholders[col])
                elif col == 5:
                    text = prev_data.get('room', placeholders[col])
                else:
                    text = placeholders.get(col, "")
                item = QTableWidgetItem(text)
                if col in [3, 4, 5] and text != placeholders[col]:
                    item.setForeground(Qt.GlobalColor.black)
                else:
                    item.setForeground(Qt.GlobalColor.gray)
                table.setItem(row_position, col, item)

        add_row_btn.clicked.connect(add_row)
        table_header_layout.addWidget(title)
        table_header_layout.addStretch()
        table_header_layout.addWidget(add_row_btn)
        table_layout.addLayout(table_header_layout)
        table_layout.addWidget(table)
        table_frame.table = table
        self.tab_widget.addTab(table_frame, semester_name)
        self.tab_widget.setCurrentWidget(table_frame)  # Switch to new tab

    def get_current_table(self):
        # Helper to get the table widget of the current tab
        current_widget = self.tab_widget.currentWidget()
        if current_widget and hasattr(current_widget, "table"):
            return current_widget.table
        return None

    def close_semester_tab(self, index):
        self.tab_widget.removeTab(index)

    # --- Keep your get_combo_style and get_button_style methods as before ---
    def get_combo_style(self):
        return """
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                 border: none;
            }
        """

    def get_button_style(self, color, min_width="120px"):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-width: {min_width};
            }}
            QPushButton:hover {{
                background-color: {self.adjust_brightness(color, 0.9)};
            }}
            QPushButton:pressed {{
                background-color: {self.adjust_brightness(color, 0.8)};
            }}
        """

    def adjust_brightness(self, hex_color, factor):
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def create_bottom_buttons(self):
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
        buttons_frame = QWidget()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(20, 10, 20, 10)
        delete_btn = QPushButton("Delete Selected Entries")
        delete_btn.setStyleSheet(self.get_button_style("#dc3545", min_width="180px"))
        clear_btn = QPushButton("Clear All Entries")
        clear_btn.setStyleSheet(self.get_button_style("#6c757d", min_width="150px"))
        save_db_btn = QPushButton("Save Entries to DB")
        save_db_btn.setStyleSheet(self.get_button_style("#28a745", min_width="160px"))
        load_db_btn = QPushButton("Load from DB")
        load_db_btn.setStyleSheet(self.get_button_style("#007bff", min_width="150px"))
        erase_db_btn = QPushButton("Erase All Database Data")
        erase_db_btn.setStyleSheet(self.get_button_style("#dc3545", min_width="200px"))
        generate_btn = QPushButton("Generate Timetable")
        generate_btn.setStyleSheet(self.get_button_style("#17a2b8", min_width="180px"))
        generate_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addSpacing(20)
        buttons_layout.addWidget(save_db_btn)
        buttons_layout.addWidget(load_db_btn)
        buttons_layout.addWidget(erase_db_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(generate_btn)

        # --- Connect delete and clear buttons ---
        delete_btn.clicked.connect(self.delete_selected_entries)
        clear_btn.clicked.connect(self.clear_all_entries)
        load_db_btn.clicked.connect(self.load_from_db)
        save_db_btn.clicked.connect(self.save_entries_to_db)
        erase_db_btn.clicked.connect(self.erase_all_database_data)
        generate_btn.clicked.connect(self.show_generate_timetable_dialog)  # Connect here

        return buttons_frame

    def show_generate_timetable_dialog(self):
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QTimeEdit, QCheckBox,
            QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QDateEdit
        )
        from PyQt6.QtCore import QTime, QDate
        import os
        import sys
        import importlib.util
        from datetime import datetime

        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Timetable Generation")
        dialog.resize(700, 800)
        layout = QVBoxLayout(dialog)

        # --- Timetable Metadata ---
        layout.addWidget(QLabel("<b>Timetable Metadata</b>"))
        college_name_edit = QLineEdit()
        college_name_edit.setPlaceholderText("College Name")
        college_name_edit.setText("GOVT. ISLAMIA GRADUATE COLLEGE, CIVIL LINES, LAHORE")  # Default value

        layout.addWidget(college_name_edit)
        timetable_title_edit = QLineEdit()
        timetable_title_edit.setPlaceholderText("Timetable Title")
        timetable_title_edit.setText("TIME TABLE FOR BS PROGRAMS")  # Default value

        layout.addWidget(timetable_title_edit)
        effective_date_edit = QDateEdit()
        effective_date_edit.setCalendarPopup(True)
        effective_date_edit.setDate(QDate.currentDate())  # Default to current date

        layout.addWidget(QLabel("Effective Date:"))
        layout.addWidget(effective_date_edit)
        department_name_edit = QLineEdit()
        department_name_edit.setPlaceholderText("Department Name")
        department_name_edit.setText("Computer Science")  # Default value

        layout.addWidget(department_name_edit)

        # --- Generation Parameters ---
        layout.addWidget(QLabel("<b>Generation Parameters</b>"))
        shift_combo = QComboBox()
        shift_combo.addItems(["Morning", "Evening"])
        layout.addWidget(QLabel("Shift:"))
        layout.addWidget(shift_combo)
        lectures_spin = QSpinBox()
        lectures_spin.setRange(1, 10)
        lectures_spin.setValue(3)
        layout.addWidget(QLabel("Lectures per Course:"))
        layout.addWidget(lectures_spin)
        duration_spin = QSpinBox()
        duration_spin.setRange(30, 180)
        duration_spin.setValue(60)
        layout.addWidget(QLabel("Lecture Duration (minutes):"))
        layout.addWidget(duration_spin)
        start_time_edit = QTimeEdit()
        start_time_edit.setDisplayFormat("hh:mm AP")
        start_time_edit.setTime(QTime(8, 0))
        layout.addWidget(QLabel("Daily Start Time:"))
        layout.addWidget(start_time_edit)
        end_time_edit = QTimeEdit()
        end_time_edit.setDisplayFormat("hh:mm AP")
        end_time_edit.setTime(QTime(13, 0))
        layout.addWidget(QLabel("Daily End Time:"))
        layout.addWidget(end_time_edit)

        # --- Days selection ---
        layout.addWidget(QLabel("Days:"))
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        day_checks = []
        day_layout = QHBoxLayout()
        for day in days:
            cb = QCheckBox(day)
            cb.setChecked(True)
            day_layout.addWidget(cb)
            day_checks.append(cb)
        layout.addLayout(day_layout)

        # --- Class Section/Semester Dropdown (from DB) ---
        layout.addWidget(QLabel("Class Section/Semester:"))
        class_section_combo = QComboBox()
        # Fetch from DB
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
        timetable_db_path = os.path.join(db_dir, "timetable_db.py")
        spec = importlib.util.spec_from_file_location("timetable_db", timetable_db_path)
        timetable_db = importlib.util.module_from_spec(spec)
        sys.modules["timetable_db"] = timetable_db
        spec.loader.exec_module(timetable_db)
        cur = timetable_db.conn.cursor()
        cur.execute("SELECT DISTINCT semester, name, shift FROM class_sections")
        class_section_list = cur.fetchall()
        def get_class_section_options_for_shift(shift):
            return [f"{sem} - {name} - {sh}" for sem, name, sh in class_section_list if sh == shift]
        class_section_combo.addItems(get_class_section_options_for_shift(shift_combo.currentText()))
        layout.addWidget(class_section_combo)
        def update_class_section_options():
            class_section_combo.clear()
            class_section_combo.addItems(get_class_section_options_for_shift(shift_combo.currentText()))
        shift_combo.currentTextChanged.connect(update_class_section_options)

        # --- Course selection and exceptions table ---
        layout.addWidget(QLabel("Course Exceptions (frequency per course):"))
        course_combo = QComboBox()
        freq_spin = QSpinBox()
        freq_spin.setRange(1, 10)
        freq_spin.setValue(1)
        add_exception_btn = QPushButton("Add Exception")
        exceptions_table = QTableWidget(0, 3)
        exceptions_table.setHorizontalHeaderLabels(["Code", "Course Name", "Frequency"])
        exceptions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        remove_exception_btn = QPushButton("Remove Selected Exception")

        # Fetch all courses for all class sections
        cur.execute("SELECT cs.semester, cs.name, cs.shift, c.code, c.name FROM courses c "
                    "JOIN timetable t ON t.course_id = c.id "
                    "JOIN class_sections cs ON t.class_section_id = cs.id")
        all_courses = cur.fetchall()

        def update_course_combo():
            # Get selected class section/semester/shift
            class_section_str = class_section_combo.currentText()
            if not class_section_str:
                course_combo.clear()
                return
            try:
                semester, section, shift = [x.strip() for x in class_section_str.split(" - ", 2)]
            except ValueError:
                course_combo.clear()
                return
            filtered = [
                f"{code} - {name}"
                for sem, sec, sh, code, name in all_courses
                if sem == semester and sec == section and sh == shift
            ]
            course_combo.clear()
            course_combo.addItems(filtered)

        # Update courses when class section changes
        class_section_combo.currentTextChanged.connect(update_course_combo)
        # Also update initially
        update_course_combo()

        # Add row
        def add_exception():
            course_str = course_combo.currentText()
            if not course_str:
                return
            code, name = course_str.split(" - ", 1)
            freq = freq_spin.value()
            row = exceptions_table.rowCount()
            exceptions_table.insertRow(row)
            exceptions_table.setItem(row, 0, QTableWidgetItem(code))
            exceptions_table.setItem(row, 1, QTableWidgetItem(name))
            exceptions_table.setItem(row, 2, QTableWidgetItem(str(freq)))
        add_exception_btn.clicked.connect(add_exception)
        # Remove row
        def remove_exception():
            selected = exceptions_table.currentRow()
            if selected >= 0:
                exceptions_table.removeRow(selected)
        remove_exception_btn.clicked.connect(remove_exception)
        # Layout for course/freq/add
        exc_layout = QHBoxLayout()
        exc_layout.addWidget(course_combo)
        exc_layout.addWidget(freq_spin)
        exc_layout.addWidget(add_exception_btn)
        exc_layout.addWidget(remove_exception_btn)
        layout.addLayout(exc_layout)
        layout.addWidget(exceptions_table)

        # --- Breaks Section ---
        layout.addWidget(QLabel("<b>Breaks (No lectures during these times)</b>"))
        breaks_table = QTableWidget(0, 3)
        breaks_table.setHorizontalHeaderLabels(["Day", "Start Time", "End Time"])
        breaks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        break_day_combo = QComboBox()
        break_day_combo.addItems(days)
        break_start_edit = QTimeEdit()
        break_start_edit.setDisplayFormat("hh:mm AP")
        break_end_edit = QTimeEdit()
        break_end_edit.setDisplayFormat("hh:mm AP")
        add_break_btn = QPushButton("Add Break")
        remove_break_btn = QPushButton("Remove Selected Break")
        # Add break
        def add_break():
            day = break_day_combo.currentText()
            start = break_start_edit.time().toString("hh:mm AP")
            end = break_end_edit.time().toString("hh:mm AP")
            # Validate start < end
            try:
                s = datetime.strptime(start, "%I:%M %p")
                e = datetime.strptime(end, "%I:%M %p")
                if s >= e:
                    QMessageBox.warning(dialog, "Invalid Break", "Break start time must be before end time.")
                    return
            except Exception:
                QMessageBox.warning(dialog, "Invalid Time", "Break times must be in HH:MM AM/PM format.")
                return
            row = breaks_table.rowCount()
            breaks_table.insertRow(row)
            breaks_table.setItem(row, 0, QTableWidgetItem(day))
            breaks_table.setItem(row, 1, QTableWidgetItem(start))
            breaks_table.setItem(row, 2, QTableWidgetItem(end))
        add_break_btn.clicked.connect(add_break)
        # Remove break
        def remove_break():
            selected = breaks_table.currentRow()
            if selected >= 0:
                breaks_table.removeRow(selected)
        remove_break_btn.clicked.connect(remove_break)
        # Layout for breaks
        breaks_layout = QHBoxLayout()
        breaks_layout.addWidget(break_day_combo)
        breaks_layout.addWidget(break_start_edit)
        breaks_layout.addWidget(break_end_edit)
        breaks_layout.addWidget(add_break_btn)
        breaks_layout.addWidget(remove_break_btn)
        layout.addLayout(breaks_layout)
        layout.addWidget(breaks_table)

        # --- Dialog Buttons ---
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Generate")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def on_generate():
            # Collect all values
            meta = {
                "college_name": college_name_edit.text(),
                "timetable_title": timetable_title_edit.text(),
                "effective_date": effective_date_edit.date().toString("dd-MM-yyyy"),
                "department_name": department_name_edit.text()
            }
            shift = shift_combo.currentText()
            lectures_per_course = lectures_spin.value()
            lecture_duration = duration_spin.value()
            start_time = start_time_edit.time().toString("hh:mm AP")
            end_time = end_time_edit.time().toString("hh:mm AP")
            selected_days = [cb.text() for cb in day_checks if cb.isChecked()]
            if not selected_days:
                QMessageBox.warning(dialog, "No Days Selected", "Please select at least one day.")
                return
            # Exceptions
            exceptions = {}
            for row in range(exceptions_table.rowCount()):
                code = exceptions_table.item(row, 0).text()
                freq = int(exceptions_table.item(row, 2).text())
                exceptions[code] = freq
            # Breaks
            breaks = []
            for row in range(breaks_table.rowCount()):
                day = breaks_table.item(row, 0).text()
                start = breaks_table.item(row, 1).text()
                end = breaks_table.item(row, 2).text()
                breaks.append({"day": day, "start": start, "end": end})

            # --- Call timetable generation ---
            dialog.accept()
            run_timetable_generation(
                shift=shift,
                lectures_per_course=lectures_per_course,
                lecture_duration=lecture_duration,
                start_time=start_time,
                end_time=end_time,
                days=selected_days,
                timetable_metadata=meta,
                course_exceptions=exceptions,
                breaks=breaks
            )

        ok_btn.clicked.connect(on_generate)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def erase_all_database_data(self):
        from PyQt6.QtWidgets import QMessageBox
        import sys
        import os
        import importlib.util

        reply = QMessageBox.question(
            self,
            "Confirm Erase",
            "Are you sure you want to erase ALL data from the database? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Dynamically import timetable_db
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
        timetable_db_path = os.path.join(db_dir, "timetable_db.py")
        spec = importlib.util.spec_from_file_location("timetable_db", timetable_db_path)
        timetable_db = importlib.util.module_from_spec(spec)
        sys.modules["timetable_db"] = timetable_db
        spec.loader.exec_module(timetable_db)

        try:
            cur = timetable_db.conn.cursor()
            # Delete all data from all tables (order matters due to foreign keys)
            cur.execute("DELETE FROM timetable")
            cur.execute("DELETE FROM courses")
            cur.execute("DELETE FROM teachers")
            cur.execute("DELETE FROM rooms")
            cur.execute("DELETE FROM class_sections")
            timetable_db.conn.commit()
            QMessageBox.information(self, "Success", "All data has been erased from the database.")
            # Optionally clear all tabs in the UI
            self.tab_widget.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to erase database data:\n{e}")

    def save_entries_to_db(self):
        import sys
        import os
        import importlib.util
        from PyQt6.QtWidgets import QMessageBox

        # Dynamically import timetable_db
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
        timetable_db_path = os.path.join(db_dir, "timetable_db.py")
        spec = importlib.util.spec_from_file_location("timetable_db", timetable_db_path)
        timetable_db = importlib.util.module_from_spec(spec)
        sys.modules["timetable_db"] = timetable_db
        spec.loader.exec_module(timetable_db)

        # --- Remove all timetable entries before saving new ones ---
        try:
            cur = timetable_db.conn.cursor()
            cur.execute("DELETE FROM timetable")
            timetable_db.conn.commit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear old timetable entries:\n{e}")
            return

        total_saved = 0
        # Loop through all tabs
        for tab_index in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(tab_index)
            if not hasattr(tab_widget, "table"):
                continue
            table = tab_widget.table
            for row in range(table.rowCount()):
                shift_combo = table.cellWidget(row, 2)
                shift = shift_combo.currentText() if shift_combo else ""
                semester = table.item(row, 3).text() if table.item(row, 3) else ""
                class_section = table.item(row, 4).text() if table.item(row, 4) else ""
                room = table.item(row, 5).text() if table.item(row, 5) else ""
                teacher = table.item(row, 6).text() if table.item(row, 6) else ""
                course_code = table.item(row, 7).text() if table.item(row, 7) else ""
                course_name = table.item(row, 8).text() if table.item(row, 8) else ""
                indicators = table.item(row, 9).text() if table.item(row, 9) else ""

                # Use timetable_db helper to get or create IDs
                teacher_id = timetable_db.fetch_id_from_name("teachers", teacher)
                if not teacher_id:
                    continue
                course_id = timetable_db.fetch_id_from_name("courses", course_name, teacher_id=teacher_id, code=course_code, indicators=indicators)
                if not course_id:
                    continue
                # --- Update indicators (Lab) if course already exists ---
                try:
                    cur.execute(
                        "UPDATE courses SET indicators = ? WHERE id = ?",
                        (indicators, course_id)
                    )
                    timetable_db.conn.commit()
                except Exception:
                    pass
                # --- End update indicators ---
                room_id = timetable_db.fetch_id_from_name("rooms", room)
                if not room_id:
                    continue
                class_section_id = timetable_db.fetch_id_from_name("class_sections", class_section, semester=semester, shift=shift)
                if not class_section_id:
                    continue

                # Insert into timetable table
                try:
                    cur.execute(
                        "INSERT INTO timetable (teacher_id, course_id, room_id, class_section_id, semester, shift) VALUES (?, ?, ?, ?, ?, ?)",
                        (teacher_id, course_id, room_id, class_section_id, semester, shift)
                    )
                    timetable_db.conn.commit()
                    total_saved += 1
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save entry on tab {tab_index+1}, row {row+1}:\n{e}")
                    return

        if total_saved == 0:
            QMessageBox.warning(self, "No Data", "There are no entries to save.")
        else:
            QMessageBox.information(self, "Success", f"All entries from all semesters saved to the database (previous entries replaced).")

    def load_from_db(self):
        import sys
        import os
        import importlib.util
        from PyQt6.QtWidgets import QInputDialog, QMessageBox

        # Ask user which shift to load
        shift, ok = QInputDialog.getItem(
            self,
            "Select Shift",
            "Which shift entries do you want to load?",
            ["Morning", "Evening", "Both"],
            0,
            False
        )
        if not ok:
            return

        # Build the path to timetable_db.py
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
        timetable_db_path = os.path.join(db_dir, "timetable_db.py")

        # Dynamically import timetable_db
        spec = importlib.util.spec_from_file_location("timetable_db", timetable_db_path)
        timetable_db = importlib.util.module_from_spec(spec)
        sys.modules["timetable_db"] = timetable_db
        spec.loader.exec_module(timetable_db)

        # Clear all tabs first
        self.tab_widget.clear()

        # Load entries for selected shift(s)
        all_entries = []
        shifts_to_load = []
        if shift == "Both":
            shifts_to_load = ["Morning", "Evening"]
        else:
            shifts_to_load = [shift]
        for s in shifts_to_load:
            entries = timetable_db.load_timetable(s)
            all_entries.extend(entries)

        # Show message if database is empty
        if not all_entries:
            QMessageBox.information(self, "Database Empty", "The database is empty. No entries to load.")
            return

        # Group entries by (semester, class_section, shift)
        from collections import defaultdict
        grouped = defaultdict(list)
        for entry in all_entries:
            key = (entry['semester'], entry['class_section_name'], entry['shift'])
            grouped[key].append(entry)

        # For each group, create a tab and fill the table
        for (semester, class_section, shift), entries in grouped.items():
            tab_name = f"{semester} - {class_section} ({shift})"
            self.add_semester_tab(tab_name)
            table = self.get_current_table()
            for entry in entries:
                row_position = table.rowCount()
                table.insertRow(row_position)

                # Checkbox
                checkbox = QCheckBox()
                cell_widget_container = QWidget()
                layout = QHBoxLayout(cell_widget_container)
                layout.addWidget(checkbox)
                layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.setContentsMargins(0,0,0,0)
                table.setCellWidget(row_position, 0, cell_widget_container)

                # Row number
                row_num_item = QTableWidgetItem(str(row_position + 1))
                row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_position, 1, row_num_item)

                # Shift
                shift_combo = QComboBox()
                shift_combo.addItems(["Morning", "Evening"])
                shift_combo.setStyleSheet(self.get_combo_style())
                shift_combo.setCurrentText(entry['shift'])
                table.setCellWidget(row_position, 2, shift_combo)

                # Semester
                semester_item = QTableWidgetItem(entry['semester'])
                semester_item.setForeground(Qt.GlobalColor.black)
                table.setItem(row_position, 3, semester_item)

                # Class/Section
                class_section_item = QTableWidgetItem(entry['class_section_name'])
                class_section_item.setForeground(Qt.GlobalColor.black)
                table.setItem(row_position, 4, class_section_item)

                # Room
                room_item = QTableWidgetItem(str(entry['room_name']))
                room_item.setForeground(Qt.GlobalColor.black)
                table.setItem(row_position, 5, room_item)

                # Teacher Name
                teacher_item = QTableWidgetItem(entry['teacher_name'])
                teacher_item.setForeground(Qt.GlobalColor.black)
                table.setItem(row_position, 6, teacher_item)

                # Course Code
                course_code_item = QTableWidgetItem(entry['course_code'])
                course_code_item.setForeground(Qt.GlobalColor.black)
                table.setItem(row_position, 7, course_code_item)

                # Course Name
                course_name_item = QTableWidgetItem(entry['course_name'])
                course_name_item.setForeground(Qt.GlobalColor.black)
                table.setItem(row_position, 8, course_name_item)

                # Lab (use indicators from DB)
                lab_value = entry.get('course_indicators', "")
                lab_item = QTableWidgetItem(lab_value if lab_value is not None else "")
                lab_item.setForeground(Qt.GlobalColor.black)
                table.setItem(row_position, 9, lab_item)

    def delete_selected_entries(self):
        from PyQt6.QtWidgets import QMessageBox
        import sys
        import os
        import importlib.util

        table = self.get_current_table()
        if not table:
            return

        # Collect rows with checked checkboxes in column 0
        rows_to_delete = []
        entries_to_delete = []
        for row in range(table.rowCount()):
            cell_widget = table.cellWidget(row, 0)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    rows_to_delete.append(row)
                    # Collect entry data for database deletion
                    entry = {
                        'shift': table.cellWidget(row, 2).currentText(),
                        'semester': table.item(row, 3).text(),
                        'class_section': table.item(row, 4).text(),
                        'room': table.item(row, 5).text(),
                        'teacher': table.item(row, 6).text(),
                        'course_code': table.item(row, 7).text(),
                        'course_name': table.item(row, 8).text()
                    }
                    entries_to_delete.append(entry)

        if not rows_to_delete:
            QMessageBox.information(self, "No Selection", "Please select entries to delete.")
            return

        # Ask user about deletion scope
        reply = QMessageBox.question(
            self,
            "Delete Confirmation",
            "Do you want to delete the selected entries from:\n\n"
            "- Click 'Yes' to delete from both UI and database\n"
            "- Click 'No' to delete from UI only\n"
            "- Click 'Cancel' to abort deletion",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        # Delete from database if user chose Yes
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Dynamically import timetable_db
                db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
                timetable_db_path = os.path.join(db_dir, "timetable_db.py")
                spec = importlib.util.spec_from_file_location("timetable_db", timetable_db_path)
                timetable_db = importlib.util.module_from_spec(spec)
                sys.modules["timetable_db"] = timetable_db
                spec.loader.exec_module(timetable_db)

                cur = timetable_db.conn.cursor()
                for entry in entries_to_delete:
                    # Find and delete the matching timetable entry
                    cur.execute("""
                        DELETE FROM timetable 
                        WHERE class_section_id IN (
                            SELECT cs.id 
                            FROM class_sections cs 
                            WHERE cs.name = ? AND cs.semester = ? AND cs.shift = ?
                        )
                        AND room_id IN (
                            SELECT r.id 
                            FROM rooms r 
                            WHERE r.name = ?
                        )
                        AND teacher_id IN (
                            SELECT t.id 
                            FROM teachers t 
                            WHERE t.name = ?
                        )
                        AND course_id IN (
                            SELECT c.id 
                            FROM courses c 
                            WHERE c.code = ? AND c.name = ?
                        )
                    """, (
                        entry['class_section'],
                        entry['semester'],
                        entry['shift'],
                        entry['room'],
                        entry['teacher'],
                        entry['course_code'],
                        entry['course_name']
                    ))
                timetable_db.conn.commit()
                QMessageBox.information(self, "Success", "Selected entries deleted from database.")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete from database: {e}")
                return

        # Remove from UI
        for row in reversed(rows_to_delete):
            table.removeRow(row)
        
        # Re-number the row numbers
        for row in range(table.rowCount()):
            item = table.item(row, 1)
            if item:
                item.setText(str(row + 1))

    def clear_all_entries(self):
        table = self.get_current_table()
        if not table:
            return
        table.setRowCount(0)

def run_timetable_generation(
    shift, lectures_per_course, lecture_duration, start_time,
    end_time, days, timetable_metadata, course_exceptions=None, breaks=None
):
    try:
        import os
        import sys
        import importlib.util
        from PyQt6.QtWidgets import QMessageBox

        # --- Dynamically import timetable_db ---
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db")
        timetable_db_path = os.path.join(db_dir, "timetable_db.py")
        spec = importlib.util.spec_from_file_location("timetable_db", timetable_db_path)
        timetable_db = importlib.util.module_from_spec(spec)
        sys.modules["timetable_db"] = timetable_db
        spec.loader.exec_module(timetable_db)

        # --- Dynamically import timetable_ga ---
        algo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "algorithm")
        ga_path = os.path.join(algo_dir, "timetable_ga.py")
        spec_ga = importlib.util.spec_from_file_location("timetable_ga", ga_path)
        timetable_ga = importlib.util.module_from_spec(spec_ga)
        sys.modules["timetable_ga"] = timetable_ga
        spec_ga.loader.exec_module(timetable_ga)

        print(f"Loading GA data for Shift: {shift}")
        db_rows_for_ga = timetable_db.load_timetable_for_ga(shift=shift)

        if not db_rows_for_ga:
            QMessageBox.warning(None, "No Data for GA", f"No timetable entries found in the database for Shift: {shift} to generate a timetable.")
            return

        ga_entries = [
            {
                "course_name": r["course_name"],
                "course_code": r["course_code"],
                "course_indicators": r.get("course_indicators", ""),
                "class_section": r["class_section_name"],
                "room": str(r["room_name"]),
                "teacher": r["teacher_name"],
                "semester": r["semester"]
            }
            for r in db_rows_for_ga
        ]

        if not ga_entries:
            QMessageBox.warning(None, "Processing Error", "Failed to prepare entries for the Genetic Algorithm.")
            return

        time_slots = timetable_ga.generate_time_slots(
            days, start_time, end_time, lecture_duration, break_duration=10, breaks=breaks
        )
        print("Generated UI time slots for GA:", len(time_slots))

        if not time_slots:
            QMessageBox.warning(None, "Configuration Error", "Could not generate any valid time slots. Check start/end times and duration.")
            return

        ga = timetable_ga.TimetableGeneticAlgorithm(
            entries=ga_entries,
            time_slots_input=time_slots,
            lectures_per_course=lectures_per_course,
            course_exceptions=course_exceptions,
            population_size=100,
            max_generations=100,
            mutation_rate=0.15
        )

        optimized_schedule, best_fitness = ga.evolve()

        print(f"Debug: GA returned optimized schedule with fitness: {best_fitness}")
        print(f"Debug: Optimized schedule contains {len(optimized_schedule or {})} lecture entries")

        if optimized_schedule is None or not optimized_schedule:
            QMessageBox.warning(None, "Generation Failed", "The genetic algorithm could not generate a valid timetable with the given constraints and data.")
            return

        display_title = f"{timetable_metadata['timetable_title']} - {shift} Shift"
        display_timetable(optimized_schedule, time_slots, days, timetable_metadata, display_title)

    except Exception as ex:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Timetable Generation Error", f"Failed to generate timetable: {ex}")
        import traceback
        traceback.print_exc()

def display_timetable(optimized_timetable_data, available_time_slots,
                      scheduled_days, timetable_metadata, display_title):
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
        QPushButton, QMessageBox, QHeaderView, QFileDialog
    )
    from PyQt6.QtCore import Qt

    dialog = QDialog()
    dialog.setWindowTitle(display_title)
    dialog.resize(1400, 900)

    # --- Track current timetable state for export ---
    current_timetable = {}
    for key_tuple, details in optimized_timetable_data.items():
        day, time = details['time_slot'].split(" ", 1)
        section = details['class_section']
        semester = details.get('semester', 'N/A')
        current_timetable[(semester, section, day, time)] = details.copy()

    # --- Helper state for selection ---
    selected_cell = {"widget": None}

    # --- Conflict checking helper ---
    def check_conflict(ld, target_day, target_time, skip_key=None):
        if not ld:
            return False, ""
        teacher = ld['teacher']
        room = ld['room']
        section = ld['class_section']
        semester = ld.get('semester', 'N/A')
        for key, details in current_timetable.items():
            if skip_key is not None and key == skip_key:
                continue
            k_sem, k_sec, k_day, k_time = key
            if k_day == target_day and k_time == target_time:
                if details['teacher'] == teacher:
                    return True, f"Teacher conflict: {teacher} already assigned at {target_day} {target_time}"
                if details['room'] == room:
                    return True, f"Room conflict: Room {room} already assigned at {target_day} {target_time}"
                if details['class_section'] == section and details.get('semester', 'N/A') == semester:
                    return True, f"Section conflict: {section} ({semester}) already assigned at {target_day} {target_time}"
        return False, ""

    # --- Helper functions for cell selection and swapping ---
    def select_cell(cell):
        if selected_cell["widget"]:
            # Reset previous cell's background
            selected_cell["widget"].setBackground(Qt.GlobalColor.white)
        selected_cell["widget"] = cell
        cell.setBackground(QColor("#b3d9ff"))  # Light blue highlight

    def deselect_cell():
        if selected_cell["widget"]:
            selected_cell["widget"].setBackground(Qt.GlobalColor.white)
        selected_cell["widget"] = None

    def on_cell_click(row, col, table, cell_widgets):
        cell = cell_widgets[(row, col)]
        if selected_cell["widget"] == cell:
            deselect_cell()
            return
        if selected_cell["widget"] is None:
            select_cell(cell)
            return
        # Swap
        swap_cells(selected_cell["widget"], cell)
        deselect_cell()

    def swap_cells(cell1, cell2):
        ld1 = getattr(cell1, "lecture_details", None)
        ld2 = getattr(cell2, "lecture_details", None)
        key1 = (cell1.semester, cell1.section, cell1.day, cell1.time_slot)
        key2 = (cell2.semester, cell2.section, cell2.day, cell2.time_slot)
        if ld2:
            conflict, msg = check_conflict(ld2, cell1.day, cell1.time_slot, skip_key=key2)
            if conflict:
                QMessageBox.warning(dialog, "Conflict Detected", f"Cannot swap:\n{msg}")
                return
        if ld1:
            conflict, msg = check_conflict(ld1, cell2.day, cell2.time_slot, skip_key=key1)
            if conflict:
                QMessageBox.warning(dialog, "Conflict Detected", f"Cannot swap:\n{msg}")
                return
        # Swap time_slot in details
        if ld1:
            ld1 = ld1.copy()
            ld1["time_slot"] = f"{cell2.day} {cell2.time_slot}"
        if ld2:
            ld2 = ld2.copy()
            ld2["time_slot"] = f"{cell1.day} {cell1.time_slot}"
        # Assign new details
        if ld2:
            create_cell_content(cell1, ld2)
        else:
            cell1.setText("")
            if hasattr(cell1, "lecture_details"):
                delattr(cell1, "lecture_details")
        if ld1:
            create_cell_content(cell2, ld1)
        else:
            cell2.setText("")
            if hasattr(cell2, "lecture_details"):
                delattr(cell2, "lecture_details")
        # Update current_timetable dict
        current_timetable.pop(key1, None)
        current_timetable.pop(key2, None)
        if ld2:
            new_key1 = (cell1.semester, cell1.section, cell1.day, cell1.time_slot)
            current_timetable[new_key1] = ld2
        if ld1:
            new_key2 = (cell2.semester, cell2.section, cell2.day, cell2.time_slot)
            current_timetable[new_key2] = ld1

    def create_cell_content(cell, lecture_details):
        cell_text = f"{lecture_details['course_name']}\n({lecture_details['course_code']})\n{lecture_details.get('course_indicators','')}\n{lecture_details['teacher']}\nR: {lecture_details['room']}"
        cell.setText(cell_text)
        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        cell.lecture_details = lecture_details

    # --- UI Layout ---
    layout = QVBoxLayout(dialog)

    # Metadata
    meta_widget = QWidget()
    meta_layout = QVBoxLayout(meta_widget)
    meta_layout.addWidget(QLabel(f"<b>{timetable_metadata.get('college_name', 'College Name N/A')}</b>"))
    meta_layout.addWidget(QLabel(timetable_metadata.get("timetable_title", "Timetable")))
    meta_layout.addWidget(QLabel(f"Effective Date: {timetable_metadata.get('effective_date', 'N/A')}"))
    meta_layout.addWidget(QLabel(f"Department: {timetable_metadata.get('department_name', 'N/A')}"))
    layout.addWidget(meta_widget)

    # Group data by (semester, section)
    sem_sec_groups = {}
    for key_tuple, details in optimized_timetable_data.items():
        semester = details.get('semester', 'N/A')
        section = details['class_section']
        group_key = (semester, section)
        if group_key not in sem_sec_groups:
            sem_sec_groups[group_key] = {}
        day, time = details['time_slot'].split(" ", 1)
        if time not in sem_sec_groups[group_key]:
            sem_sec_groups[group_key][time] = {}
        if day not in sem_sec_groups[group_key][time]:
            sem_sec_groups[group_key][time][day] = []
        sem_sec_groups[group_key][time][day].append(details)

    # Get unique time slots and days
    time_slots = sorted(list(set(slot.split(" ", 1)[1] for slot in available_time_slots)))
    days = scheduled_days

    tab_widget = QTabWidget()
    layout.addWidget(tab_widget)

    for (semester, section), data in sem_sec_groups.items():
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        table = QTableWidget(len(time_slots), len(days))
        table.setHorizontalHeaderLabels(days)
        table.setVerticalHeaderLabels(time_slots)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cell_widgets = {}

        for i, time_slot in enumerate(time_slots):
            for j, day in enumerate(days):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # If there's data for this cell
                if time_slot in data and day in data[time_slot]:
                    lecture_details = data[time_slot][day][0]
                    create_cell_content(item, lecture_details)
                # Attach meta for swapping
                item.time_slot = time_slot
                item.day = day
                item.semester = semester
                item.section = section
                cell_widgets[(i, j)] = item
                table.setItem(i, j, item)

        def make_cell_click_handler(row, col, table=table, cell_widgets=cell_widgets):
            return lambda: on_cell_click(row, col, table, cell_widgets)

        # Connect cell click events
        for i in range(len(time_slots)):
            for j in range(len(days)):
                table.item(i, j).setFlags(table.item(i, j).flags() | Qt.ItemFlag.ItemIsSelectable)
                table.item(i, j).setFlags(table.item(i, j).flags() | Qt.ItemFlag.ItemIsEnabled)
                table.item(i, j).setBackground(Qt.GlobalColor.white)
                table.item(i, j).setForeground(Qt.GlobalColor.black)
        table.cellClicked.connect(lambda row, col, t=table, c=cell_widgets: on_cell_click(row, col, t, c))

        tab_layout.addWidget(table)
        tab_widget.addTab(tab, f"{section} - {semester}")

    # Export/Close buttons
    btn_layout = QHBoxLayout()
    export_pdf_btn = QPushButton("Export to PDF")
    export_excel_btn = QPushButton("Export to Excel")
    close_btn = QPushButton("Close")
    btn_layout.addWidget(export_pdf_btn)
    btn_layout.addWidget(export_excel_btn)
    btn_layout.addStretch()
    btn_layout.addWidget(close_btn)
    layout.addLayout(btn_layout)

    def build_sem_sec_groups_from_current():
        groups = {}
        for key_tuple, details in current_timetable.items():
            semester, section, day, time = key_tuple
            group_key = (semester, section)
            if group_key not in groups:
                groups[group_key] = {}
            if time not in groups[group_key]:
                groups[group_key][time] = {}
            if day not in groups[group_key][time]:
                groups[group_key][time][day] = []
            groups[group_key][time][day].append(details)
        return groups

    def export_to_pdf(optimized_timetable_data, time_slots_cols, grouped_display_data, metadata, title):
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            import os

            # Try to import reportlab
            try:
                from reportlab.lib.pagesizes import inch
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib import colors as reportlab_colors
            except ImportError:
                QMessageBox.critical(None, "Missing Library", "ReportLab library is not installed.")
                return

            # Ask user for file path
            filepath, _ = QFileDialog.getSaveFileName(
                None,
                "Save Timetable as PDF",
                "",
                "PDF files (*.pdf)"
            )
            if not filepath:
                return

            if not filepath.lower().endswith('.pdf'):
                filepath += '.pdf'

            doc = SimpleDocTemplate(filepath, pagesize=(30*inch, 20*inch), rightMargin=2*inch)
            story = []
            styles = getSampleStyleSheet()

            # Header info
            styles['h1'].alignment = 1
            story.append(Paragraph(metadata.get("college_name", ""), styles['h1']))
            story.append(Paragraph(title, styles['h2']))
            story.append(Paragraph(f"Effective Date: {metadata.get('effective_date', '')}", styles['Normal']))
            story.append(Paragraph(f"Department: {metadata.get('department_name', '')}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

            class_keys = list(grouped_display_data.keys())
            num_classes = len(class_keys)
            per_page = 2

            for idx, class_key in enumerate(class_keys):
                semester, section = class_key

                # Determine the specific room for this class/section
                room_for_this_section = "N/A"
                for lecture_details in optimized_timetable_data.values():
                    if lecture_details['class_section'] == section and lecture_details['semester'] == semester:
                        room_for_this_section = str(lecture_details['room'])
                        break

                # Add class header
                class_header = f"{semester} {section} Room: {room_for_this_section}"
                story.append(Paragraph(class_header, styles['Heading2']))
                story.append(Spacer(1, 0.1*inch))

                # Get unique time slots and days
                time_slots = sorted(list(set(slot.split(" ", 1)[1] for slot in time_slots_cols)))
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

                # Prepare table data
                table_data = []
                header_row = ["Time"] + days
                table_data.append(header_row)

                for time_slot in time_slots:
                    row = [time_slot]
                    for day in days:
                        cell_content = ""
                        full_slot = f"{day} {time_slot}"
                        for key, details in optimized_timetable_data.items():
                            if (details['time_slot'] == full_slot and 
                                details['class_section'] == section and 
                                details['semester'] == semester):
                                cell_content = (f"{details['course_name']}\n"
                                                f"({details['course_code']})\n"
                                                f"{details.get('course_indicators', '')}\n"
                                                f"{details['teacher']}")
                        row.append(cell_content)
                    table_data.append(row)

                # Create and style the table
                col_widths = [2*inch] + [3*inch] * len(days)
                table = Table(table_data, colWidths=col_widths, rowHeights=[0.4*inch] + [1.2*inch] * len(time_slots))
                style = TableStyle([
                    ('GRID', (0,0), (-1,-1), 1, reportlab_colors.black),
                    ('BOX', (0,0), (-1,-1), 2, reportlab_colors.black),
                    ('BACKGROUND', (0,0), (-1,0), reportlab_colors.HexColor('#0d6efd')),
                    ('TEXTCOLOR', (0,0), (-1,0), reportlab_colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 12),
                    ('FONTSIZE', (0,1), (-1,-1), 10),
                    ('LEADING', (0,0), (-1,-1), 14),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ])
                table.setStyle(style)
                story.append(table)
                story.append(Spacer(1, 0.5*inch))

                # Add page break after every 2 timetables, except after the last one
                if (idx + 1) % per_page == 0 and (idx + 1) < num_classes:
                    story.append(PageBreak())

            doc.build(story)
            QMessageBox.information(None, "Success", f"Timetable exported to {filepath}")

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Export Failed", f"Could not export to PDF: {e}")
            import traceback
            traceback.print_exc()

    def export_to_excel_generated(current_timetable, available_time_slots, grouped_display_data, metadata, title):
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            import os

            # Try to import pandas and xlsxwriter
            try:
                import pandas as pd
            except ImportError:
                QMessageBox.critical(None, "Missing Library", "Pandas library is not installed.")
                return

            # Ask user for file path
            filepath, _ = QFileDialog.getSaveFileName(
                None,
                "Save Timetable as Excel",
                "",
                "Excel files (*.xlsx)"
            )
            if not filepath:
                return

            if not filepath.lower().endswith('.xlsx'):
                filepath += '.xlsx'

            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                for (semester, section), data in grouped_display_data.items():
                    # Prepare table data
                    time_slots = sorted(list(set(slot.split(" ", 1)[1] for slot in available_time_slots)))
                    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                    table_data = []
                    header_row = ["Time"] + days
                    table_data.append(header_row)
                    for time_slot in time_slots:
                        row = [time_slot]
                        for day in days:
                            cell_content = ""
                            if time_slot in data and day in data[time_slot]:
                                details = data[time_slot][day][0]
                                cell_content = (
                                    f"{details['course_name']}\n"
                                    f"({details['course_code']})\n"
                                    f"{details.get('course_indicators', '')}\n"
                                    f"{details['teacher']}\n"
                                )
                            row.append(cell_content)
                        table_data.append(row)
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                    sheet_name = f"{section}-{semester}"[:31]
                    # Write DataFrame starting from row 5 (to leave space for metadata)
                    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=5)
                    worksheet = writer.sheets[sheet_name]
                    # Write metadata in the first rows
                    worksheet.write(0, 0, metadata.get("college_name", ""))
                    worksheet.write(1, 0, title)
                    worksheet.write(2, 0, f"Effective Date: {metadata.get('effective_date', '')}")
                    worksheet.write(3, 0, f"Department: {metadata.get('department_name', '')}")
                    # Find the room for this section/semester
                    room_for_this_section = "N/A"
                    for details in current_timetable.values():
                        if details['class_section'] == section and details.get('semester') == semester:
                            room_for_this_section = str(details['room'])
                            break
                    worksheet.write(4, 0, f"Semester: {semester}, Section: {section}, Room: {room_for_this_section}")
            QMessageBox.information(None, "Success", f"Timetable exported to {filepath}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Export Failed", f"Could not export to Excel: {e}")
            import traceback
            traceback.print_exc()

    export_pdf_btn.clicked.connect(lambda: export_to_pdf(
        current_timetable, available_time_slots, build_sem_sec_groups_from_current(),
        timetable_metadata, display_title
    ))
    export_excel_btn.clicked.connect(lambda: export_to_excel_generated(
        current_timetable, available_time_slots, build_sem_sec_groups_from_current(),
        timetable_metadata, display_title
    ))
    close_btn.clicked.connect(dialog.close)

    dialog.exec()
    
    