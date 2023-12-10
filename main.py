import os
import googleapiclient.discovery
from pprint import pprint
import schedule
from datetime import datetime
import time
from Youtube import download_audio, download_video, download_transcript, convert_webm_mp4
from dotenv import load_dotenv
import os
from database import VideoDal
from constants import SAVE_DIR_AUDIO, SAVE_DIR_VIDEO, FINAL_SAVE_DIR
from loguru import logger
from Youtube import get_transcript
import re
from googleapiclient.errors import HttpError
import re
import requests
from bs4 import BeautifulSoup
from datetime import timedelta

# Load the .env file
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
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
USE_API_DESCRIPTION = os.getenv("USE_API_DESCRIPTION")

# Database
video_dal = VideoDal(DATABASE)

if not os.path.exists(FINAL_SAVE_DIR):
    os.path.exists(FINAL_SAVE_DIR)


def get_thumbnaisl(item):
    high_thumbnail_url = item["snippet"]["thumbnails"]["high"]["url"]
    default_thumbnail_url = item["snippet"]["thumbnails"]["default"]["url"]
    medium_thumbnail_url = item["snippet"]["thumbnails"]["medium"]["url"]
    return high_thumbnail_url, medium_thumbnail_url, default_thumbnail_url


def get_channel_info():
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=GOOGLE_API_KEY)
    request = youtube.channels().list(part="snippet", id=CHANNEL_ID)
    response = request.execute()
    return response


def get_channel_statistics():
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=GOOGLE_API_KEY)
    request = youtube.channels().list(part="statistics", id=CHANNEL_ID)
    response = request.execute()
    return response


def create_video_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


class ChunkVideo:
    def __init__(self) -> None:
        self.youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=GOOGLE_API_KEY)

    def pipeline(self, video_url, video_id):
        data = []
        try:
            # Step 1: Get timestamp and content pairs
            timestamp_content_pairs = self.get_description_video(video_id, USE_API_DESCRIPTION)

            # Step 3: replace timestamp by video_link
            for idx, pair in enumerate(timestamp_content_pairs):
                start_timestamp, content = pair
                start_time_in_seconds = self.time_to_second(start_timestamp)

                if idx + 1 == len(timestamp_content_pairs):
                    end_time_in_seconds = start_time_in_seconds + 30
                else:
                    end_timestamp = timestamp_content_pairs[idx + 1][0]
                    end_time_in_seconds = self.time_to_second(end_timestamp)

                chunk_link = self.create_chunk_link_by_timestamp(video_url, start_time_in_seconds, end_time_in_seconds)
                data.append((chunk_link, content))
        except Exception as error:
            logger.error(f"Error: {str(error)}")
        return data

    @staticmethod
    def time_to_second(time_str):
        parts = time_str.split(":")
        # split into two parts
        # check number of parts
        # if the number of parts == 2 mm:ss => convet into integer
        # finally, return formula
        # if the number of parts == 2 mm:ss => convet into integer
        # else: raise ValueError

        if len(parts) == 2:  # mm:ss format
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:  # hh:mm:ss format
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError("Invalid time format. Supported formats are hh:mm:ss or mm:ss.")

    @staticmethod
    def create_chunk_link_by_timestamp(video_url, start_time_in_second, end_time_in_second):
        return video_url + f"?start={start_time_in_second}&end={end_time_in_second}"

    @staticmethod
    def get_real_content(string):
        """Only apply for VTV
        Return
        [('00:00', 'Tin chính'),
        ('00:52', 'Truy nã hai tội phạm bỏ trốn khỏi trại giam'),
        ('01:37', 'Bắt đối tượng lừa đầu tư bất động sản'),
        ('02:16', 'TP. Hồ Chí Minh: Miễn phí học phí cấp THCS')]
        """
        timestamps = string.split("----------")[0].split("\n")
        timestamp_pattern = re.compile(r"\d{2}:\d{2}(:\d{2})?")
        filtered_data = [item for item in timestamps if re.search(timestamp_pattern, item)]
        timestamp_content_pairs = [
            (re.search(timestamp_pattern, item).group(), item.split(maxsplit=1)[1]) for item in filtered_data
        ]
        return timestamp_content_pairs

    def get_description_video(self, video_id, use_api=False):
        desc = ""
        try:
            if not use_api:
                soup = BeautifulSoup(requests.get("https://www.youtube.com/watch?v=II8rrpXW0B0").content, "html.parser")
                pattern = re.compile('(?<=shortDescription":").*(?=","isCrawlable)')
                desc = pattern.findall(str(soup))[0].replace("\\n", "\n")
                desc = self.get_real_content(desc)
            else:
                request = self.youtube.videos().list(id=video_id, part="snippet")
                response = request.execute()
                for item in response["items"]:
                    desc = item["snippet"]["description"]
                    desc = self.get_real_content(desc)

        except HttpError as error:
            logger.error(f"Error: {error.content if error.content else str(error)}")
        return desc


def get_latest_video(channel_id=None):
    print("Fetching latest video ")
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, developerKey=GOOGLE_API_KEY)

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00Z"

    videos = {}

    # call class ChunkVideo
    chunk_video_obj = ChunkVideo()

    try:
        # Fetch the latest video published after yesterday
        request = youtube.search().list(
            q="",
            channelId=channel_id,
            maxResults=MAX_RESULT,
            order="date",
            publishedAfter=yesterday,
            type="video",
            part="snippet",
        )
        response = request.execute()

        print("Total number of results: ", response["pageInfo"]["totalResults"])

        # Parse the items
        for item in response["items"]:
            video_id = item["id"]["videoId"]
            video_url = create_video_url(video_id)
            title = item["snippet"]["title"]
            desc = item["snippet"]["description"]
            publish_time = item["snippet"]["publishedAt"]
            high_thumbnail, medium_thumbnail, default_thumbnail = get_thumbnaisl(item)

            if "toàn cảnh" in title.lower():
                chunks = chunk_video_obj.pipeline(video_url, video_id)
                for chunk_link, content in chunks:
                    video_id = chunk_link.split("https://www.youtube.com/watch?v=")[-1]
                    videos[video_id] = {
                        "title": content,
                        "desc": content,
                        "url": chunk_link,
                        "publish_time": publish_time,
                        "high_thumbnail": high_thumbnail,
                        "medium_thumbnail": medium_thumbnail,
                        "default_thumbnail": default_thumbnail,
                    }

            else:
                logger.debug(f"{video_url} {title} {desc} {publish_time}")

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
        logger.error(f"Error: {str(e)}")

    needed_download_links = []

    # ------------------ Handle download case & Insert into data ----------------- #
    for video_id, data in videos.items():
        is_download = video_dal.get_info(video_id).first()
        if is_download is None:
            download_flag = 0
            desc = data["desc"].replace('"', "")
            title = data["title"].replace('"', "")
            high_thumbnail = data["high_thumbnail"]
            medium_thumbnail = data["medium_thumbnail"]
            default_thumbnail = data["default_thumbnail"]
            video_dal.insert(
                video_id,
                data["url"],
                title,
                desc,
                download_flag,
                data["publish_time"],
                high_thumbnail=high_thumbnail,
                medium_thumbnail=medium_thumbnail,
                default_thumbnail=default_thumbnail,
            )
            needed_download_links.append(data["url"])
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
        downloaded_files = [os.path.join(VIDEO_FOLDER, file) for file in downloaded_files]
        # convert_webm_mp4(downloaded_files)
    if DOWNLOAD_AUDIO:
        logger.debug("Downloading audio ...")
        download_audio()
    if DOWNLOAD_TRANSCRIPT:
        logger.debug("Downloading transcript ...")
        data = download_transcript(needed_download_links)
        # insert the desc
        for item in data:
            video_dal.update(video_id=item["video_id"], data={"transcript": item["transcript"]})


if __name__ == "__main__":
    # Schedule the task to run every day at 7:00 AM
    schedule.every().day.at("07:00").do(get_latest_video, channel_id=CHANNEL_ID)
    # schedule.every(60).seconds.do(get_latest_video)

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    get_latest_video(channel_id=CHANNEL_ID)
