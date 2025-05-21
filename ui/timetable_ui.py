import tkinter as tk
from tkinter import messagebox, ttk, filedialog # Added filedialog
import datetime
import random # Not directly used in this snippet but often in GA context
import sqlite3
from datetime import datetime, timedelta
from algorithms.timetable_ga import TimetableGeneticAlgorithm
# Ensure timetable_db functions are correctly imported
from db.timetable_db import init_timetable_db, fetch_id_from_name, load_timetable, load_timetable_for_ga
from utils.timeslots import generate_time_slots

def validate_time_format(time_str):
    try:
        datetime.strptime(time_str.strip(), "%I:%M %p")
        return True
    except ValueError:
        return False

# For PDF and Excel export
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors as reportlab_colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Global variables
timetable_entries = []
editing_index = None
TT_header_frame = None
TT_frame = None
tt_treeview = None
tt_teacher_entry = None
tt_course_entry = None
tt_course_code_entry = None
tt_indicators_entry = None
tt_room_entry = None
tt_class_entry = None
tt_semester_entry = None # Changed from semester_cb
tt_generate_button = None
root = None
conn = None  # Database connection
college_name_var = None
timetable_title_var = None
effective_date_var = None
department_name_var = None
checked_items = {}

def initialize(master, title_font, header_font, normal_font, button_font, return_home_func):
    global TT_header_frame, TT_frame, tt_treeview, root, conn
    global tt_teacher_entry, tt_course_entry, tt_course_code_entry, tt_indicators_entry, tt_room_entry, tt_class_entry
    global tt_generate_button, tt_semester_entry, shift_cb # Removed start_time_var, end_time_var if not used globally here

    root = master

    init_timetable_db()                     # sets up tables on module‑level conn
    from db.timetable_db import conn as db_conn
    conn = db_conn

    TT_header_frame = tk.Frame(root, bg="#0d6efd", height=60)
    header_label = tk.Label(TT_header_frame, text="Timetable Data Entry", bg="#0d6efd", fg="white", font=title_font)
    header_label.pack(side="left", padx=20, pady=15)
    btn_home = tk.Button(TT_header_frame, text="Home", command=return_home_func,
                         bg="white", fg="#0d6efd", font=normal_font, padx=15, pady=5, borderwidth=0)
    btn_home.pack(side="right", padx=20, pady=10)

    TT_frame = tk.Frame(root, bg="white")
    TT_frame.grid_rowconfigure(0, weight=1)
    TT_frame.grid_rowconfigure(1, weight=3)
    TT_frame.grid_columnconfigure(0, weight=1)

    left = tk.Frame(TT_frame, bg="white", padx=20, pady=20)
    left.grid(row=0, column=0, sticky="nsew")

    right = tk.Frame(TT_frame, bg="#f8f9fa", padx=20, pady=20)
    right.grid(row=1, column=0, sticky="nsew")

    tk.Label(left, text="Enter Timetable Details", bg="white", fg="#212529", font=header_font).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")
    ttk.Separator(left, orient='horizontal').grid(row=1, column=0, columnspan=6, sticky='ew', pady=5)

    tk.Label(left, text="Semester/Label:", bg="white").grid(row=2, column=0, pady=5, sticky="w")
    tt_semester_entry = ttk.Entry(left, font=normal_font, width=12)
    tt_semester_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(0,10))

    tk.Label(left, text="Shift:", bg="white").grid(row=2, column=2, pady=5, sticky="w")
    shift_cb = ttk.Combobox(left, values=["Morning", "Evening"], width=10, state="readonly")
    shift_cb.grid(row=2, column=3, sticky="ew", pady=5)
    shift_cb.set("Morning")
    shift_cb.bind("<<ComboboxSelected>>", lambda event: clear_entries_on_change(event, "shift"))

    tk.Label(left, text="Class/Section:", bg="white", fg="#495057", font=normal_font).grid(row=3, column=0, pady=5, sticky="w")
    tt_class_entry = ttk.Entry(left, font=normal_font)
    tt_class_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(0,10))

    tk.Label(left, text="Teacher Name:", bg="white", fg="#495057", font=normal_font).grid(row=3, column=2, pady=5, sticky="w")
    tt_teacher_entry = ttk.Entry(left, font=normal_font)
    tt_teacher_entry.grid(row=3, column=3, sticky="ew", pady=5)

    tk.Label(left, text="Course Name:", bg="white", fg="#495057", font=normal_font).grid(row=4, column=0, pady=5, sticky="w")
    tt_course_entry = ttk.Entry(left, font=normal_font)
    tt_course_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=(0,10))

    tk.Label(left, text="Course Code:", bg="white", fg="#495057", font=normal_font).grid(row=4, column=2, pady=5, sticky="w")
    tt_course_code_entry = ttk.Entry(left, font=normal_font)
    tt_course_code_entry.grid(row=4, column=3, sticky="ew", pady=5)

    tk.Label(left, text="Indicators (e.g., Lab C):", bg="white", fg="#495057", font=normal_font).grid(row=5, column=0, pady=5, sticky="w")
    tt_indicators_entry = ttk.Entry(left, font=normal_font)
    tt_indicators_entry.grid(row=5, column=1, sticky="ew", pady=5, padx=(0,10))

    tk.Label(left, text="Room:", bg="white", fg="#495057", font=normal_font).grid(row=5, column=2, pady=5, sticky="w")
    tt_room_entry = ttk.Entry(left, font=normal_font)
    tt_room_entry.grid(row=5, column=3, sticky="ew", pady=5)

    tk.Button(left, text="Save Entry", font=button_font, bg="#198754", fg="white",
            command=save_tt_entry, padx=10, pady=5, borderwidth=0).grid(row=6, column=0, columnspan=2, pady=15, sticky="w")

    tk.Button(left, text="Edit Entry", font=button_font, bg="#ffc107", fg="black",
            command=edit_selected_entry, padx=10, pady=5, borderwidth=0).grid(row=6, column=1, pady=15, sticky="w")

    tk.Label(right, text="Saved Timetable Entries", bg="#f8f9fa", fg="#212529", font=header_font).pack(anchor="w", pady=5)
    tree_container = tk.Frame(right, bg="#f8f9fa")
    tree_container.pack(fill="both", expand=True)

    columns = ["Select","#", "Semester/Label", "Shift", "Class", "Teacher", "Course", "Code", "Indicators", "Room"]
    tt_treeview = ttk.Treeview(tree_container, columns=columns, show='headings', selectmode='browse')

    for col in columns:
        tt_treeview.heading(col, text=col)
        if col == "Select":
            tt_treeview.column(col, width=50, anchor='center', stretch=tk.NO)
        elif col == "#":
            tt_treeview.column(col, width=30, anchor='center', stretch=tk.NO)
        elif col == "Course":
            tt_treeview.column(col, width=180, anchor='w')
        elif col == "Teacher":
            tt_treeview.column(col, width=120, anchor='w')
        elif col == "Indicators":
            tt_treeview.column(col, width=100, anchor='center')
        elif col == "Semester/Label":
             tt_treeview.column(col, width=100, anchor='w')
        else:
            tt_treeview.column(col, width=80, anchor='center')

    scrollbar = ttk.Scrollbar(tree_container, orient='vertical', command=tt_treeview.yview)
    tt_treeview.configure(yscrollcommand=scrollbar.set)
    tt_treeview.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    tt_treeview.bind("<Button-1>", on_treeview_click)
    btn_frame = tk.Frame(right, bg="#f8f9fa")
    btn_frame.pack(fill='x', pady=10)

    tk.Button(btn_frame, text="Delete Selected", font=button_font, bg="#dc3545", fg="white",
              command=delete_tt_entry, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    tk.Button(btn_frame, text="Clear All Entries", font=button_font, bg="#6c757d", fg="white",
              command=clear_all_tt_entries, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)

    db_frame = tk.Frame(right, bg="#f8f9fa")
    db_frame.pack(fill='x', pady=5)
    tk.Button(db_frame, text="Save Entries to DB", font=button_font, bg="#198754", fg="white",
              command=save_to_db_ui, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    tk.Button(db_frame, text="Load from DB", font=button_font, bg="#0d6efd", fg="white",
              command=load_from_db_ui, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)

    tt_generate_button = tk.Button(btn_frame, text="Generate Timetable", font=button_font, bg="#007bff", fg="white",
                                   command=generate_timetable_dialog, padx=10, pady=5, borderwidth=0)
    tt_generate_button.pack(side='right', padx=5)

    global college_name_var, timetable_title_var, effective_date_var, department_name_var
    college_name_var = tk.StringVar(value="GOVT. ISLAMIA GRADUATE COLLEGE, CIVIL LINES, LAHORE")
    timetable_title_var = tk.StringVar(value="TIME TABLE FOR BS PROGRAMS")
    effective_date_var = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))
    department_name_var = tk.StringVar(value="DEPARTMENT OF COMPUTER SCIENCE")

    update_tt_treeview()

def clear_all_tt_entries():
    global timetable_entries, editing_index
    if not timetable_entries:
        messagebox.showinfo("Info", "No entries to clear")
        return
    if messagebox.askyesno("Confirm", "Are you sure you want to clear all current timetable entries? This does not affect the database until you save."):
        timetable_entries.clear()
        editing_index = None
        clear_tt_form()
        update_tt_treeview()
        messagebox.showinfo("Cleared", "All current entries have been cleared.")

def edit_selected_entry():
    selected = [idx for idx, checked in checked_items.items() if checked]
    if not selected:
        messagebox.showwarning("No Selection", "Please select an entry to edit.")
        return
    idx = selected[0]
    if 0 <= idx < len(timetable_entries):
        entry_to_edit = timetable_entries[idx]
        clear_tt_form()
        tt_semester_entry.insert(0, entry_to_edit.get('semester', ''))
        shift_cb.set(entry_to_edit.get('shift', 'Morning'))
        tt_class_entry.insert(0, entry_to_edit.get('class_section_name', ''))
        tt_teacher_entry.insert(0, entry_to_edit.get('teacher_name', ''))
        tt_course_entry.insert(0, entry_to_edit.get('course_name', ''))
        tt_course_code_entry.insert(0, entry_to_edit.get('course_code', ''))
        tt_indicators_entry.insert(0, entry_to_edit.get('course_indicators', ''))
        tt_room_entry.insert(0, str(entry_to_edit.get('room_name', '')))
        global editing_index
        editing_index = idx
    else:
        messagebox.showerror("Error", "Invalid selection.")

def save_tt_entry():
    global editing_index, timetable_entries
    
    # Get form values
    teacher_name = tt_teacher_entry.get().strip()
    course_name = tt_course_entry.get().strip()
    course_code = tt_course_code_entry.get().strip()
    indicators = tt_indicators_entry.get().strip()
    room_name = tt_room_entry.get().strip()
    class_section_name = tt_class_entry.get().strip()
    semester_label = tt_semester_entry.get().strip()
    shift = shift_cb.get().strip()

    # Validation check
    if not all([teacher_name, course_name, course_code, room_name, class_section_name, semester_label, shift]):
        messagebox.showwarning("Missing Fields", "All fields except Indicators must be filled.")
        return False

    if not teacher_name.replace(" ", "").isalpha():
        messagebox.showwarning("Invalid Teacher Name", "Teacher name should primarily contain letters.")
    if not course_code.isalnum() and '-' not in course_code:
        messagebox.showwarning("Invalid Course Code", "Course code should be alphanumeric (e.g., CS101, CC-214).")
        return
    try:
        int(room_name)
    except ValueError:
        messagebox.showwarning("Invalid Room", "Room should be a number (e.g., 71).")
        return
    if not class_section_name.replace(" ", "").isalnum():
         messagebox.showwarning("Invalid Class/Section", "Class/Section must be alphanumeric (e.g., BSCS G1, A).")
         return

    entry_data = {
        "teacher_name": teacher_name,
        "course_name": course_name,
        "course_code": course_code,
        "course_indicators": indicators,
        "room_name": room_name,
        "class_section_name": class_section_name,
        "semester": semester_label,
        "shift": shift,
        "teacher_id": None,
        "course_id": None,
        "room_id": None,
        "class_section_id": None
    }

    if editing_index is not None and 0 <= editing_index < len(timetable_entries):
        # Update existing entry
        timetable_entries[editing_index] = entry_data
        action = "updated"
    else:
        # Add new entry
        timetable_entries.append(entry_data)
        action = "added"

    # Clear form and reset editing state
    # clear_tt_form()
    
    # Update display
    update_tt_treeview()
    messagebox.showinfo("Success", f"Entry {action} successfully.")
    return True


def save_timetable_from_treeview():
    global timetable_entries # Removed conn from here as it's not passed.

    current_semester_label = tt_semester_entry.get().strip()
    current_shift = shift_cb.get().strip()

    if not current_shift:
        messagebox.showwarning("Missing Data", "Please select Shift to define the context for saving.")
        return

    entries_to_save = [
        entry for entry in timetable_entries
        if entry["shift"] == current_shift and \
           (not current_semester_label or entry["semester"] == current_semester_label)
    ]

    context_msg = f"Shift: {current_shift}"
    if current_semester_label:
        context_msg += f", Label: {current_semester_label}"

    if not entries_to_save:
        messagebox.showinfo("No Data", f"No entries found in the current view for {context_msg} to save to DB.")
        return

    if not messagebox.askyesno("Confirm Save", f"Save {len(entries_to_save)} entries for {context_msg} to the database?"):
        return

    saved_count = 0
    failed_count = 0
    
    with conn: # This uses the 'conn' from timetable_ui.py's global scope
        for entry in entries_to_save:
            try:
                # MODIFICATION: Removed 'conn' argument from calls to fetch_id_from_name
                teacher_id = fetch_id_from_name("teachers", entry["teacher_name"])
                course_id = fetch_id_from_name("courses", entry["course_name"],
                                               teacher_id=teacher_id,
                                               code=entry["course_code"],
                                               indicators=entry["course_indicators"])
                room_id = fetch_id_from_name("rooms", entry["room_name"])
                class_section_id = fetch_id_from_name("class_sections", entry["class_section_name"],
                                                     semester=entry["semester"], shift=entry["shift"])

                if not all([teacher_id, course_id, room_id, class_section_id]):
                    messagebox.showerror("Error", f"Could not resolve IDs for entry: {entry['course_name']}. Skipping.")
                    failed_count +=1
                    continue

                cur = conn.cursor() # Using timetable_ui.py's conn for this check
                cur.execute('''SELECT id FROM timetable WHERE
                               teacher_id = ? AND course_id = ? AND room_id = ? AND
                               class_section_id = ? AND semester = ? AND shift = ?''',
                            (teacher_id, course_id, room_id, class_section_id, entry["semester"], entry["shift"]))
                if cur.fetchone():
                    print(f"Entry for {entry['course_name']} already exists in DB. Skipping.")
                    failed_count +=1
                    continue

                # Using timetable_ui.py's conn for insert
                conn.execute('''
                    INSERT INTO timetable (teacher_id, course_id, room_id, class_section_id, semester, shift)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (teacher_id, course_id, room_id, class_section_id, entry["semester"], entry["shift"]))
                saved_count += 1
            except sqlite3.Error as e: # This will catch errors from operations using timetable_ui.py's conn
                messagebox.showerror("Database Error", f"Error saving entry {entry['course_name']}: {e}")
                failed_count +=1
            except Exception as e: # This will catch errors from fetch_id_from_name if they propagate
                messagebox.showerror("Unexpected Error", f"Error processing entry {entry['course_name']}: {e}")
                failed_count +=1

    if saved_count > 0:
        conn.commit() # Commit changes made via timetable_ui.py's conn
        messagebox.showinfo("Success", f"{saved_count} entries saved to database for {context_msg}.")
    if failed_count > 0:
        messagebox.showwarning("Save Incomplete", f"{failed_count} entries could not be saved or were duplicates.")
    if saved_count == 0 and failed_count == 0 :
        messagebox.showinfo("No Action", "No new entries to save to the database for the current view.")


def clear_tt_form():
    tt_teacher_entry.delete(0, tk.END)
    tt_course_entry.delete(0, tk.END)
    tt_course_code_entry.delete(0, tk.END)
    tt_indicators_entry.delete(0, tk.END)
    tt_room_entry.delete(0, tk.END)
    tt_class_entry.delete(0, tk.END)
    tt_semester_entry.delete(0, tk.END)
    global editing_index
    editing_index = None

def on_treeview_click(event):
    region = tt_treeview.identify("region", event.x, event.y)
    if region == "cell":
        row_id = tt_treeview.identify_row(event.y)
        col = tt_treeview.identify_column(event.x)
        if col == "#1":  # "Select" column
            idx = int(row_id)
            checked_items[idx] = not checked_items.get(idx, False)
            update_tt_treeview()

def update_tt_treeview():
    global timetable_entries, tt_treeview, checked_items
    for item in tt_treeview.get_children():
        tt_treeview.delete(item)

    current_semester_label = tt_semester_entry.get().strip()
    current_shift = shift_cb.get().strip()

    display_entries = []
    if current_shift:
        display_entries = [
            e for e in timetable_entries
            if e.get('shift') == current_shift and \
               (not current_semester_label or e.get('semester') == current_semester_label)
        ]

    for i, entry in enumerate(display_entries):
        checked = checked_items.get(i, False)
        checkbox = "☑" if checked else "☐"
        values_to_insert = (
            checkbox,
            i + 1,
            entry.get('semester', ''),
            entry.get('shift', ''),
            entry.get('class_section_name', 'N/A'),
            entry.get('teacher_name', 'N/A'),
            entry.get('course_name', 'N/A'),
            entry.get('course_code', 'N/A'),
            entry.get('course_indicators', ''),
            entry.get('room_name', 'N/A')
        )
        tt_treeview.insert('', 'end', values=values_to_insert, iid=str(i))

def delete_tt_entry():
    global timetable_entries, editing_index
    
    selected_items = tt_treeview.selection()
    
    if not selected_items:
        messagebox.showwarning("Selection Error", "Please select an entry to delete first.")
        return False
        
    selected_iid = selected_items[0]
    
    try:
        index = int(selected_iid)
        if 0 <= index < len(timetable_entries):
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry? This will also remove it from the database."):
                entry = timetable_entries[index]
                
                # Delete from database if entry has an ID
                if 'entry_id' in entry:
                    from db.timetable_db import delete_timetable_entry_from_db
                    if delete_timetable_entry_from_db(entry['entry_id']):
                        print(f"Entry {entry['entry_id']} deleted from database")
                    else:
                        print(f"Warning: Could not delete entry {entry['entry_id']} from database")
                
                # Remove from local list
                timetable_entries.pop(index)
                if editing_index is not None:
                    if editing_index == index:
                        editing_index = None
                        clear_tt_form()
                    elif editing_index > index:
                        editing_index -= 1
                update_tt_treeview()
                messagebox.showinfo("Success", "Entry deleted successfully.")
                return True
    except (ValueError, IndexError):
        messagebox.showerror("Error", "Invalid selection index.")
    
    return False


def edit_tt_entry(event):
    global editing_index
    
    selected_items = tt_treeview.selection()
    if not selected_items:
        return
    
    try:
        selected_iid = selected_items[0]
        index = int(selected_iid)
        
        if 0 <= index < len(timetable_entries):
            editing_index = index
            entry_to_edit = timetable_entries[index]
            
            # Clear and populate form
            clear_tt_form()
            
            # Update form fields
            tt_semester_entry.insert(0, entry_to_edit.get('semester', ''))
            shift_cb.set(entry_to_edit.get('shift', 'Morning'))
            tt_class_entry.insert(0, entry_to_edit.get('class_section_name', ''))
            tt_teacher_entry.insert(0, entry_to_edit.get('teacher_name', ''))
            tt_course_entry.insert(0, entry_to_edit.get('course_name', ''))
            tt_course_code_entry.insert(0, entry_to_edit.get('course_code', ''))
            tt_indicators_entry.insert(0, entry_to_edit.get('course_indicators', ''))
            tt_room_entry.insert(0, str(entry_to_edit.get('room_name', '')))
            
            # Ensure editing_index is set
            editing_index = index
            
    except (ValueError, IndexError):
        messagebox.showerror("Error", "Invalid selection index.")
        clear_tt_form()
        editing_index = None


def clear_selection_if_outside_tree(event):
    widget = event.widget
    if widget == tt_treeview:
        return
        
    # Check if click is in an entry widget or combobox
    interactive_widgets = [
        tt_teacher_entry, tt_course_entry, tt_course_code_entry, 
        tt_indicators_entry, tt_room_entry, tt_class_entry, 
        tt_semester_entry, shift_cb
    ]
    
    if widget in interactive_widgets or widget.winfo_parent() in [w.winfo_parent() for w in interactive_widgets]:
        return
        
    # Clear selection and form if click is outside
    tt_treeview.selection_remove(tt_treeview.selection())
    clear_tt_form()


def clear_selection(event):
    if not tt_treeview.identify_row(event.y):
        if tt_treeview.selection():
            tt_treeview.selection_remove(tt_treeview.selection())
            clear_tt_form()
            global editing_index
            editing_index = None


def generate_timetable_dialog():
    global college_name_var, timetable_title_var, effective_date_var, department_name_var

    dialog = tk.Toplevel(root)
    dialog.title("Configure Timetable Generation")
    dialog.geometry("800x700")
    dialog.resizable(False, False)

    dialog.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f'+{x}+{y}')

    main_frame = tk.Frame(dialog, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    tk.Label(main_frame, text="Timetable Metadata", font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))

    tk.Label(main_frame, text="College Name:").grid(row=1, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=college_name_var, width=60).grid(row=1, column=1, sticky="ew", pady=2)

    tk.Label(main_frame, text="Timetable Title:").grid(row=2, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=timetable_title_var, width=60).grid(row=2, column=1, sticky="ew", pady=2)

    tk.Label(main_frame, text="Effective Date (DD-MM-YYYY):").grid(row=3, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=effective_date_var, width=20).grid(row=3, column=1, sticky="w", pady=2)

    tk.Label(main_frame, text="Department Name:").grid(row=4, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=department_name_var, width=60).grid(row=4, column=1, sticky="ew", pady=2)

    ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)

    tk.Label(main_frame, text="Generation Parameters", font=("Helvetica", 12, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0,10))

    tk.Label(main_frame, text="Shift:", anchor="w").grid(row=7, column=0, sticky="w", pady=5)
    shift_options = ["Morning", "Evening"]
    shift_dialog_var = tk.StringVar(value=shift_cb.get())
    shift_dialog_cb = ttk.Combobox(main_frame, values=shift_options, textvariable=shift_dialog_var, width=18, state="readonly")
    shift_dialog_cb.grid(row=7, column=1, sticky="w", pady=5)

    tk.Label(main_frame, text="Lectures per Course:").grid(row=9, column=0, sticky="w", pady=5)
    lectures_var = tk.StringVar(value="3")
    lectures_cb = ttk.Combobox(main_frame, values=["1", "2", "3", "4"], textvariable=lectures_var, width=18, state="readonly")
    lectures_cb.grid(row=9, column=1, sticky="w", pady=5)

    tk.Label(main_frame, text="Lecture Duration (minutes):").grid(row=10, column=0, sticky="w", pady=5)
    duration_var = tk.StringVar(value="60")
    duration_cb = ttk.Combobox(main_frame, values=["45", "50", "55", "60", "90", "120"], textvariable=duration_var, width=18, state="readonly")
    duration_cb.grid(row=10, column=1, sticky="w", pady=5)

    tk.Label(main_frame, text="Daily Start Time:").grid(row=11, column=0, sticky="w", pady=5)
    start_time_dialog_var = tk.StringVar(value="01:00 PM" if shift_dialog_var.get() == "Evening" else "08:00 AM")
    start_time_entry = ttk.Entry(main_frame, textvariable=start_time_dialog_var, width=20)
    start_time_entry.grid(row=11, column=1, sticky="w", pady=5)

    tk.Label(main_frame, text="Daily End Time:").grid(row=12, column=0, sticky="w", pady=5)
    end_time_dialog_var = tk.StringVar(value="06:00 PM" if shift_dialog_var.get() == "Evening" else "01:00 PM")
    end_time_entry = ttk.Entry(main_frame, textvariable=end_time_dialog_var, width=20)
    end_time_entry.grid(row=12, column=1, sticky="w", pady=5)

    tk.Label(main_frame, text="Days:").grid(row=13, column=0, sticky="w", pady=5)
    days_frame = tk.Frame(main_frame)
    days_frame.grid(row=13, column=1, sticky="w")
    day_vars = {}
    days_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for i, day_text in enumerate(days_options):
        var = tk.BooleanVar(value=True if day_text != "Saturday" else False)
        cb_day = ttk.Checkbutton(days_frame, text=day_text, variable=var) # Renamed cb to cb_day
        cb_day.pack(side="left", padx=2)
        day_vars[day_text] = var

    # --- Fetch all courses from the database for dropdown ---
    from db.timetable_db import conn as db_conn
    cur = db_conn.cursor()
    cur.execute("SELECT code, name FROM courses")
    course_list = cur.fetchall()
    course_options = [f"{code} - {name}" for code, name in course_list]

    # Add a frame for course-specific exceptions
    tk.Label(main_frame, text="Course Exceptions", font=("Helvetica", 12, "bold")).grid(row=15, column=0, columnspan=2, sticky="w", pady=(10,5))
    
    exceptions_frame = ttk.LabelFrame(main_frame, text="Course-specific lecture frequencies")
    exceptions_frame.grid(row=16, column=0, columnspan=2, sticky="ew", pady=5)

    # Create a treeview for exceptions
    columns = ("Course Code", "Course Name", "Lectures/Week")
    exceptions_tree = ttk.Treeview(exceptions_frame, columns=columns, show="headings", height=5)
    for col in columns:
        exceptions_tree.heading(col, text=col)
        exceptions_tree.column(col, width=150)
    exceptions_tree.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    # Add scrollbar
    scrollbar = ttk.Scrollbar(exceptions_frame, orient="vertical", command=exceptions_tree.yview)
    scrollbar.grid(row=0, column=2, sticky="ns")
    exceptions_tree.configure(yscrollcommand=scrollbar.set)

    # Entry fields for adding exceptions
    entry_frame = ttk.Frame(exceptions_frame)
    entry_frame.grid(row=1, column=0, columnspan=3, pady=5)

    # --- Use Combobox for course selection ---
    selected_course_var = tk.StringVar()
    freq_var = tk.StringVar(value="1")

    course_cb = ttk.Combobox(entry_frame, textvariable=selected_course_var, values=course_options, width=35, state="readonly")
    course_cb.grid(row=0, column=0, padx=5)
    ttk.Combobox(entry_frame, textvariable=freq_var, values=["1", "2", "3", "4"], width=5).grid(row=0, column=1, padx=5)

    def add_exception():
        course_str = selected_course_var.get()
        freq = freq_var.get()
        if course_str:
            code, name = course_str.split(" - ", 1)
            exceptions_tree.insert("", "end", values=(code, name, freq))
            selected_course_var.set("")
            freq_var.set("1")

    def remove_exception():
        selected = exceptions_tree.selection()
        if selected:
            exceptions_tree.delete(selected[0])

    ttk.Button(entry_frame, text="Add", command=add_exception).grid(row=0, column=2, padx=5)
    ttk.Button(entry_frame, text="Remove", command=remove_exception).grid(row=0, column=3, padx=5)

    dialog_btn_frame = tk.Frame(main_frame)
    dialog_btn_frame.grid(row=17, column=0, columnspan=2, pady=20)

    def validate_and_run_generation():
        try:
            meta = {
                "college_name": college_name_var.get(),
                "timetable_title": timetable_title_var.get(),
                "effective_date": effective_date_var.get(),
                "department_name": department_name_var.get()
            }

            gen_shift = shift_dialog_var.get()
            lectures_p_course = int(lectures_var.get())
            lecture_dur = int(duration_var.get())
            start_t_str = start_time_dialog_var.get()
            end_t_str = end_time_dialog_var.get()

            selected_days = [day for day, var in day_vars.items() if var.get()]
            if not selected_days:
                messagebox.showwarning("No Days Selected", "Please select at least one day for the timetable.")
                return

            if not validate_time_format(start_t_str) or not validate_time_format(end_t_str):
                messagebox.showerror("Invalid Time", "Please enter time in format HH:MM AM/PM (e.g., 07:30 AM)")
                return

            # Collect exceptions
            exceptions = {}
            for item in exceptions_tree.get_children():
                values = exceptions_tree.item(item)["values"]
                exceptions[values[0]] = int(values[2])  # Map course code to frequency

            run_timetable_generation(
                shift=gen_shift,
                lectures_per_course=lectures_p_course,
                lecture_duration=lecture_dur,
                start_time=start_t_str,
                end_time=end_t_str,
                days=selected_days,
                timetable_metadata=meta,
                course_exceptions=exceptions
            )
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your input values: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()


    tk.Button(dialog_btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side="left", padx=10)
    tk.Button(dialog_btn_frame, text="Generate", command=validate_and_run_generation, width=10, bg="#007bff", fg="white").pack(side="right", padx=10)


def run_timetable_generation(shift, lectures_per_course, lecture_duration, start_time, 
                           end_time, days, timetable_metadata, course_exceptions=None):
    try:
        print(f"Loading GA data for Shift: {shift}")
        db_rows_for_ga = load_timetable_for_ga(shift=shift)

        if not db_rows_for_ga:
            messagebox.showwarning("No Data for GA", f"No timetable entries found in the database for Shift: {shift} to generate a timetable.")
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
            messagebox.showwarning("Processing Error", "Failed to prepare entries for the Genetic Algorithm.")
            return

        time_slots = generate_time_slots(days, start_time, end_time, lecture_duration, break_duration=10)
        print("Generated UI time slots for GA:", len(time_slots))

        if not time_slots:
            messagebox.showwarning("Configuration Error", "Could not generate any valid time slots. Check start/end times and duration.")
            return

        ga = TimetableGeneticAlgorithm(
            entries=ga_entries,
            time_slots_input=time_slots,
            lectures_per_course=lectures_per_course,
            course_exceptions=course_exceptions,
            population_size=100,
            max_generations=100,
            mutation_rate=0.15
        )

        optimized_schedule, best_fitness = ga.evolve() # Corrected line

        print(f"Debug: GA returned optimized schedule with fitness: {best_fitness}")
        print(f"Debug: Optimized schedule contains {len(optimized_schedule or {})} lecture entries")


        if optimized_schedule is None or not optimized_schedule: # Check if the schedule is empty or None
            messagebox.showwarning("Generation Failed", "The genetic algorithm could not generate a valid timetable with the given constraints and data.")
            return

        # The rest of your function using 'optimized_schedule'
        display_title = f"{timetable_metadata['timetable_title']} - {shift} Shift"
        display_timetable(optimized_schedule, time_slots, days, timetable_metadata, display_title)

    except Exception as ex:
        messagebox.showerror("Timetable Generation Error", f"Failed to generate timetable: {ex}")
        import traceback
        traceback.print_exc()


def clear_entries_on_change(event, changed_field):
    global editing_index
    update_tt_treeview()


def display_timetable(optimized_timetable_data, available_time_slots,
                      scheduled_days, timetable_metadata, display_title):
    win = tk.Toplevel(root)
    win.title(display_title)
    win.geometry("1400x900")
    win.state('zoomed')

    # Create main container frame
    main_container = tk.Frame(win)
    main_container.pack(fill="both", expand=True)

    # Metadata frame at top
    meta_frame = tk.Frame(main_container, pady=10)
    meta_frame.pack(fill="x")

    # Metadata display
    tk.Label(meta_frame, text=timetable_metadata.get("college_name", "College Name N/A"), 
            font=("Helvetica", 16, "bold")).pack()
    tk.Label(meta_frame, text=timetable_metadata.get("timetable_title", "Timetable"), 
            font=("Helvetica", 14)).pack()
    tk.Label(meta_frame, text=f"Effective Date: {timetable_metadata.get('effective_date', 'N/A')}", 
            font=("Helvetica", 10)).pack()
    tk.Label(meta_frame, text=f"Department: {timetable_metadata.get('department_name', 'N/A')}", 
            font=("Helvetica", 10, "italic")).pack()
    
    # Add separator
    ttk.Separator(main_container, orient='horizontal').pack(fill='x', padx=20, pady=5)

    # Add export buttons at the top
    export_btn_frame = tk.Frame(main_container, pady=10)
    export_btn_frame.pack(fill="x", padx=20)

    tk.Button(export_btn_frame, text="Export to PDF",
             command=lambda: export_to_pdf(optimized_timetable_data, available_time_slots, 
                                         class_sem_groups, timetable_metadata, display_title),
             bg="#dc3545", fg="white", padx=15, pady=5, 
             font=('Helvetica', 10)).pack(side="left", padx=10)

    tk.Button(export_btn_frame, text="Close", command=win.destroy,
             bg="#6c757d", fg="white", padx=15, pady=5, 
             font=('Helvetica', 10)).pack(side="right", padx=10)

    # Group data by class and semester
    class_sem_groups = {}
    for key_tuple, details in optimized_timetable_data.items():
        class_sec = key_tuple[1]
        semester = details.get('semester', 'N/A')
        group_key = (semester, class_sec)
        if group_key not in class_sem_groups:
            class_sem_groups[group_key] = {}
        day, time = details['time_slot'].split(" ", 1)
        if time not in class_sem_groups[group_key]:
            class_sem_groups[group_key][time] = {}
        if day not in class_sem_groups[group_key][time]:
            class_sem_groups[group_key][time][day] = []
        lecture_info = (f"{details['course_name']} ({details.get('course_code', 'N/A')})\n"
                        f"{details.get('course_indicators', '')}\n"
                        f"{details['teacher']}\nR: {details['room']}")
        class_sem_groups[group_key][time][day].append(lecture_info)

    # Add notebook for timetable display
    notebook = ttk.Notebook(main_container)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    # Get unique time slots (without day prefix)
    time_slots = sorted(list(set(slot.split(" ", 1)[1] for slot in available_time_slots)))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    # Create a tab for each class-semester combination
    for (semester, section), data in class_sem_groups.items():
        tab_frame = ttk.Frame(notebook)
        notebook.add(tab_frame, text=f"{section} - {semester}")

        # Columns: Time, Monday, Tuesday, ...
        tree_columns = ["Time"] + days
        tree = ttk.Treeview(tab_frame, columns=tree_columns, show="headings", style="Timetable.Treeview")

        # Configure style
        style = ttk.Style()
        style.configure("Timetable.Treeview", rowheight=100)
        style.configure("Timetable.Treeview.Heading", font=('Helvetica', 9, 'bold'))

        # Configure columns
        tree.column("Time", width=120, anchor='center', stretch=tk.NO)
        tree.heading("Time", text="Time")
        for day in days:
            tree.column(day, width=200, anchor='center')
            tree.heading(day, text=day)

        # Add data rows: each row is a time slot, columns are days
        for ts in time_slots:
            row_data = [ts]
            for day in days:
                cell_content = "\n\n".join(data.get(ts, {}).get(day, []))
                row_data.append(cell_content)
            tree.insert("", "end", values=row_data)

        # Add scrollbars
        vsb = ttk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tab_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=1)


def export_to_pdf(optimized_timetable_data, time_slots_cols, grouped_display_data, metadata, title):
    if not REPORTLAB_AVAILABLE:
        messagebox.showerror("Missing Library", "ReportLab library is not installed.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Save Timetable as PDF"
    )
    if not filepath: return

    try:
        doc = SimpleDocTemplate(filepath, pagesize=(30*inch, 20*inch), rightMargin=2*inch)
        story = []
        styles = getSampleStyleSheet()

        # Header info
        styles['h1'].alignment = 1
        story.append(Paragraph(metadata.get("college_name", ""), styles['h1']))
        story.append(Paragraph(title, styles['h2']))
        story.append(Spacer(1, 0.2*inch))

        for class_key in grouped_display_data.keys():
            semester, section = class_key  # 'section' here is the class/section name like 'G1'

            # Determine the specific room for this class/section
            # All lectures for this 'section' and 'semester' should have the same room.
            room_for_this_section = "N/A" # Default if not found
            for lecture_details in optimized_timetable_data.values():
                if lecture_details['class_section'] == section and lecture_details['semester'] == semester:
                    room_for_this_section = str(lecture_details['room']) # Ensure it's a string
                    break # Found the room for this section, assuming it's consistent
            
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

            # Simply display the data as generated by GA
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
            
            # Enhanced table styling
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

        doc.build(story)
        messagebox.showinfo("Success", f"Timetable exported to {filepath}")

    except Exception as e:
        messagebox.showerror("Export Failed", f"Could not export to PDF: {e}")
        import traceback
        traceback.print_exc()


def save_to_db_ui():
    save_timetable_from_treeview()

def load_from_db_ui():
    global timetable_entries

    current_shift = shift_cb.get().strip()
    current_semester_label = tt_semester_entry.get().strip()

    if not current_shift:
        messagebox.showwarning("Missing Context", "Please select Shift to load data for.")
        return

    confirm_msg = "Loading from database will update the current list. Entries matching the current Shift"
    if current_semester_label:
        confirm_msg += f" and Label '{current_semester_label}'"
    else:
        confirm_msg += " (any Label)"
    confirm_msg += " will be replaced if they exist in the database. Proceed?"

    if not messagebox.askyesno("Confirm Load", confirm_msg):
        return
    
    label_to_load = current_semester_label if current_semester_label else None

    print(f"Loading entries from DB for Shift: {current_shift}, Label: '{label_to_load if label_to_load else 'Any'}'")
    # loaded_db_entries should come from timetable_db.load_timetable
    loaded_db_entries = load_timetable(shift=current_shift, semester_label=label_to_load)

    temp_entries = [
        e for e in timetable_entries
        if not (
            e.get('shift') == current_shift and
            (label_to_load is None or e.get('semester') == label_to_load)
        )
    ]
    timetable_entries = temp_entries + loaded_db_entries

    update_tt_treeview()
    messagebox.showinfo("Load Complete", f"{len(loaded_db_entries)} entries loaded from database for Shift: {current_shift} (Label: '{label_to_load if label_to_load else 'Any'}') and updated in list.")


def show():
    if TT_header_frame: TT_header_frame.pack(fill="x")
    if TT_frame: TT_frame.pack(fill="both", expand=True)
    update_tt_treeview()

def hide():
    if TT_header_frame: TT_header_frame.pack_forget()
    if TT_frame: TT_frame.pack_forget()