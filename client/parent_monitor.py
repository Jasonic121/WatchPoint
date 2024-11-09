# parent_monitor.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass
import queue
import json
import os


class MonitorStyle:
    # Colors
    BG_COLOR = "#ffffff"
    ALERT_BG = "#ff4444"
    WARNING_BG = "#ffbb33"
    SAFE_BG = "#00C851"
    HEADER_BG = "#4B515D"

    # Fonts
    HEADER_FONT = ("Helvetica", 16, "bold")
    TITLE_FONT = ("Helvetica", 12, "bold")
    TEXT_FONT = ("Helvetica", 12)
    ALERT_FONT = ("Helvetica", 11, "bold")

    # Dimensions
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 800


@dataclass
class MonitoringAlert:
    timestamp: str
    child_name: str
    sentiment: str
    explanation: str
    alert_needed: bool
    message_range: str = ""

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "child_name": self.child_name,
            "sentiment": self.sentiment,
            "explanation": self.explanation,
            "alert_needed": self.alert_needed,
            "message_range": self.message_range
        }


class ParentMonitorWindow:
    def __init__(self, alert_queue: queue.Queue, reset_callback: Optional[Callable] = None):
        self.window = tk.Tk()
        self.window.title("Parent Monitoring Dashboard")
        self.window.geometry(f"{MonitorStyle.WINDOW_WIDTH}x{
                             MonitorStyle.WINDOW_HEIGHT}")
        self.window.configure(bg=MonitorStyle.BG_COLOR)

        self.alert_queue = alert_queue
        self.alerts = []
        self.monitoring_active = True
        self.reset_callback = reset_callback

        # Create logs directory
        self.logs_dir = "monitoring_logs"
        os.makedirs(self.logs_dir, exist_ok=True)

        self.setup_gui()
        self.start_alert_checker()
        self.load_previous_alerts()

        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind keyboard shortcuts
        self.window.bind('<Control-r>', lambda e: self.confirm_reset())
        self.window.bind('<Control-m>', lambda e: self.toggle_monitoring())

    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with controls
        header_frame = tk.Frame(
            main_frame,
            bg=MonitorStyle.HEADER_BG,
            height=60
        )
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Header label
        header_label = tk.Label(
            header_frame,
            text="Parent Monitoring Dashboard",
            font=MonitorStyle.HEADER_FONT,
            bg=MonitorStyle.HEADER_BG,
            fg="white"
        )
        header_label.pack(side=tk.LEFT, padx=10)

        # Control buttons frame
        control_frame = tk.Frame(
            header_frame,
            bg=MonitorStyle.HEADER_BG
        )
        control_frame.pack(side=tk.RIGHT, padx=10)

        # Monitor toggle button
        self.monitor_button = tk.Button(
            control_frame,
            text="Pause Monitoring",
            command=self.toggle_monitoring,
            bg=MonitorStyle.ALERT_BG,
            fg="grey"
        )
        self.monitor_button.pack(side=tk.LEFT, padx=5)

        # Reset button
        self.reset_button = tk.Button(
            control_frame,
            text="Reset Chat",
            command=self.confirm_reset,
            bg=MonitorStyle.WARNING_BG,
            fg="grey"
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # Live Monitoring Section
        monitoring_frame = ttk.LabelFrame(
            main_frame,
            text="Live Chat Monitoring",
            padding="10"
        )
        monitoring_frame.pack(fill=tk.BOTH, pady=(0, 10))

        # Status indicators
        self.alice_status = self.create_child_status(monitoring_frame, "Alice")
        self.alice_status.pack(fill=tk.X, pady=(0, 10))

        self.bob_status = self.create_child_status(monitoring_frame, "Bob")
        self.bob_status.pack(fill=tk.X)

        # Alerts Section
        alerts_header_frame = ttk.Frame(main_frame)
        alerts_header_frame.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(
            alerts_header_frame,
            text="Chat Analysis Alerts",
            font=MonitorStyle.TITLE_FONT
        ).pack(side=tk.LEFT)

        ttk.Button(
            alerts_header_frame,
            text="Export Logs",
            command=self.export_logs
        ).pack(side=tk.RIGHT)

        # Alerts display
        alerts_frame = ttk.Frame(main_frame)
        alerts_frame.pack(fill=tk.BOTH, expand=True)

        self.alerts_display = tk.Text(
            alerts_frame,
            wrap=tk.WORD,
            font=MonitorStyle.TEXT_FONT,
            height=15,
            padx=10,
            pady=5
        )
        self.alerts_display.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            alerts_frame, command=self.alerts_display.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.alerts_display.configure(yscrollcommand=scrollbar.set)

        # Configure tags
        self.alerts_display.tag_configure(
            "negative",
            background=MonitorStyle.ALERT_BG,
            foreground="white",
            spacing1=5,
            spacing3=5
        )
        self.alerts_display.tag_configure(
            "cautionary",
            background=MonitorStyle.WARNING_BG,
            foreground="black",
            spacing1=5,
            spacing3=5
        )
        self.alerts_display.tag_configure(
            "positive",
            background=MonitorStyle.SAFE_BG,
            foreground="white",
            spacing1=5,
            spacing3=5
        )

        self.alerts_display.config(state=tk.DISABLED)

    def create_child_status(self, parent, name):
        frame = ttk.Frame(parent)

        header = ttk.Label(
            frame,
            text=f"{name}'s Chat Status",
            font=MonitorStyle.TITLE_FONT
        )
        header.pack(anchor="w")

        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X, pady=5)

        sentiment_label = ttk.Label(
            status_frame,
            text="Current Sentiment:",
            font=MonitorStyle.TEXT_FONT
        )
        sentiment_label.pack(side=tk.LEFT, padx=(0, 5))

        sentiment_value = ttk.Label(
            status_frame,
            text="POSITIVE",
            font=MonitorStyle.TEXT_FONT
        )
        sentiment_value.pack(side=tk.LEFT)

        setattr(self, f"{name.lower()}_sentiment", sentiment_value)
        return frame

    def toggle_monitoring(self):
        self.monitoring_active = not self.monitoring_active
        if self.monitoring_active:
            self.monitor_button.configure(
                text="Pause Monitoring",
                bg=MonitorStyle.ALERT_BG
            )
        else:
            self.monitor_button.configure(
                text="Resume Monitoring",
                bg=MonitorStyle.SAFE_BG
            )

    def confirm_reset(self):
        if messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset all chat history and analysis?\n"
            "This cannot be undone."
        ):
            self.reset_monitoring()

    def reset_monitoring(self):
        # Clear alerts
        self.alerts = []

        # Clear displays
        self.alerts_display.config(state=tk.NORMAL)
        self.alerts_display.delete(1.0, tk.END)
        self.alerts_display.config(state=tk.DISABLED)

        # Reset status indicators
        self.update_child_status("Alice", "POSITIVE", False)
        self.update_child_status("Bob", "POSITIVE", False)

        # Save empty state
        self.save_empty_state()

        # Call reset callback if provided
        if self.reset_callback:
            self.reset_callback()

        messagebox.showinfo(
            "Reset Complete",
            "Chat history and analysis have been reset."
        )

    def save_empty_state(self):
        today_file = os.path.join(
            self.logs_dir,
            f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(today_file, 'w') as f:
            json.dump([], f)

    def update_child_status(self, child_name: str, sentiment: str, alert_needed: bool):
        sentiment_label = getattr(self, f"{child_name.lower()}_sentiment")
        sentiment_label.configure(text=sentiment)

        color = MonitorStyle.ALERT_BG if alert_needed else (
            MonitorStyle.WARNING_BG if sentiment == "CAUTIONARY"
            else MonitorStyle.SAFE_BG
        )
        sentiment_label.configure(foreground=color)

    def add_alert(self, alert: MonitoringAlert):
        self.alerts.append(alert)
        self.save_alert(alert)

        if not self.monitoring_active:
            return

        self.alerts_display.config(state=tk.NORMAL)

        alert_text = (
            f"[{alert.timestamp}] {alert.child_name}\n"
            f"Analysis Range: {alert.message_range}\n"
            f"Sentiment: {alert.sentiment}\n"
            f"Alert Needed: {'Yes' if alert.alert_needed else 'No'}\n"
            f"Analysis: {alert.explanation}\n"
            f"{'-' * 50}\n\n"
        )

        tag = alert.sentiment.lower()

        self.alerts_display.insert("1.0", alert_text, tag)
        self.alerts_display.see("1.0")
        self.alerts_display.config(state=tk.DISABLED)

        self.update_child_status(
            alert.child_name,
            alert.sentiment,
            alert.alert_needed
        )

    def save_alert(self, alert: MonitoringAlert):
        filename = os.path.join(
            self.logs_dir,
            f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
        )

        existing_alerts = []
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing_alerts = json.load(f)

        existing_alerts.append(alert.to_dict())

        with open(filename, 'w') as f:
            json.dump(existing_alerts, f, indent=2)

    def load_previous_alerts(self):
        today_file = os.path.join(
            self.logs_dir,
            f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
        )
        if os.path.exists(today_file):
            with open(today_file, 'r') as f:
                alerts = json.load(f)
                for alert_data in alerts:
                    alert = MonitoringAlert(**alert_data)
                    self.add_alert(alert)

    def export_logs(self):
        filename = f"monitoring_export_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(filename, 'w') as f:
            f.write("Chat Monitoring Logs\n")
            f.write("=" * 50 + "\n\n")

            for alert in self.alerts:
                f.write(f"Time: {alert.timestamp}\n")
                f.write(f"Child: {alert.child_name}\n")
                f.write(f"Message Range: {alert.message_range}\n")
                f.write(f"Sentiment: {alert.sentiment}\n")
                f.write(f"Alert Needed: {
                        'Yes' if alert.alert_needed else 'No'}\n")
                f.write(f"Analysis: {alert.explanation}\n")
                f.write("-" * 50 + "\n\n")

        messagebox.showinfo(
            "Export Complete",
            f"Logs exported to {filename}"
        )

    def start_alert_checker(self):
        def check_alerts():
            if self.monitoring_active:
                try:
                    alert = self.alert_queue.get_nowait()
                    if alert:
                        self.add_alert(alert)
                except queue.Empty:
                    pass
            self.window.after(100, check_alerts)

        self.window.after(100, check_alerts)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to stop monitoring?"):
            self.monitoring_active = False
            self.window.destroy()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    # Test code
    test_queue = queue.Queue()
    window = ParentMonitorWindow(test_queue)
    window.run()
