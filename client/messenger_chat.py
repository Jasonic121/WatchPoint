# messenger_chat.py
import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from queue import Queue
import queue
from client import ChatMonitorClient, Chat, SentimentResponse
from datetime import datetime
import uuid
import nest_asyncio
from parent_monitor import ParentMonitorWindow, MonitoringAlert, MonitorStyle
import signal
import sys
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='chat_app.log'
)

# Apply nest_asyncio for nested event loops
nest_asyncio.apply()

class MessengerStyle:
    # Colors
    BG_COLOR = "#ffffff"
    SENT_BG = "#0084ff"
    RECEIVED_BG = "#e4e6eb"
    SENT_FG = "#ffffff"
    RECEIVED_FG = "#000000"
    INPUT_BG = "#f0f0f0"
    
    # Fonts
    HEADER_FONT = ("Helvetica", 12, "bold")
    MESSAGE_FONT = ("Helvetica", 11)
    INPUT_FONT = ("Helvetica", 11)
    
    # Dimensions
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 600

class AsyncTkThread:
    """Handles async operations in a separate thread"""
    
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.running = True
        self.thread.start()
        logging.info("AsyncTkThread initialized")

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        while self.running:
            try:
                self.loop.run_forever()
            except Exception as e:
                logging.error(f"AsyncTkThread error: {e}")
                if self.running:
                    continue
                break

    def run(self, coro):
        if not self.running:
            return None
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=30)
        except Exception as e:
            logging.error(f"Async operation error: {e}")
            return None

    def stop(self):
        self.running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=5)
        logging.info("AsyncTkThread stopped")

class ChatWindow:
    """Individual chat window for each user"""
    
    def __init__(self, name: str, other_name: str, client: ChatMonitorClient, 
                 message_callback, on_close: Optional[callable] = None):
        self.window = tk.Tk()
        self.window.title(f"{name}'s Chat")
        self.window.geometry(f"{MessengerStyle.WINDOW_WIDTH}x{MessengerStyle.WINDOW_HEIGHT}")
        self.window.configure(bg=MessengerStyle.BG_COLOR)
        
        self.name = name
        self.other_name = other_name
        self.client = client
        self.message_callback = message_callback
        self.on_close = on_close
        
        self.setup_gui()
        self.window.protocol("WM_DELETE_WINDOW", self.handle_close)
        logging.info(f"ChatWindow initialized for {name}")

    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(
            main_frame,
            text=f"Chat with {self.other_name}",
            font=MessengerStyle.HEADER_FONT
        )
        header.pack(pady=(0, 10))
        
        # Chat area
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            font=MessengerStyle.MESSAGE_FONT,
            bg=MessengerStyle.BG_COLOR,
            padx=10,
            pady=5,
            relief=tk.FLAT
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(chat_frame)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.chat_display.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.chat_display.yview)
        
        # Message input
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_entry = tk.Text(
            input_frame,
            height=3,
            font=MessengerStyle.INPUT_FONT,
            wrap=tk.WORD
        )
        self.message_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))
        
        send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message
        )
        send_button.pack(side=tk.RIGHT)
        
        # Configure message tags
        self.chat_display.tag_configure(
            "sent",
            justify='right',
            background=MessengerStyle.SENT_BG,
            foreground=MessengerStyle.SENT_FG,
            spacing1=4,
            spacing3=4,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.chat_display.tag_configure(
            "received",
            justify='left',
            background=MessengerStyle.RECEIVED_BG,
            foreground=MessengerStyle.RECEIVED_FG,
            spacing1=4,
            spacing3=4,
            relief=tk.SOLID,
            borderwidth=1
        )
        
        # Bind keys
        self.message_entry.bind('<Return>', lambda e: 'break' if self.send_message() else None)
        self.message_entry.bind('<Shift-Return>', lambda e: None)
        
        # Initial state
        self.chat_display.config(state=tk.DISABLED)

    def send_message(self) -> bool:
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            return False
        
        self.message_entry.delete("1.0", tk.END)
        self.display_message(self.name, message, is_self=True)
        self.message_callback(self.name, message)
        return True

    def display_message(self, sender: str, message: str, is_self: bool = False):
        self.chat_display.config(state=tk.NORMAL)
        
        tag = "sent" if is_self else "received"
        timestamp = datetime.now().strftime("%H:%M")
        
        self.chat_display.insert(tk.END, f"\n[{timestamp}] {sender}:\n", tag)
        self.chat_display.insert(tk.END, f"{message}\n", tag)
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def clear_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.message_entry.delete(1.0, tk.END)
        logging.info(f"Chat cleared for {self.name}")

    def handle_close(self):
        if self.on_close:
            self.on_close()
        self.window.destroy()
        logging.info(f"ChatWindow closed for {self.name}")

class MessengerChat:
    """Main chat application controller"""
    
    def __init__(self):
        self.async_handler = AsyncTkThread()
        self.client = ChatMonitorClient()
        self.message_queue = Queue()
        self.alert_queue = queue.Queue()
        self.current_chat = []
        self.running = True
        self.window_size = 15  # Sliding window size
        self.message_count = 0
        
        # Create windows
        self.parent_window = ParentMonitorWindow(
            self.alert_queue, 
            reset_callback=self.reset_chat
        )
        self.alice_window = ChatWindow(
            "Alice", "Bob", 
            self.client, 
            self.handle_message, 
            self.stop_application
        )
        self.bob_window = ChatWindow(
            "Bob", "Alice", 
            self.client, 
            self.handle_message, 
            self.stop_application
        )
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.position_windows()
        self.start_analysis_checker()
        logging.info("MessengerChat initialized")

    def get_analysis_window(self) -> List[Chat]:
        """Get the current sliding window of messages"""
        if len(self.current_chat) <= self.window_size:
            return self.current_chat
        return self.current_chat[-self.window_size:]

    def should_analyze(self) -> bool:
        """Determine if analysis should be performed"""
        if len(self.current_chat) <= self.window_size:
            return True
        return len(self.current_chat) % 5 == 0  # Analyze every 5 messages after window size

    def position_windows(self):
        """Position all windows on the screen"""
        screen_width = self.alice_window.window.winfo_screenwidth()
        screen_height = self.alice_window.window.winfo_screenheight()
        
        # Calculate dimensions
        chat_width = MessengerStyle.WINDOW_WIDTH
        chat_height = MessengerStyle.WINDOW_HEIGHT
        monitor_width = MonitorStyle.WINDOW_WIDTH
        monitor_height = MonitorStyle.WINDOW_HEIGHT
        
        # Position windows
        alice_x = (screen_width // 4) - (chat_width // 2)
        alice_y = (screen_height // 2) - (chat_height // 2)
        self.alice_window.window.geometry(f"{chat_width}x{chat_height}+{alice_x}+{alice_y}")
        
        bob_x = (3 * screen_width // 4) - (chat_width // 2)
        bob_y = alice_y
        self.bob_window.window.geometry(f"{chat_width}x{chat_height}+{bob_x}+{bob_y}")
        
        parent_x = (screen_width - monitor_width) // 2
        self.parent_window.window.geometry(f"{monitor_width}x{monitor_height}+{parent_x}+0")
        
        # Raise windows
        for window in [self.parent_window.window, self.alice_window.window, self.bob_window.window]:
            window.lift()
            window.focus_force()

    def reset_chat(self):
        """Reset all chat windows and history"""
        self.current_chat = []
        self.message_count = 0
        
        # Clear chat windows
        self.alice_window.clear_chat()
        self.bob_window.clear_chat()
        
        # Clear queues
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.alert_queue.empty():
            try:
                self.alert_queue.get_nowait()
            except queue.Empty:
                break
        
        logging.info("Chat system reset")

    def handle_message(self, sender: str, message: str):
        """Handle new message from a chat window"""
        self.current_chat.append(Chat(sender=sender, message=message))
        self.message_count += 1
        
        # Display in other window
        if sender == "Alice":
            self.bob_window.display_message("Alice", message, is_self=False)
        else:
            self.alice_window.display_message("Bob", message, is_self=False)
        
        # Analyze if needed
        if self.should_analyze():
            def analyze_wrapper():
                try:
                    analysis_window = self.get_analysis_window()
                    results = self.async_handler.run(
                        self.client.analyze_chats(
                            username=f"{sender}_demo",
                            chats=analysis_window
                        )
                    )
                    if results:
                        self.message_queue.put((sender, results))
                except Exception as e:
                    logging.error(f"Analysis error: {e}")

            threading.Thread(target=analyze_wrapper, daemon=True).start()

    def start_analysis_checker(self):
        """Start the analysis checking loop"""
        def check_analysis():
            try:
                sender, results = self.message_queue.get_nowait()
                if results:
                    window_start = max(1, len(self.current_chat) - self.window_size + 1)
                    window_end = len(self.current_chat)
                    
                    alert = MonitoringAlert(
                        timestamp=datetime.now().strftime("%H:%M:%S"),
                        child_name=sender,
                        sentiment=results.sentiment,
                        explanation=results.explanation,
                        alert_needed=results.alert_needed,
                        message_range=f"Messages {window_start} - {window_end}"
                    )
                    self.alert_queue.put(alert)
            except queue.Empty:
                pass
            finally:
                if self.running:
                    self.alice_window.window.after(100, check_analysis)
        
        self.alice_window.window.after(100, check_analysis)

    def signal_handler(self, signum, frame):
        """Handle system signals"""
        print("\nReceived signal to terminate. Cleaning up...")
        logging.info(f"Received signal {signum}")
        self.stop_application()

    def stop_application(self):
        """Clean shutdown of the application"""
        if not self.running:
            return
        
        self.running = False
        logging.info("Stopping application")
        
        if self.async_handler:
            self.async_handler.stop()
        
        for window in [self.parent_window.window, self.bob_window.window, self.alice_window.window]:
            try:
                window.destroy()
            except:
                pass
        
        logging.info("Application stopped")
        sys.exit(0)

    def run(self):
        """Start the application"""
        try:
            logging.info("Starting application")
            self.parent_window.window.mainloop()
        except Exception as e:
            logging.error(f"Application error: {e}")
        finally:
            self.stop_application()

if __name__ == "__main__":
    chat_app = MessengerChat()
    chat_app.run()