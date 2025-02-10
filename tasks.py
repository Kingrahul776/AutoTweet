import os
import tweepy
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twitter API Setup
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Railway Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery Configuration
celery = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

@celery.task
def schedule_tweet_task(tweet_text):
    """Schedules a tweet using Celery."""
    try:
        tweet = api.update_status(tweet_text)
        return {"message": "Tweet posted", "tweet_id": tweet.id}
    except Exception as e:
        return {"error": str(e)}
