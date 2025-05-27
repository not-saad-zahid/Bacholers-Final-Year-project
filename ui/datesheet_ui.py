import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
import sqlite3
import os
import uuid # For unique item IDs

from algorithms.datesheet_ga import DatesheetGeneticAlgorithm # Assuming this exists and is compatible or will be adapted

# --- Global variables ---
# UI Elements
root_window = None
DT_header_frame = None
DT_main_content_frame = None
dt_input_frame = None
dt_display_frame = None
notebook = None # For tabbed display
dt_entries_count_label = None  # <-- Add this for entry count

# Input Fields
dt_semester_label_entry = None
dt_shift_combobox = None
dt_class_section_entry = None
dt_teacher_name_entry = None
dt_course_name_entry = None
dt_course_code_entry = None
dt_indicators_entry = None
dt_room_entry = None
save_action_button = None # Renamed from save_entry_button, will handle Save/Update

# Data Management
# tab_entry_data stores: { "tab_id1": [{"id": unique_id, "checked": False, "data": {...}}, ...], ... }
tab_entry_data = {}
# tab_treeviews stores: { "tab_id1": treeview_widget, ... }
tab_treeviews = {}
editing_item_details = None # Stores info about the item being edited: {'tab_id': str, 'item_id': str, 'data_list_index': int}

# Fonts (to be passed by the main application)
_title_font = None
_header_font = None
_normal_font = None
_button_font = None


def get_active_tab_id():
    if notebook and notebook.tabs():
        try:
            return notebook.tab(notebook.select(), "text")
        except tk.TclError: # If no tab is selected or notebook is empty
            return None
    return None

def get_treeview_for_tab(tab_id):
    return tab_treeviews.get(tab_id)

def get_data_for_tab(tab_id):
    return tab_entry_data.get(tab_id, [])

def initialize(master, title_font, header_font, normal_font, button_font, return_home_func):
    global DT_header_frame, DT_main_content_frame, notebook
    global dt_semester_label_entry, dt_shift_combobox, dt_class_section_entry
    global dt_teacher_name_entry, dt_course_name_entry, dt_course_code_entry
    global dt_indicators_entry, dt_room_entry, save_action_button
    global root_window, dt_input_frame, dt_display_frame
    global _title_font, _header_font, _normal_font, _button_font
    global dt_entries_count_label

    root_window = master
    _title_font, _header_font, _normal_font, _button_font = title_font, header_font, normal_font, button_font

    DT_header_frame = tk.Frame(root_window, bg="#0d6efd", height=60)
    header_label = tk.Label(DT_header_frame, text="Datesheet Data Entry", bg="#0d6efd", fg="white", font=title_font)
    header_label.pack(side="left", padx=20, pady=15)
    btn_home = tk.Button(DT_header_frame, text="Home", command=return_home_func,
                         bg="white", fg="#0d6efd", font=normal_font, padx=15, pady=5, borderwidth=0)
    btn_home.pack(side="right", padx=20, pady=10)

    DT_main_content_frame = tk.Frame(root_window, bg="white")

    # --- Input Frame ---
    dt_input_frame = tk.Frame(DT_main_content_frame, bg="white", padx=20, pady=10)
    dt_input_frame.pack(side="top", fill="x", pady=(10, 0))
    dt_input_frame.grid_columnconfigure(1, weight=1) # Entry fields' column (still takes weighted space)
    dt_input_frame.grid_columnconfigure(3, weight=1) # Entry fields' column (still takes weighted space)
    # Optional: Give labels some weight too if you want them to push entries, or keep weight 0
    dt_input_frame.grid_columnconfigure(0, weight=0) 
    dt_input_frame.grid_columnconfigure(2, weight=0)


    tk.Label(dt_input_frame, text="Enter Entry Details", bg="white", fg="#212529", font=header_font).grid(row=0, column=0, columnspan=4, pady=(0,10), sticky="w")
    ttk.Separator(dt_input_frame, orient='horizontal').grid(row=1, column=0, columnspan=4, sticky='ew', pady=5, padx=5)

    current_row = 2
    entry_field_char_width = 30

    tk.Label(dt_input_frame, text="Semester/Label:", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=0, sticky="w", pady=2)
    dt_semester_label_entry = ttk.Entry(dt_input_frame, font=normal_font, width=entry_field_char_width)
    # Changed sticky to "w"
    dt_semester_label_entry.grid(row=current_row, column=1, sticky="w", pady=2, padx=(0,15)) 

    tk.Label(dt_input_frame, text="Shift:", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=2, sticky="w", pady=2, padx=(10,0))
    dt_shift_combobox = ttk.Combobox(dt_input_frame, values=["Morning", "Evening"], font=normal_font, state="readonly", width=entry_field_char_width -3)
    # Changed sticky to "w"
    dt_shift_combobox.grid(row=current_row, column=3, sticky="w", pady=2, padx=(0,15)) 
    dt_shift_combobox.set("Morning")
    current_row += 1

    tk.Label(dt_input_frame, text="Class Section:", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=0, sticky="w", pady=2)
    dt_class_section_entry = ttk.Entry(dt_input_frame, font=normal_font, width=entry_field_char_width)
    # Changed sticky to "w"
    dt_class_section_entry.grid(row=current_row, column=1, sticky="w", pady=2, padx=(0,15))

    tk.Label(dt_input_frame, text="Teacher Name:", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=2, sticky="w", pady=2, padx=(10,0))
    dt_teacher_name_entry = ttk.Entry(dt_input_frame, font=normal_font, width=entry_field_char_width)
    # Changed sticky to "w"
    dt_teacher_name_entry.grid(row=current_row, column=3, sticky="w", pady=2, padx=(0,15))
    current_row += 1

    tk.Label(dt_input_frame, text="Course Name:", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=0, sticky="w", pady=2)
    dt_course_name_entry = ttk.Entry(dt_input_frame, font=normal_font, width=entry_field_char_width)
    # Changed sticky to "w"
    dt_course_name_entry.grid(row=current_row, column=1, sticky="w", pady=2, padx=(0,15))

    tk.Label(dt_input_frame, text="Course Code:", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=2, sticky="w", pady=2, padx=(10,0))
    dt_course_code_entry = ttk.Entry(dt_input_frame, font=normal_font, width=entry_field_char_width)
    # Changed sticky to "w"
    dt_course_code_entry.grid(row=current_row, column=3, sticky="w", pady=2, padx=(0,15))
    current_row += 1

    tk.Label(dt_input_frame, text="Lab (e.g. Lab C1):", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=0, sticky="w", pady=2)
    dt_indicators_entry = ttk.Entry(dt_input_frame, font=normal_font, width=entry_field_char_width)
    # Changed sticky to "w"
    dt_indicators_entry.grid(row=current_row, column=1, sticky="w", pady=2, padx=(0,15))

    tk.Label(dt_input_frame, text="Room(s):", bg="white", fg="#495057", font=normal_font).grid(row=current_row, column=2, sticky="w", pady=2, padx=(10,0))
    dt_room_entry = ttk.Entry(dt_input_frame, font=normal_font, width=entry_field_char_width)
    # Changed sticky to "w"
    dt_room_entry.grid(row=current_row, column=3, sticky="w", pady=2, padx=(0,15))
    current_row += 1

    input_actions_frame = tk.Frame(dt_input_frame, bg="white")
    input_actions_frame.grid(row=current_row, column=0, columnspan=4, sticky="w", pady=(10,0))
    save_action_button = tk.Button(input_actions_frame, text="Save Entry", font=button_font, bg="#28a745", fg="white",
                                   command=save_or_update_dt_entry, relief=tk.FLAT, padx=10, pady=3)
    save_action_button.pack(side="left", padx=(0,10))
    
    # --- Display Frame (Notebook for Tabs) ---
    dt_display_frame = tk.Frame(DT_main_content_frame, bg="#f8f9fa", padx=20, pady=10)
    dt_display_frame.pack(side="bottom", fill="both", expand=True)

    tree_header_frame = tk.Frame(dt_display_frame, bg="#f8f9fa")
    tree_header_frame.pack(fill="x", pady=(0,5))
    tk.Label(tree_header_frame, text="Saved Entries by Semester-Section", bg="#f8f9fa", fg="#212529", font=header_font).pack(side="left", anchor="w")
    dt_entries_count_label = tk.Label(tree_header_frame, text="", bg="#f8f9fa", fg="#495057", font=normal_font)
    dt_entries_count_label.pack(side="left", padx=(10,0), anchor="w")
    # Removed loaded_db_info_label

    notebook = ttk.Notebook(dt_display_frame)
    notebook.pack(fill="both", expand=True, pady=(5,0))
    notebook.bind("<<NotebookTabChanged>>", on_tab_change)


    # --- Bottom Action Buttons ---
    tree_btn_frame = tk.Frame(dt_display_frame, bg="#f8f9fa") # Placed inside dt_display_frame, below notebook
    tree_btn_frame.pack(fill='x', pady=(10,0))

    tk.Button(tree_btn_frame, text="Load from DB", font=button_font, bg="#007bff", fg="white",
              command=load_entries_from_db, relief=tk.FLAT, padx=10, pady=3).pack(side='left', padx=(0,5))
    tk.Button(tree_btn_frame, text="Edit Selected", font=button_font, bg="#ffc107", fg="black", # Yellow
              command=prepare_to_edit_selected_entry, relief=tk.FLAT, padx=10, pady=3).pack(side="left", padx=(0,10))
    tk.Button(tree_btn_frame, text="Delete Selected", font=button_font, bg="#dc3545", fg="white",
              command=delete_dt_selected_entries, relief=tk.FLAT, padx=10, pady=3).pack(side='left', padx=(0,5))
    tk.Button(tree_btn_frame, text="Clear All UI Entries", font=button_font, bg="#6c757d", fg="white",
              command=clear_all_ui_entries, relief=tk.FLAT, padx=10, pady=3).pack(side='left', padx=(0,5))
    
    tk.Button(tree_btn_frame, text="Generate Datesheet", font=button_font, bg="#0069d9", fg="white",
              command=generate_datesheet_dialog, relief=tk.FLAT, padx=10, pady=3).pack(side='right', padx=(5,0))

    update_all_tabs_display() # Initial call to set up if any default tabs or structure is needed
    update_dt_entries_count_label() # Show initial count

def on_tab_change(event):
    # This function can be used if actions need to happen when a tab is selected
    # For example, refreshing data or enabling/disabling buttons based on active tab content
    clear_dt_input_form() # Clear form when tab changes to avoid accidental edits on wrong item
    # print(f"Switched to tab: {get_active_tab_id()}")
    pass

def _create_treeview_in_tab(tab_frame, tab_id):
    global _normal_font # Access the font passed during initialization

    tree_container = tk.Frame(tab_frame, bg="#f8f9fa")
    tree_container.pack(fill="both", expand=True)

    # Add "S.No" as the first data column after the checkbox
    columns = ("S.No", "Semester/Label", "Shift", "Class", "Teacher", "Course", "Code", "Lab", "Room")
    tree = ttk.Treeview(tree_container, columns=columns, show='tree headings', selectmode='none' # selectmode='none' as we use checkboxes
    )

    style = ttk.Style()
    heading_font_tuple = ("Helvetica", 10, "bold") # Default
    if _normal_font: # Use the passed font if available
        if isinstance(_normal_font, (list, tuple)) and len(_normal_font) >= 2:
            heading_font_tuple = (_normal_font[0], _normal_font[1], 'bold')
        elif hasattr(_normal_font, 'actual'): # tk.font.Font object
            heading_font_tuple = (_normal_font.actual()['family'], _normal_font.actual()['size'], 'bold')
    style.configure("Treeview.Heading", font=heading_font_tuple)

    # Configure the special #0 column for checkboxes
    tree.heading("#0", text="Select")
    tree.column("#0", width=50, minwidth=40, stretch=tk.NO, anchor='center')

    # Add S.No column config
    col_configs = [
        ("S.No", "S.No", 50),
        ("Semester/Label", "Semester/Label", 120), ("Shift", "Shift", 70),
        ("Class", "Class", 100), ("Teacher", "Teacher", 120), ("Course", "Course", 150),
        ("Code", "Code", 70), ("Lab", "Lab", 100), ("Room", "Room", 70)
    ]
    for col_id_text, text, width in col_configs:
        tree.heading(col_id_text, text=text)
        tree.column(col_id_text, width=width, anchor='center' if col_id_text == "S.No" or text in ["Shift", "Code", "Room"] else 'w', minwidth=max(40, width-20))

    scrollbar_y = ttk.Scrollbar(tree_container, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_y.set)
    
    tree.pack(side='left', fill='both', expand=True)
    scrollbar_y.pack(side='right', fill='y')

    tree.bind("<Button-1>", lambda event, current_tab_id=tab_id: on_tree_click(event, current_tab_id))
    
    tab_treeviews[tab_id] = tree
    if tab_id not in tab_entry_data:
        tab_entry_data[tab_id] = []
    return tree

def on_tree_click(event, tab_id):
    tree = get_treeview_for_tab(tab_id)
    if not tree: return

    region = tree.identify_region(event.x, event.y)
    item_iid = tree.identify_row(event.y)

    if not item_iid: return # Clicked outside of any item

    if region == "tree": # Click was on the #0 column (checkbox column)
        entry_list = get_data_for_tab(tab_id)
        found_entry = None
        entry_idx = -1

        # Find the corresponding entry in our data store by its unique 'id'
        # The item_iid from treeview is what we stored as 'id' when inserting.
        for idx, entry_wrapper in enumerate(entry_list):
            if entry_wrapper["id"] == item_iid:
                found_entry = entry_wrapper
                entry_idx = idx
                break
        
        if found_entry:
            found_entry["checked"] = not found_entry["checked"]
            checkbox_char = '☑' if found_entry["checked"] else '☐'
            tree.item(item_iid, text=checkbox_char) # Update visual checkbox
            # print(f"Item {item_iid} in tab {tab_id} checked state: {found_entry['checked']}")


def save_or_update_dt_entry():
    global editing_item_details, save_action_button

    semester_label = dt_semester_label_entry.get().strip()
    shift = dt_shift_combobox.get().strip()
    class_section = dt_class_section_entry.get().strip()
    teacher_name = dt_teacher_name_entry.get().strip()
    course_name = dt_course_name_entry.get().strip()
    course_code = dt_course_code_entry.get().strip()
    indicators = dt_indicators_entry.get().strip()
    room = dt_room_entry.get().strip()

    if not all([semester_label, shift, class_section, course_name, room]): # Core fields
        messagebox.showerror("Error", "Semester, Shift, Class Section, Course Name, and Room are required.", parent=root_window)
        return
    if not class_section: # Specifically for tab creation
        messagebox.showerror("Error", "Class Section is required for organizing entries.", parent=root_window)
        return

    entry_data_dict = {
        "semester_label": semester_label, "shift": shift, "class_section": class_section,
        "teacher_name": teacher_name, "course_name": course_name, "course_code": course_code,
        "indicators": indicators, "room": room
    }

    target_tab_id = f"{semester_label}-{class_section}"

    if editing_item_details: # UPDATE existing entry
        original_tab_id = editing_item_details['tab_id']
        item_id_to_update = editing_item_details['item_id']
        data_list_index = editing_item_details['data_list_index']
        
        # Check if semester/section changed, meaning it might move tabs
        if original_tab_id != target_tab_id:
            # Remove from old tab's data
            old_tab_data_list = get_data_for_tab(original_tab_id)
            if 0 <= data_list_index < len(old_tab_data_list) and old_tab_data_list[data_list_index]["id"] == item_id_to_update:
                old_tab_data_list.pop(data_list_index)
            update_tab_display(original_tab_id) # Refresh old tab
            if not get_data_for_tab(original_tab_id) and original_tab_id in notebook.tabs(): # If old tab is now empty
                idx_to_remove = -1
                for i, tab_widget_id in enumerate(notebook.tabs()):
                    if notebook.tab(tab_widget_id, "text") == original_tab_id:
                        idx_to_remove = i
                        break
                if idx_to_remove != -1:
                    notebook.forget(idx_to_remove)
                if original_tab_id in tab_treeviews: del tab_treeviews[original_tab_id]
                if original_tab_id in tab_entry_data: del tab_entry_data[original_tab_id]


            # Add to new tab's data (as a new entry essentially, but it's an update that moved)
            _add_entry_to_tab(target_tab_id, entry_data_dict, switch_to_tab=True)
        else: # Update in the same tab
            tab_data_list = get_data_for_tab(original_tab_id)
            tab_data_list[data_list_index]["data"] = entry_data_dict
            # No need to change "checked" status or "id"
            update_tab_display(original_tab_id) # Refresh current tab
        
        clear_dt_input_form() # This will also reset button text and editing_item_details
        update_dt_entries_count_label()
    else: # ADD new entry
        _add_entry_to_tab(target_tab_id, entry_data_dict, switch_to_tab=True)
        clear_dt_input_form()
        update_dt_entries_count_label()

def _add_entry_to_tab(tab_id, entry_data_dict, switch_to_tab=False):
    if tab_id not in tab_treeviews: # New tab needs to be created
        tab_frame = ttk.Frame(notebook)
        notebook.add(tab_frame, text=tab_id)
        _create_treeview_in_tab(tab_frame, tab_id)
        # tab_entry_data[tab_id] is initialized in _create_treeview_in_tab
    
    new_item_id = str(uuid.uuid4()) # Generate a unique ID for this entry item
    tab_entry_data[tab_id].append({"id": new_item_id, "checked": False, "data": entry_data_dict})
    update_tab_display(tab_id)
    update_dt_entries_count_label()
    
    if switch_to_tab:
        for i, tab_widget_id in enumerate(notebook.tabs()):
            if notebook.tab(tab_widget_id, "text") == tab_id:
                notebook.select(i)
                break


def clear_dt_input_form():
    global editing_item_details
    dt_semester_label_entry.delete(0, tk.END)
    dt_shift_combobox.set("Morning")
    dt_class_section_entry.delete(0, tk.END)
    dt_teacher_name_entry.delete(0, tk.END)
    dt_course_name_entry.delete(0, tk.END)
    dt_course_code_entry.delete(0, tk.END)
    dt_indicators_entry.delete(0, tk.END)
    dt_room_entry.delete(0, tk.END)
    
    if editing_item_details:
        save_action_button.config(text="Save Entry", bg="#28a745") # Green
    editing_item_details = None
    dt_semester_label_entry.focus()

def update_tab_display(tab_id):
    tree = get_treeview_for_tab(tab_id)
    if not tree: return

    for item in tree.get_children():
        tree.delete(item)
    
    # Insert serial number as the first value
    for idx, entry_wrapper in enumerate(get_data_for_tab(tab_id), start=1):
        e = entry_wrapper["data"]
        item_id = entry_wrapper["id"]
        checkbox_char = '☑' if entry_wrapper["checked"] else '☐'
        tree.insert('', 'end', iid=item_id, text=checkbox_char, values=(
            idx,
            e.get('semester_label', ''), e.get('shift', ''), e.get('class_section', ''),
            e.get('teacher_name', ''), e.get('course_name', ''), e.get('course_code', ''),
            e.get('indicators', ''), e.get('room', '')
        ))
    update_dt_entries_count_label()  # Update count after display

def update_all_tabs_display():
    for tab_id in tab_treeviews.keys():
        update_tab_display(tab_id)
    update_dt_entries_count_label()  # Update count after all tabs

def update_dt_entries_count_label():
    """Update the label showing the total number of entries across all tabs."""
    if dt_entries_count_label:
        total = sum(len(entries) for entries in tab_entry_data.values())
        dt_entries_count_label.config(text=f"Total Entries: {total}")

def on_tree_click(event, tab_id):
    tree = get_treeview_for_tab(tab_id)
    if not tree: return

    region = tree.identify_region(event.x, event.y)
    item_iid = tree.identify_row(event.y)

    if not item_iid: return # Clicked outside of any item

    if region == "tree": # Click was on the #0 column (checkbox column)
        entry_list = get_data_for_tab(tab_id)
        found_entry = None
        entry_idx = -1

        # Find the corresponding entry in our data store by its unique 'id'
        # The item_iid from treeview is what we stored as 'id' when inserting.
        for idx, entry_wrapper in enumerate(entry_list):
            if entry_wrapper["id"] == item_iid:
                found_entry = entry_wrapper
                entry_idx = idx
                break
        
        if found_entry:
            found_entry["checked"] = not found_entry["checked"]
            checkbox_char = '☑' if found_entry["checked"] else '☐'
            tree.item(item_iid, text=checkbox_char) # Update visual checkbox
            # print(f"Item {item_iid} in tab {tab_id} checked state: {found_entry['checked']}")


def delete_dt_selected_entries():
    active_tab_id = get_active_tab_id()
    if not active_tab_id:
        messagebox.showinfo("Info", "No active tab to delete entries from.", parent=root_window)
        return

    tab_data_list = get_data_for_tab(active_tab_id)
    items_to_delete_indices = [idx for idx, entry_wrapper in enumerate(tab_data_list) if entry_wrapper["checked"]]

    if not items_to_delete_indices:
        messagebox.showinfo("Info", "Select entries (tick checkboxes) to delete.", parent=root_window)
        return
    
    if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(items_to_delete_indices)} selected entries from tab '{active_tab_id}'?", parent=root_window):
        return

    # Iterate backwards to avoid index shifting issues when popping
    for idx in sorted(items_to_delete_indices, reverse=True):
        tab_data_list.pop(idx)
    
    update_tab_display(active_tab_id)
    
    # If tab becomes empty, remove it
    if not tab_data_list and active_tab_id in notebook.tabs():
        idx_to_remove = -1
        # Find the index of the tab in the notebook widget
        for i, tab_widget_id in enumerate(notebook.tabs()):
            if notebook.tab(tab_widget_id, "text") == active_tab_id:
                idx_to_remove = i
                break
        if idx_to_remove != -1:
            notebook.forget(idx_to_remove) # Remove tab from notebook
        
        # Clean up data structures
        if active_tab_id in tab_treeviews:
            del tab_treeviews[active_tab_id]
        if active_tab_id in tab_entry_data: # Should be empty now, but good to ensure
            del tab_entry_data[active_tab_id]


    clear_dt_input_form() # Reset form and edit state if any deleted item was being edited (unlikely with this flow but good practice)
    update_dt_entries_count_label()

def clear_all_ui_entries():
    global tab_entry_data, tab_treeviews, editing_item_details
    if not any(tab_entry_data.values()): # Check if any tab has data
        messagebox.showinfo("Info", "There are no entries to clear.", parent=root_window)
        return
    if messagebox.askyesno("Confirm Clear All", "Are you sure you want to clear all entries from all tabs?", parent=root_window):
        for tab_id_str in list(notebook.tabs()): # Iterate over a copy of tab identifiers
            notebook.forget(tab_id_str) # Remove tab from UI

        tab_entry_data.clear()
        tab_treeviews.clear()
        clear_dt_input_form() # Resets button and editing state
        update_dt_entries_count_label()

def prepare_to_edit_selected_entry():
    global editing_item_details, save_action_button

    active_tab_id = get_active_tab_id()
    if not active_tab_id:
        messagebox.showinfo("Info", "No active tab to edit entries from.", parent=root_window)
        return

    tab_data_list = get_data_for_tab(active_tab_id)
    checked_items = [(idx, entry_wrapper) for idx, entry_wrapper in enumerate(tab_data_list) if entry_wrapper["checked"]]

    if not checked_items:
        messagebox.showinfo("Info", "Select an entry (tick a checkbox) to edit.", parent=root_window)
        return
    if len(checked_items) > 1:
        messagebox.showinfo("Info", "Please select only one entry to edit at a time.", parent=root_window)
        return

    idx, entry_wrapper = checked_items[0]
    entry_data = entry_wrapper["data"]

    # Fill the form with the selected entry's data
    dt_semester_label_entry.delete(0, tk.END)
    dt_semester_label_entry.insert(0, entry_data.get("semester_label", ""))
    dt_shift_combobox.set(entry_data.get("shift", "Morning"))
    dt_class_section_entry.delete(0, tk.END)
    dt_class_section_entry.insert(0, entry_data.get("class_section", ""))
    dt_teacher_name_entry.delete(0, tk.END)
    dt_teacher_name_entry.insert(0, entry_data.get("teacher_name", ""))
    dt_course_name_entry.delete(0, tk.END)
    dt_course_name_entry.insert(0, entry_data.get("course_name", ""))
    dt_course_code_entry.delete(0, tk.END)
    dt_course_code_entry.insert(0, entry_data.get("course_code", ""))
    dt_indicators_entry.delete(0, tk.END)
    dt_indicators_entry.insert(0, entry_data.get("indicators", ""))
    dt_room_entry.delete(0, tk.END)
    dt_room_entry.insert(0, entry_data.get("room", ""))

    editing_item_details = {
        'tab_id': active_tab_id,
        'item_id': entry_wrapper["id"],
        'data_list_index': idx
    }
    save_action_button.config(text="Update Entry", bg="#ffc107") # Yellow

def load_entries_from_db():
    global tab_entry_data, tab_treeviews, notebook
    filepath = filedialog.askopenfilename(
        title="Select Timetable SQLite Database File",
        defaultextension=".db", filetypes=[("SQLite Database files", "*.db"), ("All files", "*.*")],
        parent=root_window
    )
    if not filepath: return

    # --- Get shift from input field ---
    selected_shift = dt_shift_combobox.get().strip()
    if not selected_shift:
        messagebox.showwarning("Missing Shift", "Please select a shift in the input form before loading.", parent=root_window)
        return

    new_loaded_entries_map = {} # Temp map: { "tab_id": [entry_data_dict, ...], ... }

    try:
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # Query to load all relevant data, adjust table/column names as per your DB schema
        # Modified query to exclude entries with indicators
        query = """
            SELECT 
                t.semester, t.shift,
                cs.name AS class_section_name,
                th.name AS teacher_name,
                c.name AS course_name, c.code AS course_code, c.indicators AS course_indicators,
                r.name AS room_name
            FROM timetable t
            JOIN teachers th ON t.teacher_id = th.id
            JOIN courses c ON t.course_id = c.id
            JOIN rooms r ON t.room_id = r.id
            JOIN class_sections cs ON t.class_section_id = cs.id
            WHERE c.indicators IS NULL OR c.indicators = ''
        """ # This query assumes your schema. Adjust if necessary.
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("No Data", "No entries found in the selected database with the expected structure.", parent=root_window)
            return

        # --- Filter rows by selected shift ---
        filtered_rows = [row for row in rows if str(row[1]).strip().lower() == selected_shift.lower()]

        if not filtered_rows:
            messagebox.showinfo("No Data", f"No entries found for shift '{selected_shift}' in the selected database.", parent=root_window)
            return

        for row in filtered_rows:
            entry_data = {
                "semester_label": row[0], "shift": row[1], "class_section": row[2],
                "teacher_name": row[3], "course_name": row[4], "course_code": row[5],
                "indicators": row[6], "room": str(row[7]) 
            }
            tab_id = f"{entry_data['semester_label']}-{entry_data['class_section']}"
            if not entry_data['semester_label'] or not entry_data['class_section']:
                print(f"Skipping entry due to missing semester/section for tab ID: {entry_data}")
                continue # Skip if essential for tab creation

            if tab_id not in new_loaded_entries_map:
                new_loaded_entries_map[tab_id] = []
            new_loaded_entries_map[tab_id].append(entry_data)

        if not new_loaded_entries_map:
             messagebox.showinfo("No Usable Data", "No entries could be grouped by semester/section.", parent=root_window)
             return

        if not messagebox.askyesno("Confirm Load", f"{sum(len(v) for v in new_loaded_entries_map.values())} entries found for shift '{selected_shift}', grouped into {len(new_loaded_entries_map)} semester-section tabs. Replace current UI entries?", parent=root_window):
            return

        # Clear existing UI entries
        clear_all_ui_entries() # This also clears tab_entry_data and tab_treeviews

        for tab_id, entries_list in new_loaded_entries_map.items():
            if tab_id not in tab_treeviews: # Create tab if it doesn't exist (it shouldn't after clear_all)
                tab_frame = ttk.Frame(notebook)
                notebook.add(tab_frame, text=tab_id)
                _create_treeview_in_tab(tab_frame, tab_id)
            
            for entry_data_dict in entries_list:
                 new_item_id = str(uuid.uuid4())
                 tab_entry_data[tab_id].append({"id": new_item_id, "checked": False, "data": entry_data_dict})
            update_tab_display(tab_id)
        
        if notebook.tabs(): # Select the first tab if any were created
            notebook.select(0)

        update_dt_entries_count_label()
        messagebox.showinfo("Success", f"Data loaded into {len(tab_entry_data)} tabs for shift '{selected_shift}'.", parent=root_window)
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to load data: {e}", parent=root_window)
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=root_window)
        import traceback
        traceback.print_exc()


def generate_datesheet_dialog():
    # Dialog for metadata and generation parameters
    dialog = tk.Toplevel(root_window)
    dialog.title("Configure Date Sheet Generation")
    dialog.geometry("900x800")
    dialog.resizable(True, True)
    dialog.grab_set()

    # Center dialog
    dialog.update_idletasks()
    x = (root_window.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (root_window.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f'+{x}+{y}')

    main_frame = tk.Frame(dialog, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    # --- Metadata Section ---
    tk.Label(main_frame, text="Date Sheet Metadata", font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))

    ds_college_name_var = tk.StringVar(value="GOVT. ISLAMIA GRADUATE COLLEGE, CIVIL LINES, LAHORE")
    ds_title_var = tk.StringVar(value="DATE SHEET FOR BS PROGRAMS")
    ds_effective_date_var = tk.StringVar(value="")
    ds_department_name_var = tk.StringVar(value="DEPARTMENT OF COMPUTER SCIENCE")

    tk.Label(main_frame, text="College Name:").grid(row=1, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=ds_college_name_var, width=50).grid(row=1, column=1, sticky="ew", pady=2)

    tk.Label(main_frame, text="Date Sheet Title:").grid(row=2, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=ds_title_var, width=50).grid(row=2, column=1, sticky="ew", pady=2)

    tk.Label(main_frame, text="Effective Date (DD-MM-YYYY):").grid(row=3, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=ds_effective_date_var, width=20).grid(row=3, column=1, sticky="w", pady=2)

    tk.Label(main_frame, text="Department Name:").grid(row=4, column=0, sticky="w", pady=2)
    tk.Entry(main_frame, textvariable=ds_department_name_var, width=50).grid(row=4, column=1, sticky="ew", pady=2)

    ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)

    # --- Generation Parameters ---
    tk.Label(main_frame, text="Generation Parameters", font=("Helvetica", 12, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0,10))

    tk.Label(main_frame, text="Exam Start Date (YYYY-MM-DD):").grid(row=7, column=0, sticky="w", pady=2)
    start_date_var = tk.StringVar()
    tk.Entry(main_frame, textvariable=start_date_var, width=20).grid(row=7, column=1, sticky="w", pady=2)

    tk.Label(main_frame, text="Exam Start Time (HH:MM AM/PM, e.g., 09:00 AM):").grid(row=8, column=0, sticky="w", pady=2)
    exam_start_time_var = tk.StringVar(value="09:00 AM")
    tk.Entry(main_frame, textvariable=exam_start_time_var, width=20).grid(row=8, column=1, sticky="w", pady=2)

    tk.Label(main_frame, text="Exam End Time (HH:MM AM/PM, e.g., 01:00 PM):").grid(row=9, column=0, sticky="w", pady=2)
    exam_end_time_var = tk.StringVar(value="01:00 PM")
    tk.Entry(main_frame, textvariable=exam_end_time_var, width=20).grid(row=9, column=1, sticky="w", pady=2)

    # Days of the week (Sunday excluded)
    tk.Label(main_frame, text="Exam Days:").grid(row=10, column=0, sticky="w", pady=2)
    days_frame = tk.Frame(main_frame)
    days_frame.grid(row=10, column=1, sticky="w")
    day_vars = {}
    days_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for i, day_text in enumerate(days_options):
        var = tk.BooleanVar(value=True)
        cb_day = ttk.Checkbutton(days_frame, text=day_text, variable=var)
        cb_day.pack(side="left", padx=2)
        day_vars[day_text] = var

    # Additional Excluded Dates
    tk.Label(main_frame, text="Additional Excluded Dates (comma-separated YYYY-MM-DD):").grid(row=11, column=0, sticky="w", pady=2)
    excluded_dates_var = tk.StringVar()
    tk.Entry(main_frame, textvariable=excluded_dates_var, width=40).grid(row=11, column=1, sticky="w", pady=2)

    # --- Dialog Buttons ---
    dialog_btn_frame = tk.Frame(main_frame)
    dialog_btn_frame.grid(row=20, column=0, columnspan=2, pady=20)

    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors as reportlab_colors
        from reportlab.lib.units import inch
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False

    def to_24h(time_str):
        import datetime as dtmod
        try:
            return dtmod.datetime.strptime(time_str.strip(), "%I:%M %p").strftime("%H:%M")
        except Exception:
            return time_str.strip()

    def to_ampm(time_str):
        import datetime as dtmod
        try:
            return dtmod.datetime.strptime(time_str.strip(), "%H:%M").strftime("%I:%M %p")
        except Exception:
            return time_str.strip()

    def export_datesheet_to_pdf(metadata, grouped_by_date, sorted_dates, exam_start_time_24, exam_end_time_24):
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Missing Library", "ReportLab library is not installed.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Datesheet as PDF"
        )
        if not filepath:
            return

        try:
            from reportlab.lib.pagesizes import landscape, A4
            # Use landscape A4 and wider margins
            doc = SimpleDocTemplate(
                filepath,
                pagesize=landscape(A4),
                rightMargin=10,    # Reduced right margin
                leftMargin=10,     # Reduced left margin
                topMargin=30,
                bottomMargin=30
            )
            styles = getSampleStyleSheet()
            story = []

            def add_metadata():
                story.append(Paragraph(f"<b>{metadata.get('college_name','')}</b>", styles['Title']))
                story.append(Paragraph(metadata.get('datesheet_title', ''), styles['Heading2']))
                story.append(Paragraph(f"Effective Date: {metadata.get('effective_date', '')}", styles['Normal']))
                story.append(Paragraph(f"Department: {metadata.get('department_name', '')}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))

            add_metadata()

            # Build table data for all dates (no PageBreak)
            for idx, date_str in enumerate(sorted_dates):
                exams = grouped_by_date[date_str]
                # Date as "Monday, June 2, 2025"
                try:
                    import datetime as dtmod
                    dt_obj = dtmod.datetime.strptime(date_str, "%Y-%m-%d")
                    date_display = dt_obj.strftime("%A, %B %-d, %Y") if hasattr(dt_obj, "strftime") else date_str
                except Exception:
                    date_display = date_str

                table_data = [
                    ["Date & Day", "Semester/Section", "Subject (Code)", "Time", "Room", "Invigilator"]
                ]
                for e_sched in exams:
                    # Get standard data values
                    sem_sec = f"{e_sched.get('semester','')} / {e_sched.get('class_section','')}"
                    subj_code = f"{e_sched.get('subject','')} – {e_sched.get('course_code','')}"
                    room = e_sched.get('room','')
                    invigilator = e_sched.get('teacher','')
                    
                    # Format date and day together
                    try:
                        dt_obj = dtmod.datetime.strptime(date_str, "%Y-%m-%d")
                        date_day_display = f"{dt_obj.strftime('%d-%m-%Y')}\n{dt_obj.strftime('%A')}"
                    except Exception:
                        date_day_display = date_str
                    
                    # Get time range
                    start_ampm = to_ampm(e_sched.get('time', exam_start_time_24))
                    end_ampm = to_ampm(exam_end_time_24)
                    time_range = f"{start_ampm} - {end_ampm}"

                    table_data.append([
                        date_day_display,
                        sem_sec,
                        subj_code,
                        time_range,
                        room,
                        invigilator
                    ])

                # Adjusted column widths to fit content better
                col_widths = [2.2*inch, 2.0*inch, 2.5*inch, 1.5*inch, 1.0*inch, 2.0*inch]
                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                
                # Added wordWrap to table style
                style = TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, reportlab_colors.black),
                    ('BACKGROUND', (0,0), (-1,0), reportlab_colors.HexColor('#0d6efd')),
                    ('TEXTCOLOR', (0,0), (-1,0), reportlab_colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,0), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 11),
                    ('FONTSIZE', (0,1), (-1,-1), 9),  # Slightly smaller font for content
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ALIGN', (0,1), (-1,-1), 'CENTER'),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [reportlab_colors.whitesmoke, reportlab_colors.lightgrey]),
                    ('WORDWRAP', (0,0), (-1,-1), True),  # Enable word wrapping
                ])
                table.setStyle(style)
                story.append(table)
                story.append(Spacer(1, 0.2*inch))
                # --- Removed PageBreak ---

            doc.build(story)
            messagebox.showinfo("Success", f"Datesheet exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export to PDF: {e}")
            import traceback
            traceback.print_exc()

    def validate_and_run_datesheet_generation():
        # Collect metadata
        metadata = {
            "college_name": ds_college_name_var.get(),
            "datesheet_title": ds_title_var.get(),
            "effective_date": ds_effective_date_var.get(),
            "department_name": ds_department_name_var.get()
        }
        # Collect generation parameters
        start_date = start_date_var.get().strip()
        exam_start_time = exam_start_time_var.get().strip()
        exam_end_time = exam_end_time_var.get().strip()
        selected_days = [day for day, var in day_vars.items() if var.get()]
        excluded_dates = [d.strip() for d in excluded_dates_var.get().split(",") if d.strip()]

        if not start_date:
            messagebox.showwarning("Missing Data", "Please enter the exam start date.", parent=dialog)
            return
        if not exam_start_time or not exam_end_time:
            messagebox.showwarning("Missing Data", "Please enter exam start and end times.", parent=dialog)
            return
        if not selected_days:
            messagebox.showwarning("No Days Selected", "Please select at least one day for exams.", parent=dialog)
            return

        # Prepare entries for GA
        all_entries_for_ga = []
        for tab_id, entries_list in tab_entry_data.items():
            for entry_wrapper in entries_list:
                entry = entry_wrapper["data"]
                all_entries_for_ga.append({
                    'subject': entry.get('course_name'),
                    'room': entry.get('room'),
                    'shift': entry.get('shift'),
                    'semester': entry.get('semester_label'),
                    'teacher': entry.get('teacher_name'),
                    'course_code': entry.get('course_code'),
                    'class_section': entry.get('class_section')
                })

        if not all_entries_for_ga:
            messagebox.showinfo("Info", "Add entries first. These entries will be considered for scheduling.", parent=dialog)
            return

        # Convert exam times to 24-hour format
        exam_start_time_24 = to_24h(exam_start_time)
        exam_end_time_24 = to_24h(exam_end_time)

        # --- Fix: Pass all required parameters to the GA ---
        try:
            ga = DatesheetGeneticAlgorithm(
                entries=all_entries_for_ga,
                max_generations=100,
                population_size=50,
                start_date=start_date,
                exam_start_time=exam_start_time_24,
                exam_end_time=exam_end_time_24,
                exam_days=selected_days,
                excluded_dates=excluded_dates
            )
            sched = ga.run()

            if not sched:
                messagebox.showinfo(
                    "Result",
                    "GA did not produce a schedule.\n\n"
                    "Possible reasons:\n"
                    "- Not enough available days for all exams (check your start date, selected days, and excluded dates)\n"
                    "- Too many exams for the available slots\n"
                    "- Data entry errors (e.g., duplicate courses for a section)\n\n"
                    "Try adjusting your parameters and try again.",
                    parent=dialog
                )
                return

            # --- Group by date for tabbed display ---
            from collections import defaultdict
            import datetime as dtmod

            grouped_by_date = defaultdict(list)
            for e_sched in sched:
                grouped_by_date[e_sched.get('date', 'N/A')].append(e_sched)

            # --- Preview window with metadata and export button ---
            win = tk.Toplevel(root_window)
            win.title("Optimized Datesheet Preview")
            win.geometry("1100x700")
            win.grab_set()

            # --- Metadata display at top ---
            meta_frame = tk.Frame(win, pady=10)
            meta_frame.pack(fill="x")
            tk.Label(meta_frame, text=metadata.get("college_name", ""), font=("Helvetica", 16, "bold")).pack()
            tk.Label(meta_frame, text=metadata.get("datesheet_title", ""), font=("Helvetica", 13)).pack()
            tk.Label(meta_frame, text=f"Effective Date: {metadata.get('effective_date', '')}", font=("Helvetica", 10)).pack()
            tk.Label(meta_frame, text=f"Department: {metadata.get('department_name', '')}", font=("Helvetica", 10, "italic")).pack()

            # --- Export to PDF button ---
            export_btn_frame = tk.Frame(win, pady=10)
            export_btn_frame.pack(fill="x")
            sorted_dates = sorted(grouped_by_date.keys(), key=lambda d: d if d == 'N/A' else dtmod.datetime.strptime(d, "%Y-%m-%d"))
            tk.Button(export_btn_frame, text="Export to PDF", bg="#dc3545", fg="white", font=("Helvetica", 10, "bold"),
                      padx=15, pady=5,
                      command=lambda: export_datesheet_to_pdf(metadata, grouped_by_date, sorted_dates, exam_start_time_24, exam_end_time_24)).pack(side="left", padx=10)

            # --- Notebook for date tabs ---
            preview_notebook = ttk.Notebook(win)
            preview_notebook.pack(fill="both", expand=True, padx=10, pady=10)

            def to_ampm(time_str):
                try:
                    return dtmod.datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p")
                except Exception:
                    return time_str

            for date_str in sorted_dates:
                exams = grouped_by_date[date_str]
                # Determine day name
                try:
                    day_name = dtmod.datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
                except Exception:
                    day_name = "N/A"

                tab_frame = ttk.Frame(preview_notebook)
                preview_notebook.add(tab_frame, text=f"{date_str} ({day_name})")

                # Columns: Semester, Subject, Course Code, Class Section, Day, Date, Time, Room, Shift, Teacher (Invigilator)
                cols = ('Semester', 'Subject', 'Course Code', 'Class Section', 'Day', 'Date', 'Time', 'Room', 'Shift', 'Teacher (Invigilator)')
                tree_preview = ttk.Treeview(tab_frame, columns=cols, show='headings')

                tree_style = ttk.Style(tab_frame)
                heading_font_tuple_preview = ("Helvetica", 10, "bold")
                if _normal_font:
                    if isinstance(_normal_font, (list, tuple)) and len(_normal_font) >= 2:
                        heading_font_tuple_preview = (_normal_font[0], _normal_font[1], 'bold')
                    elif hasattr(_normal_font, 'actual'):
                        heading_font_tuple_preview = (_normal_font.actual()['family'], _normal_font.actual()['size'], 'bold')
                tree_style.configure("Treeview.Heading", font=heading_font_tuple_preview)

                col_configs_preview = [
                    ('Semester', 100), ('Subject', 150), ('Course Code', 80), ('Class Section', 100),
                    ('Day', 90), ('Date', 100), ('Time', 120), ('Room', 80), ('Shift', 80), ('Teacher (Invigilator)', 120)
                ]
                for c_text, c_width in col_configs_preview:
                    tree_preview.heading(c_text, text=c_text)
                    tree_preview.column(c_text, anchor='w' if c_text in ['Subject', 'Semester', 'Teacher (Invigilator)'] else 'center', width=c_width, minwidth=max(50, c_width-20))

                ysb = ttk.Scrollbar(tab_frame, orient='vertical', command=tree_preview.yview)
                xsb = ttk.Scrollbar(tab_frame, orient='horizontal', command=tree_preview.xview)
                tree_preview.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

                tree_preview.grid(row=0, column=0, sticky='nsew')
                ysb.grid(row=0, column=1, sticky='ns')
                xsb.grid(row=1, column=0, sticky='ew')

                tab_frame.grid_rowconfigure(0, weight=1)
                tab_frame.grid_columnconfigure(0, weight=1)

                # For each exam, add row with day and time range
                for e_sched in exams:
                    # Compute day name for each row (should match tab, but robust)
                    try:
                        row_day = dtmod.datetime.strptime(e_sched.get('date', ''), "%Y-%m-%d").strftime("%A")
                    except Exception:
                        row_day = "N/A"
                    # Show both start and end time in 12-hour AM/PM format
                    sched_time = e_sched.get('time') if e_sched.get('time') else exam_start_time_24
                    start_ampm = to_ampm(sched_time)
                    end_ampm = to_ampm(exam_end_time_24)
                    time_range = f"{start_ampm} - {end_ampm}"
                    tree_preview.insert('', 'end', values=(
                        e_sched.get('semester', 'N/A'),
                        e_sched.get('subject', 'N/A'),
                        e_sched.get('course_code', 'N/A'),
                        e_sched.get('class_section', 'N/A'),
                        row_day,
                        e_sched.get('date', 'N/A'),
                        time_range,
                        e_sched.get('room', 'N/A'),
                        e_sched.get('shift', e_sched.get('shift', 'N/A')),
                        e_sched.get('teacher', e_sched.get('teacher', 'N/A'))
                    ))
            dialog.destroy()
        except Exception as ex:
            messagebox.showerror("GA Execution Error", f"Failed to generate datesheet: {ex}\n\nNote: The Genetic Algorithm (datesheet_ga.py) might need adaptation.", parent=dialog)
            import traceback
            traceback.print_exc()

    tk.Button(dialog_btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side="left", padx=10)
    tk.Button(dialog_btn_frame, text="Generate", command=validate_and_run_datesheet_generation, width=10, bg="#007bff", fg="white").pack(side="right", padx=10)

# ...existing code...

def show():
    if DT_header_frame: DT_header_frame.pack(fill="x")
    if DT_main_content_frame: DT_main_content_frame.pack(fill="both", expand=True)
    # If there are tabs, select the first one by default if notebook is visible
    if notebook and notebook.tabs():
        try:
            if not notebook.select(): # If no tab is currently selected
                 notebook.select(0)
        except tk.TclError:
            pass # No tabs to select
    update_all_tabs_display()


def hide():
    if DT_header_frame: DT_header_frame.pack_forget()
    if DT_main_content_frame: DT_main_content_frame.pack_forget()

# Example usage (for testing this module standalone)
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Datesheet UI Module Test")
    root.geometry("1000x700")

    # Define some basic fonts for testing
    test_title_font = ("Helvetica", 16, "bold")
    test_header_font = ("Helvetica", 12, "bold")
    test_normal_font = ("Helvetica", 10)
    test_button_font = ("Helvetica", 10, "bold")

    def go_home_mock():
        print("Home button clicked (mock)")

    # Initialize the datesheet UI components
    initialize(root, test_title_font, test_header_font, test_normal_font, test_button_font, go_home_mock)
    
    # Pack the main frames for visibility
    show()

    # You might want to add some sample data for testing tabs
    # sample_entry_1 = {
    #     "semester_label": "Spring2024", "shift": "Morning", "class_section": "BSCS-8A",
    #     "teacher_name": "Dr. Foo", "course_name": "Algo", "course_code": "CS401",
    #     "indicators": "Lab", "room": "C1"
    # }
    # sample_entry_2 = {
    #     "semester_label": "Spring2024", "shift": "Morning", "class_section": "BSCS-8B",
    #     "teacher_name": "Dr. Bar", "course_name": "OS", "course_code": "CS402",
    #     "indicators": "", "room": "C2"
    # }
    # _add_entry_to_tab("Spring2024-BSCS-8A", sample_entry_1, switch_to_tab=True)
    # _add_entry_to_tab("Spring2024-BSCS-8B", sample_entry_2)
    # if notebook and notebook.tabs():
    #    notebook.select(0)


    root.mainloop()