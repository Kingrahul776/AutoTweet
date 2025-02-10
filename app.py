import os
import tweepy
import psycopg2
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file (useful for local development)
load_dotenv()

app = Flask(__name__)

# Load Twitter API credentials from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

# Debugging: Print environment variables to confirm they're loading
print("🔹 DEBUG: Checking API Keys")
print("API_KEY:", API_KEY)
print("API_SECRET:", API_SECRET)
print("ACCESS_TOKEN:", ACCESS_TOKEN)
print("ACCESS_SECRET:", ACCESS_SECRET)
print("DATABASE_URL:", DATABASE_URL)

# Check if API keys are missing
if not API_KEY or not API_SECRET or not ACCESS_TOKEN or not ACCESS_SECRET:
    raise ValueError("❌ ERROR: Missing Twitter API credentials! Check environment variables.")

# Twitter Authentication
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# PostgreSQL Database Connection
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connected to PostgreSQL Database")
except Exception as e:
    print("❌ ERROR: Could not connect to PostgreSQL!")
    print(str(e))
    conn = None

# Create table for scheduled tweets if not exists
if conn:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_tweets (
            id SERIAL PRIMARY KEY,
            tweet_text TEXT NOT NULL,
            scheduled_time TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()

@app.route('/')
def home():
    return "🚀 Twitter Bot API Running on Railway!"

# Route to Post a Tweet
@app.route('/tweet', methods=['POST'])
def post_tweet():
    data = request.json
    tweet_text = data.get("text", "")

    if not tweet_text:
        return jsonify({"error": "Tweet text is required"}), 400

    try:
        tweet = api.update_status(tweet_text)
        return jsonify({"message": "✅ Tweet posted successfully", "tweet_id": tweet.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to Schedule a Tweet (uses Celery)
@app.route('/schedule_tweet', methods=['POST'])
def schedule_tweet():
    data = request.json
    tweet_text = data.get("text", "")
    delay = data.get("delay", 10)  # Default delay is 10 seconds

    if not tweet_text:
        return jsonify({"error": "Tweet text is required"}), 400

    # Store in PostgreSQL
    if conn:
        cur.execute("INSERT INTO scheduled_tweets (tweet_text) VALUES (%s)", (tweet_text,))
        conn.commit()

    # Import Celery task dynamically to prevent circular import issues
    from tasks import schedule_tweet_task
    schedule_tweet_task.apply_async(args=[tweet_text], countdown=delay)

    return jsonify({"message": "⏳ Tweet scheduled", "delay": delay})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
