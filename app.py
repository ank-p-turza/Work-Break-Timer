import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
import threading
import time
import winsound
from pystray import MenuItem as item
import pystray
from PIL import Image
import sys
import pyttsx3

class Warner:
    def __init__(self):
        self.root = ttkb.Window("darkly")
        self.root.title("Work/Break Timer")
        self.root.iconbitmap("icon.ico")
        self.root.geometry("500x600")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.style = ttkb.Style()
        self.style.theme_use('darkly')
        
        self.work_time_value = tk.DoubleVar()
        self.break_time_value = tk.DoubleVar()
        self.alarm_duration_value = tk.DoubleVar()
        
        self.is_running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.icon = None
        self.icon_thread = None
        self.window_visible = True
        
        self.create_widgets()
        self.create_system_tray()
        
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', self.voices[1].id)

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="30 30 30 30")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.create_mode_switch()
        self.create_sliders()
        self.create_button()

    def create_system_tray(self):
        image = Image.open("icon.png")
        self.icon = pystray.Icon("name", image, "Work/Break Timer", menu=self.create_menu())
        self.icon_thread = threading.Thread(target=self.icon.run)
        self.icon_thread.daemon = True
        self.icon_thread.start()

    def create_menu(self):
        return pystray.Menu(
            item('Show', self.show_window, visible=lambda item: not self.window_visible),
            item('Hide', self.hide_window, visible=lambda item: self.window_visible),
            item('Exit', self.quit_window)
        )

    def show_window(self):
        self.window_visible = True
        self.root.after(0, self._show_window)
        self.icon.update_menu()

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        self.window_visible = False
        self.root.withdraw()
        self.icon.update_menu()

    def quit_window(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        if self.icon:
            self.icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def create_mode_switch(self):
        switch_frame = ttk.Frame(self.main_frame)
        switch_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.mode_switch = ttkb.Checkbutton(
            switch_frame, bootstyle="round-toggle",
            text="Dark Mode", command=self.toggle_mode,
            variable=ttkb.BooleanVar(value=True)
        )
        self.mode_switch.pack(side=tk.RIGHT)
    def create_sliders(self):
        self.create_slider("Work Time (Recommended 25 minutes):", 1, 60, self.work_time_value)
        self.create_slider("Break Time (Recommended 5 minutes):", 1, 30, self.break_time_value)
        self.create_slider("Alarm Duration (seconds):", 1, 5, self.alarm_duration_value)
    def create_slider(self, text, from_, to, variable):
        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=10)
        ttk.Label(frame, text=text, font=("Helvetica", 12)).pack(anchor="w")
        slider = ttkb.Scale(
            frame, from_=from_, to=to, variable=variable,
            length=400, bootstyle="primary"
        )
        slider.pack(fill=tk.X, pady=5)
        value_label = ttk.Label(frame, text="Selected value: 0", font=("Helvetica", 10))
        value_label.pack(anchor="e")   
        variable.trace_add('write', lambda *args: self.update_label(value_label, variable))
    def create_button(self):
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=20)
        self.button = ttkb.Button(
            button_frame, text="Start Timer",
            command=self.toggle_timer, bootstyle="primary-outline"
        )
        self.button.pack()
    def update_label(self, label, var):
        label.config(text=f"Selected value: {int(var.get())}")
    def toggle_mode(self):
        if self.style.theme.name == 'darkly':
            self.style.theme_use('cosmo')
            self.mode_switch.config(text="Light Mode")
        else:
            self.style.theme_use('darkly')
            self.mode_switch.config(text="Dark Mode")
    def toggle_timer(self):
        if self.is_running:
            self.is_running = False
            self.stop_event.set()
            self.button.config(text="Start Timer")
            if self.thread:
                self.thread.join()
        else:
            if self.work_time_value.get() == 0 or self.break_time_value.get() == 0 or self.alarm_duration_value.get() == 0:
                self.show_warning("Please set all values above 0 before starting the timer.")
                return
            self.is_running = True
            self.stop_event.clear()
            self.button.config(text="Stop Timer")
            self.thread = threading.Thread(target=self.run_loop)
            self.thread.start()
    def show_warning(self, message):
        warning_window = tk.Toplevel(self.root)
        warning_window.transient(self.root)
        warning_window.grab_set()
        warning_window.title("Warning")
        warning_window.geometry("300x100")
        ttk.Label(warning_window, text=message, wraplength=250).pack(pady=10)
        ttk.Button(warning_window, text="OK", command=warning_window.destroy).pack(pady=10)
        warning_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - warning_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - warning_window.winfo_height()) // 2
        warning_window.geometry(f"+{x}+{y}")
    def run_loop(self):
        while self.is_running:
            work_time = int(self.work_time_value.get() )* 60 
            break_time = int(self.break_time_value.get() )* 60 
            alarm_duration = int(self.alarm_duration_value.get() * 1000)  
            if self.wait_or_stop(work_time):
                break
            self.play_beep(alarm_duration)
            time.sleep(1)
            self.engine.say(f"This is break time take a {int(self.break_time_value.get())} minute break.")
            self.engine.runAndWait()
            if self.wait_or_stop(break_time):
                break
            self.play_beep(alarm_duration)
            time.sleep(1)
            self.engine.say("This is time to get back to work.")
            self.engine.runAndWait()
    def wait_or_stop(self, duration):
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.stop_event.is_set():
                return True
            time.sleep(0.1)
        return False
    def play_beep(self, beep_time):
        winsound.Beep(1000, beep_time)
    def run(self):
        self.root.mainloop()
if __name__ == "__main__":
    app = Warner()
    app.run()