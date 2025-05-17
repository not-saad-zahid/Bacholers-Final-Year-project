import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import random
import sqlite3
from datetime import datetime, timedelta
from algorithms.timetable_ga import TimetableGeneticAlgorithm
from db.timetable_db import init_timetable_db, fetch_id_from_name, load_timetable, load_timetable_for_ga

# Global variables
timetable_entries = []
editing_index = None
TT_header_frame = None
TT_frame = None
tt_treeview = None
tt_teacher_entry = None
tt_course_entry = None
tt_room_entry = None
tt_class_entry = None
tt_generate_button = None
root = None
conn = None  # Database connection


def initialize(master, title_font, header_font, normal_font, button_font, return_home_func):
    global TT_header_frame, TT_frame, tt_treeview, root
    global tt_teacher_entry, tt_course_entry, tt_room_entry, tt_class_entry, tt_generate_button, semester_cb, shift_cb, start_time_var, end_time_var
    global conn  # Declare conn as global to use it throughout the file

    # Initialize database
    conn = init_timetable_db()  # Initialize and assign the database connection

    # Header
    TT_header_frame = tk.Frame(root, bg="#0d6efd", height=60)
    TT_header_frame.pack(fill="x")
    header_label = tk.Label(TT_header_frame, text="Timetable Generator", bg="#0d6efd", fg="white", font=title_font)
    header_label.pack(side="left", padx=20, pady=15)
    btn_home = tk.Button(TT_header_frame, text="Home", command=return_home_func,
                         bg="white", fg="#0d6efd", font=normal_font, padx=15, pady=5, borderwidth=0)
    btn_home.pack(side="right", padx=20, pady=10)

    # Main frame
    TT_frame = tk.Frame(root, bg="white")
    TT_frame.pack(fill="both", expand=True)
    TT_frame.grid_rowconfigure(0, weight=1)
    TT_frame.grid_rowconfigure(1, weight=3)
    TT_frame.grid_columnconfigure(0, weight=1)

    # Left pane for inputs
    left = tk.Frame(TT_frame, bg="white", padx=20, pady=20)
    left.grid(row=0, column=0, sticky="nsew")

    # Right pane for display
    right = tk.Frame(TT_frame, bg="#f8f9fa", padx=20, pady=20)
    right.grid(row=1, column=0, sticky="nsew", columnspan=2)

    # Input heading
    tk.Label(left, text="Enter Timetable Details", bg="white", fg="#212529", font=header_font).grid(row=0, column=0, columnspan=2, pady=10, sticky="w")
    ttk.Separator(left, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)

    # Semester
    tk.Label(left, text="Semester (1-8):", bg="white").grid(row=2, column=0, pady=5)
    semester_cb = ttk.Combobox(left, values=[str(i) for i in range(1, 9)])
    semester_cb.grid(row=2, column=1, sticky="ew", pady=5)
    semester_cb.set("1")
    semester_cb.bind("<<ComboboxSelected>>", clear_entries_on_change)  # Bind event

    # Shift
    tk.Label(left, text="Shift:", bg="white").grid(row=2, column=3, pady=5)
    shift_cb = ttk.Combobox(left, values=["Morning", "Evening"])
    shift_cb.grid(row=2, column=4, sticky="ew", pady=5)
    shift_cb.set("Morning")
    shift_cb.bind("<<ComboboxSelected>>", clear_entries_on_change)  # Bind event

    # Initialize start_time_var
    start_time_var = tk.StringVar(value="8:00 AM")  # Default value
    # Initialize end_time_var
    end_time_var = tk.StringVar(value="1:00 PM")  # Default value
    
    # Teacher Name
    tk.Label(left, text="Teacher Name:", bg="white", fg="#495057", font=normal_font).grid(row=3, column=0, pady=5)
    tt_teacher_entry = ttk.Entry(left, font=normal_font)
    tt_teacher_entry.grid(row=3, column=1, sticky="ew", pady=5)

    # Course
    tk.Label(left, text="Course Name:", bg="white", fg="#495057", font=normal_font).grid(row=3, column=3, pady=5)
    tt_course_entry = ttk.Entry(left, font=normal_font)
    tt_course_entry.grid(row=3, column=4, sticky="ew", pady=5)

    # Room
    tk.Label(left, text="Room:", bg="white", fg="#495057", font=normal_font).grid(row=3, column=5, pady=5)
    tt_room_entry = ttk.Entry(left, font=normal_font)
    tt_room_entry.grid(row=3, column=6, sticky="ew", pady=5)

    # Class/Section
    tk.Label(left, text="Class/Section:", bg="white", fg="#495057", font=normal_font).grid(row=3, column=7, pady=5)
    tt_class_entry = ttk.Entry(left, font=normal_font)
    tt_class_entry.grid(row=3, column=8, sticky="ew", pady=5)

    # Save Entry button
    tk.Button(left, text="Save Entry", font=button_font, bg="#198754", fg="white",
              command=save_tt_entry, padx=10, pady=5, borderwidth=0).grid(row=6, column=0, columnspan=2, pady=15)

    # Right: Treeview
    tk.Label(right, text="Saved Timetable Entries", bg="#f8f9fa", fg="#212529", font=header_font).pack(anchor="w", pady=5)
    tree_container = tk.Frame(right, bg="#f8f9fa")
    tree_container.pack(fill="both", expand=True)
    
    # Create the Treeview widget
    tt_treeview = ttk.Treeview(tree_container,
                               columns=("#", "Semester", "Shift", "Teacher", "Course", "Room", "Class"),
                               show='headings', selectmode='browse')

    # Configure the Treeview columns
    columns = ["#", "Semester", "Shift", "Teacher", "Course", "Room", "Class"]
    for col in columns:
        tt_treeview.heading(col, text=col)
        tt_treeview.column(col, width=100, anchor='center')

    # Add a scrollbar to the Treeview
    scrollbar = ttk.Scrollbar(tree_container, orient='vertical', command=tt_treeview.yview)
    tt_treeview.configure(yscrollcommand=scrollbar.set)
    tt_treeview.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    # Bind events to the Treeview and its parent frame
    tt_treeview.bind("<Double-1>", edit_tt_entry)
    tt_treeview.bind("<Button-1>", clear_selection)
    left.bind("<Button-1>", clear_selection)  # For clicks anywhere in the root window
    right.bind("<Button-1>", clear_selection)  # For clicks anywhere in the root window

    # Action buttons
    btn_frame = tk.Frame(right, bg="#f8f9fa")
    btn_frame.pack(fill='x', pady=10)
    tk.Button(btn_frame, text="Delete Selected", font=button_font, bg="#dc3545", fg="white",
              command=delete_tt_entry, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    tk.Button(btn_frame, text="Clear All", font=button_font, bg="#6c757d", fg="white",
              command=clear_all_tt_entries, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    tt_generate_button = tk.Button(btn_frame, text="Generate Timetable", font=button_font, bg="#0d6efd", fg="white",
                                   command=generate_timetable, padx=10, pady=5, borderwidth=0)
    tt_generate_button.pack(side='right', padx=5)

    # DB buttons
    db_frame = tk.Frame(right, bg="#f8f9fa")
    db_frame.pack(fill='x', pady=10)
    tk.Button(db_frame, text="Save to DB", font=button_font, bg="#198754", fg="white",
              command=save_to_db_ui, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    tk.Button(db_frame, text="Load from DB", font=button_font, bg="#0d6efd", fg="white",
              command=load_from_db_ui, padx=10, pady=5, borderwidth=0).pack(side='right', padx=5)

    update_tt_treeview()
    
    
    
def fetch_name_from_id(table, id):
    """
    Fetch the name of a record from the database by its ID.
    """
    try:
        query = f"SELECT name FROM {table} WHERE id = ?"
        cur = conn.cursor()
        cur.execute(query, (id,))
        result = cur.fetchone()
        return result[0] if result else "Unknown"
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch name from {table}: {e}")
        return "Unknown"
    
def clear_all_tt_entries():
    global timetable_entries
    if not timetable_entries:
        messagebox.showinfo("Info", "No entries to clear")
        return
    if messagebox.askyesno("Confirm", "Are you sure you want to clear all entries?"):
        timetable_entries.clear()
        update_tt_treeview()


def save_tt_entry():
    """
    Save a timetable entry after validating the input fields.
    """
    global editing_index, timetable_entries
    teacher = tt_teacher_entry.get().strip()
    course = tt_course_entry.get().strip()
    room = tt_room_entry.get().strip()
    class_section = tt_class_entry.get().strip()
    semester = semester_cb.get().strip()
    shift = shift_cb.get().strip()

    # Validate Semester
    try:
        semester_val = int(semester)
        if semester_val < 1 or semester_val > 8:
            raise ValueError
    except ValueError:
        messagebox.showwarning("Invalid Semester", "Semester must be a number between 1 and 8.")
        return

    # Validate Shift
    if shift not in ["Morning", "Evening"]:
        messagebox.showwarning("Invalid Shift", "Shift must be either 'Morning' or 'Evening'.")
        return

    # Validate Teacher Name
    if not teacher or not teacher.isalpha():
        messagebox.showwarning("Invalid Teacher Name", "Teacher name must contain only letters and cannot be empty.")
        return

    # Validate Course Name
    if not course:
        messagebox.showwarning("Invalid Course Name", "Course name cannot be empty.")
        return

    # Validate Room (must be a positive integer)
    try:
        room_val = int(room)
        if room_val <= 0:
            raise ValueError
    except ValueError:
        messagebox.showwarning("Invalid Room", "Room must be a positive integer.")
        return

    # Validate Class/Section (must be alphanumeric)
    if not class_section or not class_section.isalnum():
        messagebox.showwarning("Invalid Class/Section", "Class/Section must be alphanumeric and cannot be empty.")
        return

    # Create the entry dictionary
    entry = {
        "teacher_id": None,  # Placeholder for teacher_id
        "course_id": None,   # Placeholder for course_id
        "room_id": None,     # Placeholder for room_id
        "class_section_id": None,  # Placeholder for class_section_id
        "semester": semester_val,
        "shift": shift,
        "teacher_name": teacher,
        "course_name": course,
        "room_name": room,
        "class_section_name": class_section
    }

    # Add or update the entry in the timetable
    if editing_index is not None:
        timetable_entries[editing_index] = entry
        editing_index = None
    else:
        timetable_entries.append(entry)

    # Update the treeview
    update_tt_treeview()


    
            
def save_timetable_from_treeview():
    """
    Save timetable entries currently displayed in the treeview to the database for the current semester and shift.
    """
    global conn

    # Get the current semester and shift
    current_semester = semester_cb.get().strip()
    current_shift = shift_cb.get().strip()

    if not current_semester or not current_shift:
        messagebox.showwarning("Missing Data", "Please select Semester and Shift before saving.")
        return

    try:
        current_semester_val = int(current_semester)
    except ValueError:
        messagebox.showwarning("Invalid Semester", "Semester must be a number (1-8).")
        return

    # Retrieve entries from the treeview
    treeview_entries = []
    for item in tt_treeview.get_children():
        values = tt_treeview.item(item, 'values')
        treeview_entries.append({
            "semester": int(values[1]),
            "shift": values[2],
            "teacher_name": values[3],
            "course_name": values[4],
            "room_name": values[5],
            "class_section_name": values[6]
        })

    # Filter entries for the current semester and shift
    filtered_entries = [
        entry for entry in treeview_entries
        if entry["semester"] == current_semester_val and entry["shift"] == current_shift
    ]

    if not filtered_entries:
        messagebox.showwarning("Empty", f"No entries found for Semester {current_semester_val} and Shift {current_shift} to save.")
        return

    # Save the filtered entries to the database
    init_timetable_db()
    with conn:
        for entry in filtered_entries:
            try:
                # Fetch IDs for teacher, course, room, and class_section
                teacher_id = fetch_id_from_name("teachers", entry["teacher_name"])
                course_id = fetch_id_from_name("courses", entry["course_name"], teacher_id=teacher_id)
                room_id = fetch_id_from_name("rooms", entry["room_name"])
                class_section_id = fetch_id_from_name(
                    "class_sections", entry["class_section_name"],
                    semester=current_semester_val, shift=current_shift
                )

                # Insert the entry into the database
                conn.execute('''
                    INSERT INTO timetable (
                        teacher_id, course_id, room_id, class_section_id, semester, shift
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    teacher_id,
                    course_id,
                    room_id,
                    class_section_id,
                    current_semester_val,
                    current_shift
                ))
                print("Inserted timetable entry:", entry)
            except sqlite3.Error as e:
                print("Error inserting timetable entry:", e)
    conn.commit()
    print("Timetable saved successfully.")
    messagebox.showinfo("Success", f"Saved {len(filtered_entries)} entries for Semester {current_semester_val} and Shift {current_shift}.")
        

def clear_tt_form():
    """
    Clear all input fields in the form.
    """
    tt_teacher_entry.delete(0, tk.END)
    tt_course_entry.delete(0, tk.END)
    tt_room_entry.delete(0, tk.END)
    tt_class_entry.delete(0, tk.END)


def update_tt_treeview(current_shift=None, current_semester=None, is_loading=False):
    """
    Update the treeview with the current timetable entries.
    :param current_shift: Filter entries by the current shift.
    :param current_semester: Filter entries by the current semester.
    :param is_loading: A flag to indicate if data is being loaded from the database.
    """
    # Clear the existing treeview items
    for item in tt_treeview.get_children():
        tt_treeview.delete(item)

    # Filter entries for the current semester and shift if provided
    filtered_entries = timetable_entries
    if current_shift and current_semester:
        filtered_entries = [
            e for e in timetable_entries
            if e.get('shift') == current_shift and e.get('semester') == current_semester
        ]

    # Populate the treeview with updated entries
    for i, e in enumerate(filtered_entries):
        # Ensure all required keys exist in the entry
        if not all(key in e for key in ['teacher_id', 'course_id', 'room_id', 'class_section_id', 'semester', 'shift']):
            messagebox.showwarning("Invalid Entry", f"Entry {i + 1} is missing required fields and will be skipped.")
            continue

        # Fetch names only when loading data
        if is_loading:
            teacher_name = fetch_name_from_id("teachers", e['teacher_id'])
            course_name = fetch_name_from_id("courses", e['course_id'])
            room_name = fetch_name_from_id("rooms", e['room_id'])
            class_section_name = fetch_name_from_id("class_sections", e['class_section_id'])
        else:
            teacher_name = e.get('teacher_name', 'Unknown')
            course_name = e.get('course_name', 'Unknown')
            room_name = e.get('room_name', 'Unknown')
            class_section_name = e.get('class_section_name', 'Unknown')

        # Insert the entry into the treeview
        tt_treeview.insert('', 'end', values=(
            i + 1,  # Entry number
            e['semester'],  # Semester
            e['shift'],  # Shift
            teacher_name,  # Teacher name
            course_name,  # Course name
            room_name,  # Room name
            class_section_name  # Class/Section name
        ))
        
def delete_tt_entry():
    """
    Delete the selected timetable entry for the current semester and shift.
    """
    global timetable_entries

    # Get the current semester and shift
    current_semester = semester_cb.get().strip()
    current_shift = shift_cb.get().strip()

    if not current_semester or not current_shift:
        messagebox.showwarning("Missing Data", "Please select Semester and Shift before deleting an entry.")
        return

    try:
        current_semester_val = int(current_semester)
    except ValueError:
        messagebox.showwarning("Invalid Semester", "Semester must be a number (1-8).")
        return

    # Get the selected entry in the treeview
    sel = tt_treeview.focus()
    if not sel:
        messagebox.showwarning("Selection Error", "Please select an entry to delete.")
        return

    # Confirm deletion
    if not messagebox.askyesno("Confirm", "Are you sure you want to delete this entry?"):
        return

    # Get the index of the selected entry
    idx = int(tt_treeview.item(sel)['values'][0]) - 1

    # Check if the selected entry matches the current semester and shift
    entry = timetable_entries[idx]
    if entry.get('semester') == current_semester_val and entry.get('shift') == current_shift:
        # Remove the entry from the database
        try:
            conn.execute('''
                DELETE FROM timetable
                WHERE teacher_id = ? AND course_id = ? AND room_id = ? AND class_section_id = ? AND semester = ? AND shift = ?
            ''', (
                entry['teacher_id'],
                entry['course_id'],
                entry['room_id'],
                entry['class_section_id'],
                current_semester_val,
                current_shift
            ))
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete entry from the database: {e}")
            return

        # Remove the entry from the timetable_entries list
        timetable_entries.pop(idx)

        # Update the treeview
        update_tt_treeview(current_shift=current_shift, current_semester=current_semester_val)
        messagebox.showinfo("Success", "Entry deleted successfully.")
    else:
        messagebox.showwarning("Mismatch", "The selected entry does not match the current semester and shift.")        

        
def edit_tt_entry(event):
    """
    Edit the selected timetable entry for the current semester and shift.
    """
    global editing_index
    sel = tt_treeview.selection()

    # If no selection, clear the form and reset editing_index
    if not sel:
        editing_index = None
        clear_tt_form()
        return

    # Get the selected item's values
    vals = tt_treeview.item(sel[0])['values']

    # Get the current semester and shift
    current_semester = semester_cb.get().strip()
    current_shift = shift_cb.get().strip()

    if not current_semester or not current_shift:
        messagebox.showwarning("Missing Data", "Please select Semester and Shift before editing an entry.")
        return

    try:
        current_semester_val = int(current_semester)
    except ValueError:
        messagebox.showwarning("Invalid Semester", "Semester must be a number (1-8).")
        return

    # Check if the selected entry matches the current semester and shift
    if int(vals[1]) != current_semester_val or vals[2] != current_shift:
        messagebox.showwarning("Mismatch", "The selected entry does not match the current semester and shift.")
        return

    # Set the editing index and populate the form with selected values
    editing_index = vals[0] - 1
    clear_tt_form()

    semester_cb.set(vals[1])
    shift_cb.set(vals[2])
    tt_teacher_entry.insert(0, vals[3])
    tt_course_entry.insert(0, vals[4])
    tt_room_entry.insert(0, vals[5])
    tt_class_entry.insert(0, vals[6])
    

def clear_selection(event):
    """
    Clear the selection in the treeview if the user clicks on an empty space.
    """
    if not tt_treeview.identify_row(event.y):  # Check if the click is not on a row
        tt_treeview.selection_remove(tt_treeview.selection())  # Deselect all rows
        clear_tt_form()  # Clear the form
        global editing_index
        editing_index = None  # Reset the editing index


def generate_timetable():
    if not timetable_entries:
        messagebox.showwarning("Empty Entries", "Please add timetable entries first")
        return

    dialog = tk.Toplevel(root)
    dialog.title("Timetable Configuration")
    dialog.geometry("500x450")
    dialog.resizable(False, False)
    dialog.grab_set()
    
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'+{x}+{y}')
    
    main_frame = tk.Frame(dialog, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)
    
    title_label = tk.Label(main_frame, text="Configure Timetable Generation", font=("Helvetica", 14, "bold"))
    title_label.pack(anchor="w", pady=(0, 15))
    
    form_frame = tk.Frame(main_frame)
    form_frame.pack(fill="x", expand=True)
    
    # current_semester = str(timetable_entries[0]['semester'])
    current_shift = timetable_entries[0]['shift']
    
    tk.Label(form_frame, text="Semesters:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
    semester_display = ttk.Combobox(form_frame, values=['1-2'], width=18)
    semester_display.grid(row=0, column=1, sticky="w", pady=5)
    semester_display.set("1-2")
    
    tk.Label(form_frame, text="Shift:", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
    shift_display = ttk.Combobox(form_frame, values=["Morning", "Evening"], width=18)
    shift_display.grid(row=1, column=1, sticky="w", pady=5)
    shift_display.set("Morning")

    tk.Label(form_frame, text="Lectures per Course:", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
    lectures_var = tk.StringVar(value="3")
    lectures_cb = ttk.Combobox(form_frame, values=["1", "2", "3"], textvariable=lectures_var, width=18)
    lectures_cb.grid(row=2, column=1, sticky="w", pady=5)
    
    tk.Label(form_frame, text="Max Lectures per Day:", anchor="w").grid(row=3, column=0, sticky="w", pady=5)
    max_lectures_var = tk.StringVar(value="4")
    max_lectures_cb = ttk.Combobox(form_frame, values=["1", "2", "3", "4", "5"], textvariable=max_lectures_var, width=18)
    max_lectures_cb.grid(row=3, column=1, sticky="w", pady=5)
    
    tk.Label(form_frame, text="Lecture Duration (minutes):", anchor="w").grid(row=4, column=0, sticky="w", pady=5)
    duration_var = tk.StringVar(value="60")
    duration_cb = ttk.Combobox(form_frame, values=["30", "40", "45", "50", "60", "90", "120"], textvariable=duration_var, width=18)
    duration_cb.grid(row=4, column=1, sticky="w", pady=5)
    
    tk.Label(form_frame, text="Daily Start Time:", anchor="w").grid(row=5, column=0, sticky="w", pady=5)
    if current_shift == "Morning":
        default_start = "8:00 AM"
    else:
        default_start = "1:00 PM"
    start_time_var = tk.StringVar(value=default_start)
    start_time_entry = ttk.Entry(form_frame, textvariable=start_time_var, width=20)
    start_time_entry.grid(row=5, column=1, sticky="w", pady=5)
    
    tk.Label(form_frame, text="Daily End Time:", anchor="w").grid(row=6, column=0, sticky="w", pady=5)
    if current_shift == "Morning":
        default_end = "12:00 PM"
    else:
        default_end = "4:00 PM"
    end_time_var = tk.StringVar(value=default_end)
    end_time_entry = ttk.Entry(form_frame, textvariable=end_time_var, width=20)
    end_time_entry.grid(row=6, column=1, sticky="w", pady=5)
    
    btn_frame = tk.Frame(main_frame)
    btn_frame.pack(fill="x", expand=True, pady=(20, 0))
    
    def validate_and_generate():
        try:
            semester_display_value = semester_display.get()
            if semester_display_value not in ["1-2"]:
                messagebox.showwarning("Invalid Semester", "Please select a valid semester (1-2)")
                return
            shift_display_value = shift_display.get()
            if shift_display_value not in ["Morning", "Evening"]:
                messagebox.showwarning("Invalid Shift", "Please select a valid shift (Morning or Evening).")
                return
            lectures_per_course = int(lectures_var.get())
            max_lectures_per_day = int(max_lectures_var.get())
            lecture_duration = int(duration_var.get())

            try:
                datetime.strptime(start_time_var.get(), "%I:%M %p")
                datetime.strptime(end_time_var.get(), "%I:%M %p")
            except ValueError:
                messagebox.showwarning("Invalid Time Format", "Please use format HH:MM AM/PM (e.g. 9:00 AM)")
                return

            dialog.destroy()

            # Call the timetable generation function
            run_timetable_generation(
                semester=semester_display_value,
                shift=shift_display_value,
                lectures_per_course=lectures_per_course,
                max_lectures_per_day=max_lectures_per_day,
                lecture_duration=lecture_duration,
                start_time=start_time_var.get(),
                end_time=end_time_var.get()
            )

        except ValueError as e:
            messagebox.showwarning("Invalid Input", f"Please enter valid numbers: {str(e)}")

    tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
              font=("Helvetica", 10, "bold"), bg="#6c757d", fg="white", padx=20, pady=5, borderwidth=0).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Generate Timetable", command=validate_and_generate,
              font=("Helvetica", 10, "bold"), bg="#0d6efd", fg="white", padx=20, pady=5, borderwidth=0).pack(side="right", padx=5)

def run_timetable_generation(semester, shift, lectures_per_course, max_lectures_per_day, lecture_duration, start_time, end_time):
    try:
        # Determine which semesters to fetch based on the input
        if semester == "1-2":
            semesters = [1, 2]
        elif isinstance(semester, str) and semester.isdigit():
            semesters = [int(semester)]
        elif isinstance(semester, int):
            semesters = [semester]
        else:
            semesters = []

        # Fetch timetable entries for the selected semesters and shift
        timetable_entries = []
        for sem in semesters:
            timetable_entries.extend(load_timetable_for_ga(sem, shift))

        if not timetable_entries:
            messagebox.showwarning("No Data", "No timetable entries found in the database for the selected semester(s) and shift.")
            return

        # Parse start and end times
        start_dt = datetime.strptime(start_time, "%I:%M %p")
        end_dt = datetime.strptime(end_time, "%I:%M %p")

        # Generate time slots based on dialog box constraints
        selected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        time_slots = generate_time_slots(start_dt, end_dt, lecture_duration, selected_days)

        if not time_slots:
            messagebox.showwarning("Configuration Error", "Could not generate any valid time slots with the given parameters.")
            return

        # Prepare entries for the genetic algorithm
        ga_entries = prepare_entries_for_ga(timetable_entries)

        # Run the genetic algorithm
        ga = TimetableGeneticAlgorithm(
            ga_entries,
            lectures_per_course=lectures_per_course,
            max_lectures_per_day=max_lectures_per_day,
            lecture_duration=lecture_duration,
            time_slots=time_slots,
            population_size=100,
            max_generations=200,
            mutation_rate=0.15
        )
        
        optimized = ga.generate_optimized_timetable()

        if optimized is None:
            messagebox.showwarning("Generation Failed", "Could not generate a valid timetable.")
            return

        # Display the generated timetable
        display_timetable(optimized, time_slots, selected_days, lecture_duration, semester, shift)

    except Exception as ex:
        messagebox.showerror("Error", f"Failed to generate timetable: {str(ex)}")
        
                
def clear_entries_on_change(event):
    """
    Clear all saved timetable entries when semester or shift is changed.
    """
    global timetable_entries
    if timetable_entries:
        if messagebox.askyesno("Confirm", "Changing Semester or Shift will clear all saved entries. Do you want to proceed?"):
            timetable_entries.clear()
            update_tt_treeview()
        else:
            # Reset the combobox to its previous value
            event.widget.set(event.widget.get())  # Keep the current value

def generate_time_slots(start_dt, end_dt, lecture_duration, selected_days, entries=None):
    """
    Generate time slots for lectures based on the entries provided.
    Each slot is exactly 'lecture_duration' minutes.
    If entries are provided, only generate slots for the days/classes present in entries.
    """
    time_slots = []

    total_minutes = ((end_dt.hour * 60 + end_dt.minute) - (start_dt.hour * 60 + start_dt.minute))
    slot_duration = lecture_duration
    slots_per_day = total_minutes // slot_duration

    if slots_per_day <= 0:
        return []

    # If entries are provided, determine which days/classes are needed
    if entries:
        # Collect unique days/classes from entries if available
        # (Assuming entries may have a 'day' or 'class_section_name' field)
        entry_days = set()
        for entry in entries:
            # If your entries have a 'day' field, use it; otherwise, use all selected_days
            if 'day' in entry:
                entry_days.add(entry['day'])
        if entry_days:
            days_to_use = [day for day in selected_days if day in entry_days]
        else:
            days_to_use = selected_days
    else:
        days_to_use = selected_days

    for day in days_to_use:
        current_time = start_dt
        for _ in range(slots_per_day):
            end_time = (datetime(1, 1, 1, current_time.hour, current_time.minute) +
                        timedelta(minutes=slot_duration))

            slot_start = current_time.strftime("%I:%M %p")
            slot_end = end_time.strftime("%I:%M %p")

            time_slot = f"{day} {slot_start}-{slot_end}"
            time_slots.append(time_slot)

            # Move to the next slot
            current_time = (datetime(1, 1, 1, current_time.hour, current_time.minute) +
                            timedelta(minutes=slot_duration))

    return time_slots

def prepare_entries_for_ga(entries):
    """
    Prepare entries for the genetic algorithm.
    Converts tuples to dicts if necessary.
    """
    ga_entries = []
    for entry in entries:
        # If entry is a tuple, convert to dict (adjust keys as per your schema)
        if isinstance(entry, tuple):
            # Example: adjust these keys to match your tuple structure
            keys = ['semester', 'shift', 'teacher', 'course', 'room', 'class', 'other_fields']
            ga_entry = dict(zip(keys, entry))
        else:
            ga_entry = entry.copy()
        ga_entry['time_slot'] = None  # Let the GA assign this
        ga_entries.append(ga_entry)
    return ga_entries



def display_timetable(optimized, time_slots, selected_days, lecture_duration, semester, shift):
    win = tk.Toplevel(root)
    win.title(f"Optimized Timetable - Semester {semester} ({shift} Shift)")
    win.geometry("1000x600")
    
    main_frame = tk.Frame(win, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)
    
    header_frame = tk.Frame(main_frame, bg="#f0f0f0")
    header_frame.pack(fill="x", pady=(0, 20))
    
    tk.Label(header_frame, text=f"Semester {semester} - {shift} Shift", 
            font=("Helvetica", 14, "bold"), bg="#f0f0f0").pack(pady=10)
    
    # Extract days and times from time_slots
    # Use the order from selected_days, but only include days that are actually in time_slots
    days_in_slots = [slot.split()[0] for slot in time_slots]
    days = [day for day in selected_days if day in days_in_slots]
    times = sorted({ " ".join(slot.split()[1:]) for slot in time_slots })
    
    tree_frame = tk.Frame(main_frame)
    tree_frame.pack(fill="both", expand=True)
    
    columns = ["Time"] + days
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=len(times))
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=max(100, len(col) * 15), anchor="center")
    
    # Insert empty rows for each time range
    for time_range in times:
        tree.insert("", "end", values=[time_range] + ["" for _ in days])
    
    # Fill the timetable grid with GA results
    for (course, class_sec, instance), details in optimized.items():
        slot = details['time_slot']
        if not slot:
            continue
        day, time_part = slot.split(" ", 1)
        # Find the row for this time_part
        row_id = None
        for item_id in tree.get_children():
            if tree.item(item_id)["values"][0] == time_part:
                row_id = item_id
                break
        if row_id is None or day not in columns:
            continue
        day_idx = columns.index(day)
        row_values = list(tree.item(row_id)["values"])
        existing = row_values[day_idx]

        new_entry = f"{details.get('course', course)}\n{details.get('class', class_sec)}\nInstance: {instance}\n{details.get('teacher', '')}\nRoom: {details.get('room', '')}"
        print(f"Placing in cell [Day: {day}, Time: {time_part}]:\n{new_entry}\n")

        # Append instead of overwrite
        if existing and existing.strip():
            # Only append if the new entry is not already present (avoid duplicates)
            if new_entry not in existing:
                row_values[day_idx] = existing + "\n---\n" + new_entry
        else:
            row_values[day_idx] = new_entry
        tree.item(row_id, values=row_values)
    
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)
    
    btn_frame = tk.Frame(main_frame, pady=10)
    btn_frame.pack(fill="x")
    
    tk.Button(btn_frame, text="Close", command=win.destroy, 
             bg="#f0f0f0", padx=20, pady=5).pack(side="right", padx=5)
    
    tk.Button(btn_frame, text="Export to PDF", command=lambda: messagebox.showinfo("Export", 
                "PDF export functionality could be implemented here"),
             bg="#0d6efd", fg="white", padx=20, pady=5).pack(side="right", padx=5)

        
    
def save_to_db_ui():
    """
    Save only the current shift's timetable entries to the database.
    """
    global timetable_entries

    # Get the current shift
    current_shift = shift_cb.get().strip()

    if not current_shift:
        messagebox.showwarning("Missing Data", "Please select a Shift before saving.")
        return

    # Filter entries for the current shift
    shift_entries = [entry for entry in timetable_entries if entry.get('shift') == current_shift]

    if not shift_entries:
        messagebox.showwarning("Empty", f"No entries found for the {current_shift} shift to save.")
        return

    # Save the filtered entries to the database
    save_timetable_from_treeview()
    
    
def load_from_db_ui():
    """
    Load timetable entries from the database for the selected semester and shift.
    """
    global timetable_entries

    # Confirm with the user before loading
    if not messagebox.askyesno("Confirm", "Load data from database? This will replace current entries."):
        return
    
    # Get the selected semester and shift
    semester = semester_cb.get().strip()
    shift = shift_cb.get().strip()
    
    if not semester or not shift:
        messagebox.showwarning("Missing Data", "Please select Semester and Shift before loading.")
        return

    try:
        semester_val = int(semester)
    except ValueError:
        messagebox.showwarning("Invalid Semester", "Semester must be a number (1-8).")
        return

    # Debug: Print semester and shift
    # print("Loading data for Semester:", semester_val, "Shift:", shift)
    
    # Load data from the database
    timetable_entries = load_timetable(semester_val, shift)
    
    # Debug: Print loaded entries
    # print("Loaded entries:", timetable_entries)
    
    # Update the treeview with the loaded entries
    update_tt_treeview()
    messagebox.showinfo("Success", f"{len(timetable_entries)} entries loaded from database.")
    
        
def show():
    TT_header_frame.pack(fill="x")
    TT_frame.pack(fill="both", expand=True)


def hide():
    TT_header_frame.pack_forget()
    TT_frame.pack_forget()
