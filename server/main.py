from fastapi import FastAPI
from sentiment_analyzer import analyze_sentiment
from models import *

app = FastAPI()


@app.post("/analyze_chats", response_model=SentimentResponse)
async def analyze_chats(request: ChatAnalysisRequest):
    sentiment_response = analyze_sentiment(request.chats)

    return sentiment_response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
