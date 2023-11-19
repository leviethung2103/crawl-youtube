from yt_dlp import YoutubeDL
import yt_dlp
import os
from unidecode import unidecode
from constants import SAVE_DIR_VIDEO, SAVE_DIR_AUDIO, SAVE_DIR_TRANSCRIPT
import ffmpeg
from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
from pprint import pprint
import re
import whisper


def rename_files_in_folder(folder_path):
    files = os.listdir(folder_path)

    for file_name in files:
        old_file_path = os.path.join(folder_path, file_name)
        new_file_name = unidecode(file_name)
        new_file_name = new_file_name.replace("|", "")
        new_file_name = "_".join(new_file_name.split())
        new_file_path = os.path.join(folder_path, new_file_name)
        os.rename(old_file_path, new_file_path)


def get_video_id(url) -> str:
    """ Get the video id from "https://www.youtube.com/watch?v=D75tKXyN8lg" -> D75tKXyN8lg"""
    youtube_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{10}[048AEIMQUYcgkosw])'
    match = re.search(youtube_id_pattern, url)
    return match.group(1) if match else None


def get_transcript(video_id: str) -> str:
    """
    Fetches and returns the transcript of a YouTube video with the given video ID.
    Returns an empty string if the transcript is not found.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except NoTranscriptFound:
        return ""


def download_transcript(urls=[]):
    # @TODO: Get the audio and using the Whisper to get the transcript
    if not os.path.exists(SAVE_DIR_TRANSCRIPT):
        os.makedirs(SAVE_DIR_TRANSCRIPT)

    data = []

    if len(urls) == 0:
        return data

    for url in urls:
        video_id = get_video_id(url)
        transcript = get_transcript(video_id)
        data.append({'url': url, 'video_id': video_id,
                    'transcript': transcript})
    return data


def whisper_transcription(audio_file):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result['text']


def download_video(urls=[]):
    if not os.path.exists(SAVE_DIR_VIDEO):
        os.makedirs(SAVE_DIR_VIDEO)

    # bestvideo[ext=mp4]+bestaudio[ext=m4a]
    # 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best',

    ydl_opts = {
        'format': 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best',
        "socket_timeout": 60,
        'outtmpl': SAVE_DIR_VIDEO + '/%(id)s.%(ext)s',
    }

    result = {}

    with YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                ydl.download([url])
                logger.debug(f"Video: {url} downloaded successfully")
                result[url] = 1
            except Exception as e:
                logger.error(f"Error downloading video {url}: {str(e)}")
                result[url] = 0

    return result


def download_audio(urls=[]):
    if not os.path.exists(SAVE_DIR_AUDIO):
        os.makedirs(SAVE_DIR_AUDIO)

    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'outtmpl': SAVE_DIR_AUDIO + '/%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

    # rename all the filenames
    # rename_files_in_folder(SAVE_DIR_AUDIO)


def webm2mp4(input_file, output_file):
    """ Very slow convertion """
    try:
        input_options = {}
        output_options = {
            'c:v': 'libx264',
            'strict': 'experimental',
        }

        # Convert WebM to MP4
        ffmpeg.input(input_file, **input_options).output(output_file,
                                                         **output_options).run(overwrite_output=True)
    except Exception as error:
        print(f"Error: {str(error)}")


def convert_webm_mp4(input_paths):
    """ Default resolution 640x480 """
    for input_path in input_paths:
        if os.path.splitext(input_path)[1].lower() == ".webm":
            print("Converting {} to mp4...".format(input_path))
            output_file = os.path.splitext(input_path)[0] + '.mp4'
            stream = ffmpeg.input(input_path).output(
                output_file, vcodec="h264_nvenc", acodec="aac", vf='scale=640:480').overwrite_output()

            ffmpeg.run(stream)
        else:
            print("Invalid input file. Only webm files are supported.")
