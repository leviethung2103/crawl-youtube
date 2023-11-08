import os
import googleapiclient.discovery
from pprint import pprint 
import schedule
from datetime import datetime, timedelta
import time 
from Youtube import download_audio, download_video
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

CHANNEL_ID = "UCabsTV34JwALXKGMqHpvUiA" # vtv24h
MAX_RESULT = 10

def get_channel_info():
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)
    request = youtube.channels().list(part="snippet", id=CHANNEL_ID)
    response = request.execute()

    pprint(response)

def get_channel_statistics():
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)
    request = youtube.channels().list(part="statistics", id=CHANNEL_ID)
    response = request.execute()

    pprint(response)

def create_video_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def get_latest_video():
    print("Fetching latest video ")
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') + "T00:00:00Z"

    video_links = []

    try:
        # Fetch the latest video published after yesterday
        request = youtube.search().list(
            q="",
            channelId=CHANNEL_ID,
            maxResults=MAX_RESULT,
            order="date",
            publishedAfter=yesterday,
            type="video",
            part="snippet"
        )
        response = request.execute()
    
        print("Total number of results: ", response['pageInfo']['totalResults'])
    
        # Parse the items
        for item in response['items']:
            video_url = create_video_url(item['id']['videoId'])
            title = item['snippet']['title']
            desc = item['snippet']['description']
            publish_time = item['snippet']['publishedAt']
            print(video_url, title, desc, publish_time)
            video_links.append(video_url)
            
    except Exception as e:
        print(f"Error: {str(e)}")

    print("Download videos")
    download_video(video_links)

# Schedule the task to run every day at 7:00 AM 
schedule.every().day.at("07:00").do(get_latest_video)
# schedule.every(60).seconds.do(get_latest_video)

# get_channel_statistics()
# response = get_latest_video()

while True:
    schedule.run_pending()
    time.sleep(1)