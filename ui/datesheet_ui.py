import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import Calendar
from datetime import datetime

from algorithms.datesheet_ga import DatesheetGeneticAlgorithm
from db.datesheet_db import init_datesheet_db, save_datesheet, load_datesheet

# Global variables
datesheet_entries = []
editing_index = None
DT_header_frame = None
DT_frame = None

dt_treeview = None

dt_start_date_entry = None

dt_end_date_entry = None

dt_start_time_entry = None

dt_end_time_entry = None

dt_room_entry = None

subject_entries = []

dt_generate_button = None

root = None


def initialize(master, title_font, header_font, normal_font, button_font, return_home_func):
    global DT_header_frame, DT_frame, dt_treeview
    global dt_start_date_entry, dt_end_date_entry, dt_start_time_entry, dt_end_time_entry, dt_room_entry
    global subject_entries, dt_generate_button, root

    root = master
    # Initialize database
    init_datesheet_db()

    # Header frame
    DT_header_frame = tk.Frame(root, bg="#0d6efd", height=60)
    DT_header_frame.pack(fill="x")
    header_label = tk.Label(DT_header_frame, text="Datesheet Generator", bg="#0d6efd", fg="white", font=title_font)
    header_label.pack(side="left", padx=20, pady=15)
    btn_home = tk.Button(DT_header_frame, text="Home", command=return_home_func,
                         bg="white", fg="#0d6efd", font=normal_font, padx=15, pady=5, borderwidth=0)
    btn_home.pack(side="right", padx=20, pady=10)

    # Main frame
    DT_frame = tk.Frame(root, bg="white")
    DT_frame.pack(fill="both", expand=True)
    DT_frame.grid_columnconfigure(0, weight=2)
    DT_frame.grid_columnconfigure(1, weight=3)
    DT_frame.grid_rowconfigure(0, weight=1)

    # Left pane for inputs
    dt_left = tk.Frame(DT_frame, bg="white", padx=20, pady=20)
    dt_left.grid(row=0, column=0, sticky="nsew")

    # Right pane for display
    dt_right = tk.Frame(DT_frame, bg="#f8f9fa", padx=20, pady=20)
    dt_right.grid(row=0, column=1, sticky="nse")

    # Helper to open calendar
    def open_calendar(entry_widget):
        top = tk.Toplevel(dt_left)
        cal = Calendar(top, date_pattern="yyyy-mm-dd")
        cal.pack(pady=10)
        def select_date():
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, cal.get_date())
            top.destroy()
        tk.Button(top, text="Select", command=select_date).pack(pady=5)

    # Input fields
    tk.Label(dt_left, text="Enter Datesheet Details", bg="white", fg="#212529", font=header_font).grid(row=0, column=0, columnspan=4, pady=10, sticky="w")
    ttk.Separator(dt_left, orient='horizontal').grid(row=1, column=0, columnspan=4, sticky='ew', pady=5)

    # Start Date
    tk.Label(dt_left, text="Start Date:", bg="white", fg="#495057", font=normal_font).grid(row=2, column=0, sticky="w", pady=5)
    dt_start_date_entry = ttk.Entry(dt_left, font=normal_font)
    dt_start_date_entry.grid(row=2, column=1, sticky="ew", pady=5)
    tk.Button(dt_left, text="Select", command=lambda: open_calendar(dt_start_date_entry)).grid(row=2, column=2, padx=5)

    # End Date
    tk.Label(dt_left, text="End Date:", bg="white", fg="#495057", font=normal_font).grid(row=3, column=0, sticky="w", pady=5)
    dt_end_date_entry = ttk.Entry(dt_left, font=normal_font)
    dt_end_date_entry.grid(row=3, column=1, sticky="ew", pady=5)
    tk.Button(dt_left, text="Select", command=lambda: open_calendar(dt_end_date_entry)).grid(row=3, column=2, padx=5)

    # Start Time
    tk.Label(dt_left, text="Start Time:", bg="white", fg="#495057", font=normal_font).grid(row=4, column=0, sticky="w", pady=5)
    dt_start_time_entry = ttk.Entry(dt_left, font=normal_font)
    dt_start_time_entry.grid(row=4, column=1, sticky="ew", pady=5)

    # End Time
    tk.Label(dt_left, text="End Time:", bg="white", fg="#495057", font=normal_font).grid(row=5, column=0, sticky="w", pady=5)
    dt_end_time_entry = ttk.Entry(dt_left, font=normal_font)
    dt_end_time_entry.grid(row=5, column=1, sticky="ew", pady=5)

    # Subjects
    tk.Label(dt_left, text="Subjects:", bg="white", fg="#495057", font=normal_font).grid(row=6, column=0, sticky="nw", pady=5)
    dt_subjects_frame = tk.Frame(dt_left, bg="white")
    dt_subjects_frame.grid(row=6, column=1, sticky="ew", pady=5)
    subject_entries.clear()
    for i in range(6):
        ent = ttk.Entry(dt_subjects_frame, font=normal_font)
        ent.grid(row=i, column=0, pady=2, sticky="ew")
        subject_entries.append(ent)

    # Room
    tk.Label(dt_left, text="Room:", bg="white", fg="#495057", font=normal_font).grid(row=7, column=0, sticky="w", pady=5)
    dt_room_entry = ttk.Entry(dt_left, font=normal_font)
    dt_room_entry.grid(row=7, column=1, sticky="ew", pady=5)

    # Save Entry button
    tk.Button(dt_left, text="Save Entry", font=button_font, bg="#198754", fg="white",
              command=save_dt_entry, padx=10, pady=5, borderwidth=0).grid(row=8, column=0, columnspan=2, pady=15)

    # Right side: Treeview
    tk.Label(dt_right, text="Saved Datesheet Entries", bg="#f8f9fa", fg="#212529", font=header_font).pack(anchor="w", pady=5)
    tree_container = tk.Frame(dt_right, bg="#f8f9fa")
    tree_container.pack(fill="both", expand=True)
    dt_treeview = ttk.Treeview(tree_container,
                               columns=("#","Start","End","S.Time","E.Time","Subjects","Room"),
                               show='headings', selectmode='browse')
    for col, txt, width in [('#','ID',40),('Start','Start Date',100),('End','End Date',100),
                            ('S.Time','Start Time',80),('E.Time','End Time',80),
                            ('Subjects','Subjects',200),('Room','Room',100)]:
        dt_treeview.heading(col, text=txt)
        dt_treeview.column(col, width=width, anchor='center')
    scrollbar = ttk.Scrollbar(tree_container, orient='vertical', command=dt_treeview.yview)
    dt_treeview.configure(yscrollcommand=scrollbar.set)
    dt_treeview.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    dt_treeview.bind("<Double-1>", edit_dt_entry)

    # Action buttons
    btn_frame = tk.Frame(dt_right, bg="#f8f9fa")
    btn_frame.pack(fill='x', pady=10)
    tk.Button(btn_frame, text="Delete", font=button_font, bg="#dc3545", fg="white",
              command=delete_dt_entry, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    tk.Button(btn_frame, text="Clear All", font=button_font, bg="#6c757d", fg="white",
              command=clear_all_dt_entries, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    dt_generate_button = tk.Button(btn_frame, text="Generate", font=button_font, bg="#0d6efd", fg="white",
                                   command=generate_datesheet, padx=10, pady=5, borderwidth=0)
    dt_generate_button.pack(side='right', padx=5)

    # DB buttons
    db_frame = tk.Frame(dt_right, bg="#f8f9fa")
    db_frame.pack(fill='x', pady=10)
    tk.Button(db_frame, text="Save to DB", font=button_font, bg="#198754", fg="white",
              command=save_to_db_ui, padx=10, pady=5, borderwidth=0).pack(side='left', padx=5)
    tk.Button(db_frame, text="Load from DB", font=button_font, bg="#0d6efd", fg="white",
              command=load_from_db_ui, padx=10, pady=5, borderwidth=0).pack(side='right', padx=5)

    update_dt_treeview()


def save_dt_entry():
    """Save a new entry or update an existing one"""
    global editing_index
    sd = dt_start_date_entry.get().strip()
    ed = dt_end_date_entry.get().strip()
    st = dt_start_time_entry.get().strip()
    et = dt_end_time_entry.get().strip()
    room = dt_room_entry.get().strip()
    subs = [e.get().strip() for e in subject_entries]
    # validate
    if not all([sd, ed, st, et, room]) or not any(subs):
        messagebox.showerror("Error", "All fields required, at least one subject.")
        return
    try:
        datetime.strptime(sd, '%Y-%m-%d')
        datetime.strptime(ed, '%Y-%m-%d')
        datetime.strptime(st, '%H:%M')
        datetime.strptime(et, '%H:%M')
    except ValueError:
        messagebox.showerror("Error", "Invalid date/time format.")
        return
    entry = {"start_date":sd, "end_date":ed,
             "start_time":st, "end_time":et,
             "subjects":[s for s in subs if s],
             "room":room}
    if editing_index is not None:
        datesheet_entries[editing_index] = entry
        editing_index = None
    else:
        datesheet_entries.append(entry)
    clear_dt_form()
    update_dt_treeview()


def clear_dt_form():
    dt_start_date_entry.delete(0, tk.END)
    dt_end_date_entry.delete(0, tk.END)
    dt_start_time_entry.delete(0, tk.END)
    dt_end_time_entry.delete(0, tk.END)
    dt_room_entry.delete(0, tk.END)
    for e in subject_entries:
        e.delete(0, tk.END)


def update_dt_treeview():
    for item in dt_treeview.get_children():
        dt_treeview.delete(item)
    for i, e in enumerate(datesheet_entries):
        dt_treeview.insert('', 'end', values=(
            i+1,
            e['start_date'], e['end_date'],
            e['start_time'], e['end_time'],
            ", ".join(e['subjects']),
            e['room']
        ))


def delete_dt_entry():
    sel = dt_treeview.focus()
    if not sel:
        messagebox.showinfo("Info", "Select an entry first.")
        return
    if not messagebox.askyesno("Confirm", "Delete selected entry?"):
        return
    idx = int(dt_treeview.item(sel)['values'][0]) - 1
    datesheet_entries.pop(idx)
    update_dt_treeview()


def clear_all_dt_entries():
    if not datesheet_entries:
        messagebox.showinfo("Info", "No entries to clear.")
        return
    if messagebox.askyesno("Confirm", "Clear all entries?"):
        datesheet_entries.clear()
        update_dt_treeview()


def edit_dt_entry(event):
    global editing_index
    sel = dt_treeview.selection()
    if not sel: return
    vals = dt_treeview.item(sel[0])['values']
    editing_index = vals[0] - 1
    clear_dt_form()
    dt_start_date_entry.insert(0, vals[1])
    dt_end_date_entry.insert(0, vals[2])
    dt_start_time_entry.insert(0, vals[3])
    dt_end_time_entry.insert(0, vals[4])
    subs = vals[5].split(', ')
    for i, s in enumerate(subs):
        if i < len(subject_entries): subject_entries[i].insert(0, s)
    dt_room_entry.insert(0, vals[6])


def generate_datesheet():
    """Run GA and show optimized schedule"""
    if not datesheet_entries:
        messagebox.showinfo("Info", "Add entries first.")
        return
    try:
        ga = DatesheetGeneticAlgorithm(datesheet_entries)
        sched = ga.run()
        # Display in new window
        win = tk.Toplevel(root)
        win.title("Optimized Datesheet")
        cols = ('Start','End','S.Time','E.Time','Subjects','Room')
        tree = ttk.Treeview(win, columns=cols, show='headings')
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor='center')
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        for e in sched:
            tree.insert('', 'end', values=(
                e['start_date'], e['end_date'],
                e['start_time'], e['end_time'],
                ", ".join(e.get('subjects', [])),
                e['room']
            ))
    except Exception as ex:
        messagebox.showerror("Error", f"Failed to generate: {ex}")


def save_to_db_ui():
    """Save entries list to database"""
    if not datesheet_entries:
        messagebox.showinfo("Info", "No entries to save.")
        return
    if not messagebox.askyesno("Confirm", "Save all entries to database? This will overwrite existing entries."):
        return
    save_datesheet(datesheet_entries)
    messagebox.showinfo("Success", f"{len(datesheet_entries)} entries saved to database.")


def load_from_db_ui():
    """Load entries from database into UI list"""
    global datesheet_entries
    if not messagebox.askyesno("Confirm", "Load data from database? This will replace current entries."):
        return
    datesheet_entries = load_datesheet()
    update_dt_treeview()
    messagebox.showinfo("Success", f"{len(datesheet_entries)} entries loaded from database.")


def show():
    DT_header_frame.pack(fill="x")
    DT_frame.pack(fill="both", expand=True)


def hide():
    DT_header_frame.pack_forget()
    DT_frame.pack_forget()
