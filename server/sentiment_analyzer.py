from openai import OpenAI
import json
from typing import List
from dotenv import load_dotenv
from models import *
import os


def analyze_sentiment(chats: List[Chat]) -> SentimentResponse:

    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://nova-litellm-proxy.onrender.com"
    )

    chat_text = "\n".join([f"{chat.sender}: {chat.message}" for chat in chats])

    prompt = f"""Analyze the following chat messages and classify the overall sentiment as either NEGATIVE, CAUTIONARY, or POSITIVE.
    If the sentiment is NEGATIVE or CAUTIONARY, determine if an alert should be sent to a parent.
    Respond in JSON format with keys: sentiment, alert_needed, explanation. In the explanation include categories from the following if
    NEGATIVE catgeory occurs: Bullying, Profanity, Harassment, Teasing, Inappropriate, Sexual, Self Harm.

    Chat messages:
    {chat_text}
    """

    response = client.chat.completions.create(
        model="anthropic/claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": "You are an AI assistant that analyzes chat messages for sentiment and potential issues."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.choices[0].message.content
    parsed_result = json.loads(result)

    return SentimentResponse(**parsed_result)
