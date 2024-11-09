# client.py
import httpx
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
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
        logging.info(f"ChatMonitorClient initialized with server: {server_url}")

    async def analyze_chats(self, username: str, chats: List[Chat]) -> Optional[SentimentResponse]:
        """
        Send chats for analysis and get sentiment response
        """
        try:
            payload = {
                "username": username,
                "chats": [{"sender": chat.sender, "message": chat.message} for chat in chats]
            }

            logging.debug(f"Sending analysis request for {username} with {len(chats)} messages")
            response = await self.client.post(
                f"{self.server_url}/analyze_chats",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                logging.debug(f"Received analysis response: {data}")
                return SentimentResponse(**data)
            else:
                logging.error(f"Server error: {response.status_code}")
                self.message_cache.append(payload)
                return None

        except httpx.RequestError as e:
            logging.error(f"Request error: {e}")
            self.message_cache.append(payload)
            return None
        except Exception as e:
            logging.error(f"Unexpected error in analyze_chats: {e}")
            return None

    def display_results(self, results: Optional[SentimentResponse]) -> str:
        """
        Format analysis results for display
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
        try:
            await self.client.aclose()
            logging.info("ChatMonitorClient closed")
        except Exception as e:
            logging.error(f"Error closing client: {e}")

    async def retry_cached_messages(self):
        """
        Retry sending cached messages
        """
        if not self.message_cache:
            return

        logging.info(f"Attempting to send {len(self.message_cache)} cached messages")
        retry_cache = self.message_cache.copy()
        self.message_cache.clear()

        for payload in retry_cache:
            try:
                response = await self.client.post(
                    f"{self.server_url}/analyze_chats",
                    json=payload
                )
                if response.status_code != 200:
                    self.message_cache.append(payload)
            except Exception as e:
                self.message_cache.append(payload)
                logging.error(f"Error retrying cached message: {e}")