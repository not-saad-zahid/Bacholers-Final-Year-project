import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import random
import sqlite3
from datetime import datetime, timedelta
from algorithms.timetable_ga import TimetableGeneticAlgorithm
from db.timetable_db import init_timetable_db, save_timetable, load_timetable

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
    ttk.Separator(left, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)

    # Semester
    tk.Label(left, text="Semester (1-8):", bg="white").grid(row=2, column=0, pady=5)
    semester_cb = ttk.Combobox(left, values=[str(i) for i in range(1,9)])
    semester_cb.grid(row=2, column=1, sticky="ew", pady=5)
    semester_cb.set(1)

    # Shift
    tk.Label(left, text="Shift:", bg="white").grid(row=2, column=3, pady=5)
    shift_cb = ttk.Combobox(left, values=["Morning","Evening"])
    shift_cb.grid(row=2, column=4, sticky="ew", pady=5)
    shift_cb.set("Morning")

    # Initialize start_time_var
    start_time_var = tk.StringVar(value="8:00 AM")  # Default value
    # Initialize end_time_var
    end_time_var = tk.StringVar(value="1:00 PM")  # Default value
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
    
    
def fetch_id_from_name(table, name, **kwargs):
    """
    Fetch the ID of a record from the database by name.
    If the record does not exist, insert it and return the new ID.
    """
    try:
        # Validate the name for class_sections
        if table == "class_sections" and not name.isalnum():
            messagebox.showwarning("Invalid Class/Section Name", "Class/Section name must be alphanumeric.")
            return None

        # Check if the record exists
        query = f"SELECT id FROM {table} WHERE name = ?"
        cur = conn.cursor()
        cur.execute(query, (name,))
        result = cur.fetchone()
        if result:
            return result[0]

        # Insert the record if it does not exist
        if table == "courses" and "teacher_id" in kwargs:
            cur.execute(f"INSERT INTO {table} (name, teacher_id) VALUES (?, ?)", (name, kwargs["teacher_id"]))
        elif table == "class_sections" and "semester" in kwargs and "shift" in kwargs:
            cur.execute(f"INSERT INTO {table} (name, semester, shift) VALUES (?, ?, ?)", (name, kwargs["semester"], kwargs["shift"]))
        elif table == "rooms":
            cur.execute(f"INSERT INTO {table} (name) VALUES (?)", (int(name),))  # Ensure room is an integer
        else:
            cur.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))

        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch or create ID in {table}: {e}")
        return None

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
    if not teacher.isalpha():
        messagebox.showwarning("Invalid Teacher Name", "Teacher name must contain only letters.")
        return

    # Validate Course Name
    if not course:
        messagebox.showwarning("Invalid Course Name", "Course name cannot be empty.")
        return

    # Validate Room (must be an integer)
    try:
        room_val = int(room)
        if room_val <= 0:
            raise ValueError
    except ValueError:
        messagebox.showwarning("Invalid Room", "Room must be a positive integer.")
        return

    # Validate Class/Section (must be alphanumeric)
    if not class_section.isalnum():
        messagebox.showwarning("Invalid Class/Section", "Class/Section must be alphanumeric.")
        return

    # Check for existing semester and shift conflicts
    if timetable_entries:
        existing_sem = int(timetable_entries[0]['semester'])
        existing_shift = timetable_entries[0]['shift']
        if semester_val != existing_sem or shift != existing_shift:
            if messagebox.askyesno("Change Semester/Shift", "Changing the semester or shift will clear all entries. Do you want to proceed?"):
                timetable_entries.clear()
                update_tt_treeview()
            else:
                return

    # Ensure Semester and Shift are selected
    if not semester or not shift:
        messagebox.showwarning("Missing Data", "Semester and Shift must be selected.")
        return

    # Fetch or create IDs for teacher, course, room, and class_section
    teacher_id = fetch_id_from_name("teachers", teacher)
    course_id = fetch_id_from_name("courses", course, teacher_id=teacher_id)
    room_id = fetch_id_from_name("rooms", room)
    class_section_id = fetch_id_from_name("class_sections", class_section, semester=semester_val, shift=shift)

    if not teacher_id or not course_id or not room_id or not class_section_id:
        messagebox.showwarning("Invalid Data", "Please ensure all fields are valid and exist in the database.")
        return

    # Create the entry dictionary
    entry = {
        "teacher_id": teacher_id,
        "course_id": course_id,
        "room_id": room_id,
        "class_section_id": class_section_id,
        "semester": semester_val,
        "shift": shift,
    }

    # Add or update the entry in the timetable
    if editing_index is not None:
        timetable_entries[editing_index] = entry
        editing_index = None
    else:
        timetable_entries.append(entry)

    # Update the treeview
    update_tt_treeview()

    # Show success message
    messagebox.showinfo("Success", "Timetable entry saved successfully!")


def clear_tt_form():
    """
    Clear all input fields in the form.
    """
    tt_teacher_entry.delete(0, tk.END)
    tt_course_entry.delete(0, tk.END)
    tt_room_entry.delete(0, tk.END)
    tt_class_entry.delete(0, tk.END)


def update_tt_treeview():
    """
    Update the treeview with the current timetable entries.
    """
    # Clear the existing treeview items
    for item in tt_treeview.get_children():
        tt_treeview.delete(item)

    # Populate the treeview with updated entries
    for i, e in enumerate(timetable_entries):
        teacher_name = fetch_name_from_id("teachers", e['teacher_id'])
        course_name = fetch_name_from_id("courses", e['course_id'])
        room_name = fetch_name_from_id("rooms", e['room_id'])
        class_section_name = fetch_name_from_id("class_sections", e['class_section_id'])

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
    sel = tt_treeview.focus()
    if not sel:
        messagebox.showwarning("Selection Error", "Please select an entry to delete")
        return
    if not messagebox.askyesno("Confirm", "Are you sure you want to delete this entry?"):
        return
    idx = int(tt_treeview.item(sel)['values'][0]) - 1
    timetable_entries.pop(idx)
    update_tt_treeview()

def edit_tt_entry(event):
    global editing_index
    sel = tt_treeview.selection()
    
    # If no selection, clear the form and reset editing_index
    if not sel:
        editing_index = None
        clear_tt_form()
        return
    
    # Get the selected item's values
    vals = tt_treeview.item(sel[0])['values']
    
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
    
    current_semester = str(timetable_entries[0]['semester'])
    current_shift = timetable_entries[0]['shift']
    
    # tk.Label(form_frame, text="Semester:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
    # semester_display = tk.Label(form_frame, text=current_semester, anchor="w", bg="#f0f0f0", width=20, relief="ridge", padx=5)
    # semester_display.grid(row=0, column=1, sticky="w", pady=5)
    
    # tk.Label(form_frame, text="Shift:", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
    # shift_display = tk.Label(form_frame, text=current_shift, anchor="w", bg="#f0f0f0", width=20, relief="ridge", padx=5)
    # shift_display.grid(row=1, column=1, sticky="w", pady=5)
    
    tk.Label(form_frame, text="Lectures per Course:", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
    lectures_var = tk.StringVar(value="1")
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
        default_end = "1:00 PM"
    else:
        default_end = "5:00 PM"
    end_time_var = tk.StringVar(value=default_end)
    end_time_entry = ttk.Entry(form_frame, textvariable=end_time_var, width=20)
    end_time_entry.grid(row=6, column=1, sticky="w", pady=5)
    
    btn_frame = tk.Frame(main_frame)
    btn_frame.pack(fill="x", expand=True, pady=(20, 0))
    
    def validate_and_generate():
        try:
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
                semester=current_semester,
                shift=current_shift,
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
        # Fetch timetable entries from the database
        timetable_entries = load_timetable(semester, shift)
        if not timetable_entries:
            messagebox.showwarning("No Data", "No timetable entries found in the database for the selected semester and shift.")
            return

        # Parse start and end times
        start_dt = datetime.strptime(start_time, "%I:%M %p")
        end_dt = datetime.strptime(end_time, "%I:%M %p")

        # Generate time slots based on dialog box constraints
        selected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        time_slots = generate_time_slots(start_dt, end_dt, lecture_duration, 10, selected_days)

        if not time_slots:
            messagebox.showwarning("Configuration Error", "Could not generate any valid time slots with the given parameters.")
            return

        # Prepare entries for the genetic algorithm
        ga_entries = prepare_entries_for_ga(timetable_entries, time_slots)

        # Run the genetic algorithm
        ga = TimetableGeneticAlgorithm(
            semester=semester,
            shift=shift,
            lectures_per_course=lectures_per_course,
            max_lectures_per_day=max_lectures_per_day,
            lecture_duration=lecture_duration,
            start_time=start_time,
            end_time=end_time,
            population_size=100,
            max_generations=100,
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
        
def generate_time_slots(start_dt, end_dt, lecture_duration, break_duration, selected_days):
    time_slots = []
    
    total_minutes = ((end_dt.hour * 60 + end_dt.minute) - 
                    (start_dt.hour * 60 + start_dt.minute))
    slot_duration = lecture_duration + break_duration
    slots_per_day = total_minutes // slot_duration
    
    if slots_per_day <= 0:
        return []
    
    for day in selected_days:
        current_time = start_dt
        for _ in range(slots_per_day):
            end_time = (datetime(1, 1, 1, current_time.hour, current_time.minute) + 
                      timedelta(minutes=lecture_duration))
            
            slot_start = current_time.strftime("%I:%M %p")
            slot_end = end_time.strftime("%I:%M %p")
            
            time_slot = f"{day} {slot_start}-{slot_end}"
            time_slots.append(time_slot)
            
            current_time = (datetime(1, 1, 1, current_time.hour, current_time.minute) + 
                          timedelta(minutes=slot_duration))
    
    return time_slots

def prepare_entries_for_ga(entries, time_slots):
    ga_entries = []
    
    for entry in entries:
        ga_entry = entry.copy()
        ga_entry['time_slot'] = random.choice(time_slots)
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
    
    courses = sorted(list(optimized.keys()), key=lambda x: (x[1], x[0]))
    
    days = list(set(slot.split()[0] for slot in time_slots))
    times = sorted(list(set(" ".join(slot.split()[1:]) for slot in time_slots)))
    
    tree_frame = tk.Frame(main_frame)
    tree_frame.pack(fill="both", expand=True)
    
    columns = ["Time"] + days
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=len(times))
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=len(col) * 15, anchor="center")
    
    for time_range in times:
        tree.insert("", "end", values=[time_range] + ["" for _ in days])
    
    for (course, class_sec), details in optimized.items():
        slot = details['time_slot']
        day, time_part = slot.split(" ", 1)
        
        for item_id in tree.get_children():
            if tree.item(item_id)["values"][0] == time_part:
                row_id = item_id
                break
        
        day_idx = columns.index(day)
        row_values = list(tree.item(row_id)["values"])
        row_values[day_idx] = f"{course}\n{class_sec}\n{details['teacher']}\nRoom: {details['room']}"
        
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
    if not timetable_entries:
        messagebox.showwarning("Empty", "No entries to save")
        return
    save_timetable(timetable_entries)
    messagebox.showinfo("Success", f"Saved {len(timetable_entries)} entries")

def load_from_db_ui():
    global timetable_entries
    if not messagebox.askyesno("Confirm", "Load data from database? This will replace current entries."):
        return
    
    semester = semester_cb.get().strip()
    shift = shift_cb.get().strip()
    
    if not semester or not shift:
        messagebox.showwarning("Missing Data", "Please select Semester and Shift before loading.")
        return
    try:
        semester_val = int(semester)
    except ValueError:
        messagebox.showwarning("Invalid Semester", "Semester must be a number (1-8)")
        return
    
    timetable_entries = load_timetable(semester_val, shift)
    update_tt_treeview()
    messagebox.showinfo("Success", f"{len(timetable_entries)} entries loaded from database.")

def show():
    TT_header_frame.pack(fill="x")
    TT_frame.pack(fill="both", expand=True)

def hide():
    TT_header_frame.pack_forget()
    TT_frame.pack_forget()