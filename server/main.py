from fastapi import FastAPI
from sentiment_analyzer import analyze_sentiment
from alert_manager import send_alert_to_parent
from models import *

app = FastAPI()


@app.post("/analyze_chats", response_model=SentimentResponse)
async def analyze_chats(request: ChatAnalysisRequest):
    sentiment_response = analyze_sentiment(request.chats)

    # if sentiment_response.alert_needed:
    #     send_alert_to_parent(request.username, sentiment_response)

    return sentiment_response
