import tkinter as tk
from tkinter import font as tkfont

from ui.timetable_ui import initialize as init_tt, show as show_tt, hide as hide_tt
from ui.datesheet_ui import initialize as init_dt, show as show_dt, hide as hide_dt

# Global frames for navigation
header_frame = None
main_frame = None



def return_home():
    """Hide module UIs and show home page"""
    hide_tt()
    hide_dt()
    header_frame.pack(side="top", fill="x")
    main_frame.pack(expand=True, fill="both", padx=0, pady=0)


def open_timetable():
    """Show timetable UI"""
    header_frame.pack_forget()
    main_frame.pack_forget()
    show_tt()


def open_datesheet():
    """Show datesheet UI"""
    header_frame.pack_forget()
    main_frame.pack_forget()
    show_dt()


def main():
    global header_frame, main_frame

    root = tk.Tk()
    root.title("Automatic Scheduler for GIGCCL")
    root.geometry("1280x720")
    root.state('zoomed')

    # Define fonts
    title_font = tkfont.Font(family="Helvetica", size=18, weight="bold")
    header_font = tkfont.Font(family="Helvetica", size=14, weight="bold")
    normal_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
    button_font = tkfont.Font(family="Helvetica", size=11, weight="bold")
    subtitle_font = tkfont.Font(family="Helvetica", size=12, slant="italic")

    # Initialize modules and hide them initially
    init_tt(root, title_font, header_font, normal_font, button_font, return_home)
    hide_tt()
    init_dt(root, title_font, header_font, normal_font, button_font, return_home)
    hide_dt()

    # ---------------------- Home Page ----------------------
    # Header
    header_frame = tk.Frame(root, bg="#0d6efd", height=70)
    header_frame.pack(side="top", fill="x")
    # Gradient effect using nested frames
    header_gradient = tk.Frame(header_frame, height=70)
    header_gradient.pack(fill="x")
    strip = tk.Frame(header_gradient, bg="#0d6efd", height=60)
    strip.pack(fill="x", expand=True)

    title_label = tk.Label(
        header_frame,
        text="Automatic Scheduler",
        bg="#0d6efd",
        fg="white",
        font=title_font
    )
    title_label.place(relx=0.02, rely=0.5, anchor="w")

    logo_label = tk.Label(
        header_frame,
        text="GIGCCL",
        bg="#0d6efd",
        fg="white",
        font=title_font
    )
    logo_label.place(relx=0.98, rely=0.5, anchor="e")

    # Main content frame
    main_frame = tk.Frame(root, bg="#f8f9fa")
    main_frame.pack(expand=True, fill="both", padx=0, pady=0)

    # Banner
    banner_frame = tk.Frame(main_frame, bg="#f8f9fa", height=180)
    banner_frame.pack(fill="x")
    main_heading = tk.Label(
        banner_frame,
        text="Academic Scheduling System",
        font=title_font,
        bg="#f8f9fa",
        fg="#212529"
    )
    main_heading.pack(pady=(25, 5))
    subtitle = tk.Label(
        banner_frame,
        text="Streamline your academic scheduling process with our automated tools",
        font=subtitle_font,
        bg="#f8f9fa",
        fg="#495057"
    )
    subtitle.pack(pady=5)
    description = tk.Label(
        banner_frame,
        text=(
            "Create conflict-free timetables and examination schedules\n"
            "with just a few clicks. Perfect for academic institutions of all sizes."
        ),
        font=normal_font,
        bg="#f8f9fa",
        fg="#6c757d"
    )
    description.pack(pady=10)

    # Cards container
    content_frame = tk.Frame(main_frame, bg="#f8f9fa")
    content_frame.pack(expand=True, fill="both")
    card_frame = tk.Frame(content_frame, bg="#f8f9fa")
    card_frame.pack(expand=True, fill="both")

    # Timetable Card
    tt_card = tk.Frame(card_frame, bg="white", relief="solid", borderwidth=1)
    tt_card.pack(side="left", expand=True, fill="both", padx=15, pady=10)
    tt_title = tk.Label(tt_card, text="Class Timetable Generator", font=header_font, bg="white")
    tt_title.pack(pady=5)
    tt_desc = tk.Label(
        tt_card,
        text=(
            "Create optimal class schedules\n"
            "with automatic conflict resolution.\n"
            "Ideal for schools and colleges."
        ),
        font=normal_font,
        bg="white",
        fg="#6c757d",
        justify="center"
    )
    tt_desc.pack(pady=10)
    tt_features = [
        "Conflict-free scheduling",
        "Teacher workload optimization",
        "Room allocation"
    ]
    tt_features_frame = tk.Frame(tt_card, bg="white")
    tt_features_frame.pack(pady=5)
    for feature in tt_features:
        f_frame = tk.Frame(tt_features_frame, bg="white")
        f_frame.pack(anchor="w", padx=30, pady=2)
        bullet = tk.Label(f_frame, text="•", fg="#0d6efd", bg="white", font=normal_font)
        bullet.pack(side="left", padx=(0,5))
        lbl = tk.Label(f_frame, text=feature, fg="#495057", bg="white", font=normal_font)
        lbl.pack(side="left")
    btn_timetable = tk.Button(
        tt_card,
        text="Generate Timetable",
        font=button_font,
        bg="#0d6efd",
        fg="white",
        command=open_timetable,
        padx=15,
        pady=8,
        borderwidth=0
    )
    btn_timetable.pack(pady=15)

    # Datesheet Card
    dt_card = tk.Frame(card_frame, bg="white", relief="solid", borderwidth=1)
    dt_card.pack(side="right", expand=True, fill="both", padx=15, pady=10)
    dt_title = tk.Label(dt_card, text="Examination DateSheet", font=header_font, bg="white")
    dt_title.pack(pady=5)
    dt_desc = tk.Label(
        dt_card,
        text=(
            "Plan examination schedules\n"
            "without subject conflicts.\n"
            "Simplify your exam planning process."
        ),
        font=normal_font,
        bg="white",
        fg="#6c757d",
        justify="center"
    )
    dt_desc.pack(pady=10)
    dt_features = [
        "Minimize student exam stress",
        "Spread exams appropriately",
        "Automatic conflict resolution"
    ]
    dt_features_frame = tk.Frame(dt_card, bg="white")
    dt_features_frame.pack(pady=5)
    for feature in dt_features:
        f_frame = tk.Frame(dt_features_frame, bg="white")
        f_frame.pack(anchor="w", padx=30, pady=2)
        bullet = tk.Label(f_frame, text="•", fg="#0d6efd", bg="white", font=normal_font)
        bullet.pack(side="left", padx=(0,5))
        lbl = tk.Label(f_frame, text=feature, fg="#495057", bg="white", font=normal_font)
        lbl.pack(side="left")
    btn_datesheet = tk.Button(
        dt_card,
        text="Generate DateSheet",
        font=button_font,
        bg="#0d6efd",
        fg="white",
        command=open_datesheet,
        padx=15,
        pady=8,
        borderwidth=0
    )
    btn_datesheet.pack(pady=15)

    # Footer
    footer_frame = tk.Frame(main_frame, bg="#343a40", height=30)
    footer_frame.pack(side="bottom", fill="x")
    footer_frame.pack_propagate(False)
    footer_text = tk.Label(
        footer_frame,
        text="© 2025 GIGCCL Scheduling System",
        font=normal_font,
        bg="#343a40",
        fg="white"
    )
    footer_text.pack(side="left", padx=20)
    version_text = tk.Label(
        footer_frame,
        text="v1.0",
        font=normal_font,
        bg="#343a40",
        fg="#adb5bd"
    )
    version_text.pack(side="right", padx=20)

    root.mainloop()


if __name__ == "__main__":
    main()
