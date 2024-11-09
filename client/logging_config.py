# logging_config.py
import logging
import os
from datetime import datetime

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler with daily rotation
            logging.FileHandler(
                f'logs/chat_app_{datetime.now().strftime("%Y%m%d")}.log'
            ),
            # Console handler
            logging.StreamHandler()
        ]
    )

    # Set specific levels for different components
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)