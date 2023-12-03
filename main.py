import os
import googleapiclient.discovery
from pprint import pprint
import schedule
from datetime import datetime, timedelta
import time
from Youtube import download_audio, download_video, download_transcript, convert_webm_mp4
from dotenv import load_dotenv
import os
from database import VideoDal
from constants import SAVE_DIR_AUDIO, SAVE_DIR_VIDEO, FINAL_SAVE_DIR
from loguru import logger
from Youtube import get_transcript

# Load the .env file
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

CHANNEL_ID = "UCabsTV34JwALXKGMqHpvUiA"  # vtv24h

DATABASE = os.getenv("DATABASE")

DOWNLOAD_VIDEO = int(os.getenv("DOWNLOAD_VIDEO"))
DOWNLOAD_AUDIO = int(os.getenv("DOWNLOAD_AUDIO"))
DOWNLOAD_TRANSCRIPT = int(os.getenv("DOWNLOAD_TRANSCRIPT"))

MAX_RESULT = int(os.getenv("MAX_NUMBER_VIDEOS"))

VIDEO_FOLDER = os.getenv("VIDEO_FOLDER")
AUDIO_FOLDER = os.getenv("AUDIO_FOLDE")
TRANSCRIPT_FOLDER = os.getenv("TRANSCRIPT_FOLDER")

# Database
video_dal = VideoDal(DATABASE)

if not os.path.exists(FINAL_SAVE_DIR):
    os.path.exists(FINAL_SAVE_DIR)


def get_thumbnaisl(item):
    high_thumbnail_url = item['snippet']['thumbnails']['high']['url']
    default_thumbnail_url = item['snippet']['thumbnails']['default']['url']
    medium_thumbnail_url = item['snippet']['thumbnails']['medium']['url']
    return high_thumbnail_url, medium_thumbnail_url, default_thumbnail_url


def get_channel_info():
    youtube = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, developerKey=GOOGLE_API_KEY)
    request = youtube.channels().list(part="snippet", id=CHANNEL_ID)
    response = request.execute()
    return response


def get_channel_statistics():
    youtube = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, developerKey=GOOGLE_API_KEY)
    request = youtube.channels().list(part="statistics", id=CHANNEL_ID)
    response = request.execute()
    return response


def create_video_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def get_latest_video():
    print("Fetching latest video ")
    youtube = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, developerKey=GOOGLE_API_KEY)

    yesterday = (datetime.now() - timedelta(days=1)
                 ).strftime('%Y-%m-%d') + "T00:00:00Z"

    video_links = []

    videos = {}

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

        print("Total number of results: ",
              response['pageInfo']['totalResults'])

        # Parse the items
        for item in response['items']:
            video_id = item['id']['videoId']
            video_url = create_video_url(video_id)
            title = item['snippet']['title']
            desc = item['snippet']['description']
            publish_time = item['snippet']['publishedAt']
            high_thumbnail,  medium_thumbnail, default_thumbnail = get_thumbnaisl(
                item)

            logger.debug(f"{video_url} {title} {desc} {publish_time}")
            video_links.append(video_url)

            videos[video_id] = {
                "title": title,
                "desc": desc,
                "url": video_url,
                "publish_time": publish_time,
                "high_thumbnail": high_thumbnail,
                "medium_thumbnail": medium_thumbnail,
                "default_thumbnail": default_thumbnail,
            }

    except Exception as e:
        print(f"Error: {str(e)}")

    needed_download_links = []

    # ------------------ Handle download case & Insert into data ----------------- #
    for video_id, data in videos.items():
        is_download = video_dal.get_info(video_id).first()
        if is_download is None:
            download_flag = 0
            desc = data['desc'].replace('"', '')
            title = data['title'].replace('"', '')
            high_thumbnail = data['high_thumbnail']
            medium_thumbnail = data['medium_thumbnail']
            default_thumbnail = data['default_thumbnail']
            video_dal.insert(video_id, data['url'], title,
                             desc, download_flag, data['publish_time'],
                             high_thumbnail=high_thumbnail, medium_thumbnail=medium_thumbnail,
                             default_thumbnail=default_thumbnail)
            needed_download_links.append(data['url'])
        else:
            # needed_download_links.append(data['url'])
            logger.debug(f"Video: {video_id} already in database")

    # check download is successfull, update to database
    if DOWNLOAD_VIDEO:
        logger.debug("Downloading videos ...")
        download_result = download_video(needed_download_links)
        logger.debug(f"Download result: {download_result}")
        # convert video webm -> mp4
        downloaded_files = os.listdir(VIDEO_FOLDER)
        downloaded_files = [os.path.join(VIDEO_FOLDER, file)
                            for file in downloaded_files]
        # convert_webm_mp4(downloaded_files)
    if DOWNLOAD_AUDIO:
        logger.debug("Downloading audio ...")
        download_audio()
    if DOWNLOAD_TRANSCRIPT:
        logger.debug("Downloading transcript ...")
        data = download_transcript(needed_download_links)
        # insert the desc
        for item in data:
            video_dal.update(video_id=item['video_id'], data={
                             'transcript': item['transcript']})


# Schedule the task to run every day at 7:00 AM
schedule.every().day.at("12:00").do(get_latest_video)
# schedule.every(60).seconds.do(get_latest_video)


# get_channel_statistics()
# response = get_latest_video()
# while True:
#     schedule.run_pending()
#     time.sleep(1)
get_latest_video()
