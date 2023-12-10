import os
import googleapiclient.discovery
from pprint import pprint
import schedule
from datetime import datetime, timedelta
import time
from Youtube import download_audio, download_video, download_transcript, convert_webm_mp4
from dotenv import load_dotenv
import os
from podcast_database import PodcastDal
from constants import SAVE_DIR_AUDIO, SAVE_DIR_VIDEO, FINAL_SAVE_DIR
from loguru import logger
from Youtube import get_transcript
import requests
from bs4 import BeautifulSoup

# Load the .env file
load_dotenv()


DATABASE = os.getenv("PODCAST_DATABASE")
podcast_dal = PodcastDal(DATABASE)

URLS = ["https://vnexpress.net/podcast/tien-lam-gi",
        "https://vnexpress.net/podcast/tai-chinh-ca-nhan"]

if not os.path.exists(FINAL_SAVE_DIR):
    os.path.exists(FINAL_SAVE_DIR)


def crawl_audio(url):
    try:
        with requests.get(url) as response:
            if response.status_code != 200:
                return ""
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            player_div = soup.find('div', class_='player-popcast-v2')
            if player_div:
                audio_tag = player_div.find('audio')
                if audio_tag and 'src' in audio_tag.attrs:
                    mp3_player_link = audio_tag['src']
            return mp3_player_link

    except requests.RequestException as e:
        print(f"An error occurred while making the request: {e}")

    return ""


def crawl_podcast(url):

    # Send a GET request to the URL
    response = requests.get(url)
    category = url.split("/")[-1]

    data = []
    if response.status_code == 200:
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        podcasts = soup.find_all('article', class_='item-news')
        print("Number of podcasts:", len(podcasts))
        for podcast in podcasts:
            link = podcast.find('a', href=True)
            if link:
                href = link['href']
                print("Link:", href)

                title = podcast.find('h2', class_='title-news')
                if title:
                    title_text = title.text.strip()
                    print("Title:", title_text)

                description = podcast.find('p', class_='description').a
                if description:
                    description_text = description.text.strip()
                    print("Description:", description_text)

                if title and description:
                    mp3_player_link = crawl_audio(href)
                    print("Mp3 Link: ", mp3_player_link)
                data.append((mp3_player_link, title_text, description_text,
                            category))

    else:
        print(
            f"Failed to retrieve content. Status code: {response.status_code}")
    return data


def get_latest_podcast():
    print("Fetching latest podcast ")
    yesterday = (datetime.now() - timedelta(days=1)
                 ).strftime('%Y-%m-%d') + "T00:00:00Z"

    for url in URLS:
        print("url", url)
        responses = crawl_podcast(url)

        for response in responses:
            podcast_url = response[0]
            is_exist = podcast_dal.get_info(podcast_url).first()
            if is_exist is None:
                podcast_dal.insert(
                    podcast_url=response[0], title=response[1], description=response[2], category=response[3])
            else:
                logger.debug(f"Podcast: {podcast_url} already in database")


# Schedule the task to run every day at 7:00 AM
# schedule.every().day.at("07:00").do(get_latest_podcast)
# schedule.every(60).seconds.do(get_latest_video)


# get_channel_statistics()
# response = get_latest_video()
# while True:
#     schedule.run_pending()
#     time.sleep(1)
get_latest_podcast()
