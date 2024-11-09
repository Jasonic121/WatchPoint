# client.py
import httpx
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

@dataclass
class Chat:
    sender: str
    message: str

@dataclass
class SentimentResponse:
    sentiment: str
    alert_needed: bool
    explanation: str

class ChatMonitorClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.message_cache = []

    async def analyze_chats(self, username: str, chats: List[Chat]) -> Optional[SentimentResponse]:
        """
        Send chats for analysis and get sentiment response
        """
        try:
            payload = {
                "username": username,
                "chats": [{"sender": chat.sender, "message": chat.message} for chat in chats]
            }

            response = await self.client.post(
                f"{self.server_url}/analyze_chats",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return SentimentResponse(**data)
            else:
                print(f"Error: Server returned status code {response.status_code}")
                self.message_cache.append(payload)
                return None

        except httpx.RequestError as e:
            print(f"Error sending chats: {e}")
            self.message_cache.append(payload)
            return None

    def display_results(self, results: Optional[SentimentResponse]) -> str:
        """
        Display analysis results in a user-friendly format
        """
        if not results:
            return "⚠️ Unable to analyze chats"

        alert_symbol = "🚨" if results.alert_needed else "✓"
        
        return f"""
{alert_symbol} Analysis Results:
Sentiment: {results.sentiment}
Alert Needed: {"Yes" if results.alert_needed else "No"}
Explanation: {results.explanation}
"""

    async def close(self):
        """
        Close the HTTP client
        """
        await self.client.aclose()

# test_client.py
async def test_chat_monitoring():
    client = ChatMonitorClient()
    try:
        # Test chat messages
        test_chats = [
            Chat(sender="John", message="Hey, how are you doing?"),
            Chat(sender="Alice", message="I'm not feeling great today"),
            Chat(sender="John", message="What's wrong?"),
            Chat(sender="Alice", message="Just feeling down")
        ]
        
        print("\nAnalyzing chat conversation...")
        results = await client.analyze_chats("alice_user", test_chats)
        print(client.display_results(results))
        
        # Test another conversation
        another_chats = [
            Chat(sender="Bob", message="Hi everyone!"),
            Chat(sender="Charlie", message="Hello Bob, welcome!")
        ]
        
        print("\nAnalyzing another conversation...")
        results = await client.analyze_chats("bob_user", another_chats)
        print(client.display_results(results))

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_chat_monitoring())

# monitor_gui.py (Optional GUI client)
import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
from queue import Queue

class ChatMonitorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chat Monitor")
        self.client = ChatMonitorClient()
        self.message_queue = Queue()
        self.setup_gui()

    def setup_gui(self):
        # Username frame
        username_frame = ttk.Frame(self.root, padding="5")
        username_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(username_frame, text="Username:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(username_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=5)

        # Chat input frame
        chat_frame = ttk.Frame(self.root, padding="5")
        chat_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(chat_frame, text="Sender:").grid(row=0, column=0)
        self.sender_entry = ttk.Entry(chat_frame, width=20)
        self.sender_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(chat_frame, text="Message:").grid(row=1, column=0)
        self.message_entry = ttk.Entry(chat_frame, width=40)
        self.message_entry.grid(row=1, column=1, padx=5)
        
        ttk.Button(chat_frame, text="Add Message", 
                  command=self.add_message).grid(row=2, column=0, columnspan=2)
        
        # Messages display
        self.messages_text = scrolledtext.ScrolledText(self.root, height=10, width=50)
        self.messages_text.grid(row=2, column=0, padx=5, pady=5)
        
        # Analysis results display
        self.results_text = scrolledtext.ScrolledText(self.root, height=5, width=50)
        self.results_text.grid(row=3, column=0, padx=5, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(self.root, padding="5")
        button_frame.grid(row=4, column=0)
        ttk.Button(button_frame, text="Analyze", 
                  command=self.analyze_messages).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Clear", 
                  command=self.clear_all).grid(row=0, column=1, padx=5)

        self.messages = []

    def add_message(self):
        sender = self.sender_entry.get().strip()
        message = self.message_entry.get().strip()
        
        if sender and message:
            chat = Chat(sender=sender, message=message)
            self.messages.append(chat)
            self.messages_text.insert(tk.END, 
                                   f"{sender}: {message}\n")
            self.sender_entry.delete(0, tk.END)
            self.message_entry.delete(0, tk.END)

    def analyze_messages(self):
        if not self.messages:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No messages to analyze")
            return

        username = self.username_entry.get().strip()
        if not username:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Please enter a username")
            return

        threading.Thread(target=self._run_analysis, 
                       args=(username, self.messages.copy()),
                       daemon=True).start()

    def _run_analysis(self, username, messages):
        async def analyze():
            results = await self.client.analyze_chats(username, messages)
            self.message_queue.put(results)

        asyncio.run(analyze())
        self.root.after(100, self._check_results)

    def _check_results(self):
        try:
            results = self.message_queue.get_nowait()
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, 
                                   self.client.display_results(results))
        except:
            self.root.after(100, self._check_results)

    def clear_all(self):
        self.messages = []
        self.messages_text.delete(1.0, tk.END)
        self.results_text.delete(1.0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.sender_entry.delete(0, tk.END)
        self.message_entry.delete(0, tk.END)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # # Run GUI client
    # gui = ChatMonitorGUI()
    # gui.run()
    
    # Or run test client
    asyncio.run(test_chat_monitoring())