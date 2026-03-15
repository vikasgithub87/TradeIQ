# TradeIQ

AI-powered intraday trading intelligence platform for NSE India.

## Proof of Concept

Runs sentiment analysis on NSE companies using live news + Claude API.

### Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Copy .env.example to .env and fill in your API keys:
   copy .env.example .env

3. Run the proof of concept:
   python poc_script.py

### Expected Output

For each of 3 companies (RELIANCE, INFY, HDFCBANK), you will see:
- Number of news articles found
- A 3-sentence analyst-quality trade brief
