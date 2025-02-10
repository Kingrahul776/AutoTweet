import os
import tweepy
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from tasks import schedule_tweet_task
import psycopg2

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Twitter API Authentication
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# PostgreSQL Database (Railway)
DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create table for scheduled tweets if not exists
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
    return "Twitter Bot API Running on Railway!"

# Route to Post a Tweet
@app.route('/tweet', methods=['POST'])
def post_tweet():
    data = request.json
    tweet_text = data.get("text", "")

    if not tweet_text:
        return jsonify({"error": "Tweet text is required"}), 400

    try:
        tweet = api.update_status(tweet_text)
        return jsonify({"message": "Tweet posted successfully", "tweet_id": tweet.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to Schedule a Tweet
@app.route('/schedule_tweet', methods=['POST'])
def schedule_tweet():
    data = request.json
    tweet_text = data.get("text", "")
    delay = data.get("delay", 10)  # Default delay is 10 seconds

    if not tweet_text:
        return jsonify({"error": "Tweet text is required"}), 400

    # Store in PostgreSQL
    cur.execute("INSERT INTO scheduled_tweets (tweet_text) VALUES (%s)", (tweet_text,))
    conn.commit()

    # Schedule the tweet with Celery
    schedule_tweet_task.apply_async(args=[tweet_text], countdown=delay)

    return jsonify({"message": "Tweet scheduled", "delay": delay})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
