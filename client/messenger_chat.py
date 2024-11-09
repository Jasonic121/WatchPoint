# messenger_chat.py
import tkinter as tk
from tkinter import ttk
import asyncio
import threading
from queue import Queue
from client import ChatMonitorClient, Chat, SentimentResponse
from datetime import datetime
import uuid
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Create a single event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

class MessengerStyle:
    # Colors
    BG_COLOR = "#ffffff"
    SENT_BG = "#0084ff"
    RECEIVED_BG = "#e4e6eb"
    SENT_FG = "#ffffff"
    RECEIVED_FG = "#000000"
    INPUT_BG = "#f0f0f0"
    
    # Fonts
    HEADER_FONT = ("Helvetica", 14, "bold")
    MESSAGE_FONT = ("Helvetica", 11)
    INPUT_FONT = ("Helvetica", 11)
    ANALYSIS_FONT = ("Helvetica", 10)
    
    # Dimensions
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 600
    CHAT_HEIGHT = 20
    INPUT_HEIGHT = 2

class AsyncTkThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

class ChatWindow:
    def __init__(self, name, other_name, client, message_callback):
        self.window = tk.Tk()
        self.window.title(f"{name}'s Chat")
        self.window.geometry(f"{MessengerStyle.WINDOW_WIDTH}x{MessengerStyle.WINDOW_HEIGHT}")
        self.window.configure(bg=MessengerStyle.BG_COLOR)
        
        self.name = name
        self.other_name = other_name
        self.client = client
        self.message_callback = message_callback
        
        self.setup_gui()

    def setup_gui(self):
        # Main container
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Header
        header = ttk.Label(
            self.main_frame,
            text=self.other_name,
            font=MessengerStyle.HEADER_FONT,
            background=MessengerStyle.BG_COLOR
        )
        header.pack(pady=(5, 10))
        
        # Chat area
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = tk.Text(
            self.chat_frame,
            wrap=tk.WORD,
            font=MessengerStyle.MESSAGE_FONT,
            bg=MessengerStyle.BG_COLOR,
            padx=10,
            pady=5,
            relief=tk.FLAT,
            cursor="arrow"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.chat_frame)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        
        # Connect scrollbar
        self.chat_display.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.chat_display.yview)
        
        # Message tags
        self.chat_display.tag_configure(
            "sent",
            justify='right',
            rmargin=10,
            lmargin1=50,
            lmargin2=50,
            spacing1=5,
            spacing3=5
        )
        self.chat_display.tag_configure(
            "received",
            justify='left',
            rmargin=50,
            lmargin1=10,
            lmargin2=10,
            spacing1=5,
            spacing3=5
        )
        
        # Input area
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        self.message_entry = tk.Text(
            input_frame,
            font=MessengerStyle.INPUT_FONT,
            height=MessengerStyle.INPUT_HEIGHT,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.message_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))
        
        send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_message
        )
        send_button.pack(side=tk.RIGHT)
        
        # Analysis area
        self.analysis_frame = tk.LabelFrame(
            self.main_frame,
            text="Message Analysis",
            font=MessengerStyle.ANALYSIS_FONT,
            bg=MessengerStyle.BG_COLOR
        )
        self.analysis_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.analysis_display = tk.Text(
            self.analysis_frame,
            height=4,
            font=MessengerStyle.ANALYSIS_FONT,
            bg=MessengerStyle.BG_COLOR,
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.analysis_display.pack(fill=tk.X, padx=5, pady=5)
        self.analysis_display.config(state=tk.DISABLED)
        
        # Bindings
        self.message_entry.bind('<Return>', self.handle_return)
        self.message_entry.bind('<Shift-Return>', self.handle_shift_return)
        
        # Initial states
        self.chat_display.config(state=tk.DISABLED)

    def handle_return(self, event):
        if not event.state & 0x1:  # Shift not pressed
            self.send_message()
            return 'break'
        return None

    def handle_shift_return(self, event):
        return None

    def send_message(self):
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            return
        
        self.message_entry.delete("1.0", tk.END)
        self.display_message(self.name, message, is_self=True)
        self.message_callback(self.name, message)

    def display_message(self, sender: str, message: str, is_self: bool = False):
        self.chat_display.config(state=tk.NORMAL)
        
        tag_name = f"msg_{uuid.uuid4().hex[:8]}"
        tag_base = "sent" if is_self else "received"
        
        self.chat_display.tag_configure(
            tag_name,
            background=MessengerStyle.SENT_BG if is_self else MessengerStyle.RECEIVED_BG,
            foreground=MessengerStyle.SENT_FG if is_self else MessengerStyle.RECEIVED_FG,
            borderwidth=1,
            relief=tk.SOLID
        )
        
        self.chat_display.insert(tk.END, f"{message}\n", (tag_base, tag_name))
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def update_analysis(self, results: SentimentResponse):
        self.analysis_display.config(state=tk.NORMAL)
        self.analysis_display.delete("1.0", tk.END)
        
        if results.alert_needed:
            self.analysis_display.insert(tk.END, "🚨 ", "alert")
        
        self.analysis_display.insert(
            tk.END,
            f"Sentiment: {results.sentiment}\n"
            f"Explanation: {results.explanation}"
        )
        
        self.analysis_display.config(state=tk.DISABLED)

class MessengerChat:
    def __init__(self):
        self.async_handler = AsyncTkThread()
        self.client = ChatMonitorClient()
        self.message_queue = Queue()
        self.current_chat = []
        
        self.alice_window = ChatWindow("Alice", "Bob", self.client, self.handle_message)
        self.bob_window = ChatWindow("Bob", "Alice", self.client, self.handle_message)
        
        self.position_windows()
        self.start_analysis_checker()

    def position_windows(self):
        screen_width = self.alice_window.window.winfo_screenwidth()
        screen_height = self.alice_window.window.winfo_screenheight()
        
        window_width = MessengerStyle.WINDOW_WIDTH
        window_height = MessengerStyle.WINDOW_HEIGHT
        
        self.alice_window.window.geometry(
            f"{window_width}x{window_height}+{screen_width//4-window_width//2}+{screen_height//2-window_height//2}"
        )
        self.bob_window.window.geometry(
            f"{window_width}x{window_height}+{3*screen_width//4-window_width//2}+{screen_height//2-window_height//2}"
        )

    def handle_message(self, sender: str, message: str):
        self.current_chat.append(Chat(sender=sender, message=message))
        
        if sender == "Alice":
            self.bob_window.display_message("Alice", message, is_self=False)
        else:
            self.alice_window.display_message("Bob", message, is_self=False)
        
        def analyze_wrapper():
            try:
                results = self.async_handler.run(
                    self.client.analyze_chats(
                        username=f"{sender}_demo",
                        chats=self.current_chat
                    )
                )
                self.message_queue.put(results)
            except Exception as e:
                print(f"Analysis error: {e}")

        threading.Thread(target=analyze_wrapper, daemon=True).start()

    def start_analysis_checker(self):
        def check_analysis():
            try:
                results = self.message_queue.get_nowait()
                if results:
                    self.alice_window.update_analysis(results)
                    self.bob_window.update_analysis(results)
            except:
                pass
            finally:
                self.alice_window.window.after(100, check_analysis)
        
        self.alice_window.window.after(100, check_analysis)

    def run(self):
        try:
            self.alice_window.window.mainloop()
        finally:
            self.async_handler.loop.call_soon_threadsafe(self.async_handler.loop.stop)
            self.async_handler.thread.join()

if __name__ == "__main__":
    chat_app = MessengerChat()
    chat_app.run()