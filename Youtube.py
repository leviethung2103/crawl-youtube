from yt_dlp import YoutubeDL
import yt_dlp
import os
from unidecode import unidecode
from constants import SAVE_DIR_VIDEO, SAVE_DIR_AUDIO, SAVE_DIR_TRANSCRIPT, WHISPER_MODEL
import ffmpeg
from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
from pprint import pprint
import re
import whisper
import time


def create_chunks(text: str, max_tokens_per_part: int, mode: str):
    """
    Splits the given text into chunks based on the specified mode and the maximum tokens per part.
    Returns a list of chunks.
    """

    if mode == "auto":
        token_count = len(text.split())
        if token_count <= max_tokens_per_part:
            return [text]

    words = text.split()
    chunks = []
    current_part = "I have a text that I would like to summarize. It consists of many parts and these parts are separated by '-----'. Please keep the original language of text. Here is the 1. part: ---- "
    current_token_count = 0
    for word in words:
        if current_token_count + 1 <= max_tokens_per_part:
            current_part += word + " "
            current_token_count += 1
        else:
            current_part += "-----\n\Please take note of this paragraph carefully and refrain from responding to it. Kindly wait for the next part. "
            chunks.append(current_part)
            current_part = f"Here is the {len(chunks)+1} part: ---- "
            current_token_count = 0
    if current_part:
        current_part += "-----\n\n. Summarize the content by section with timestamp, with following format: 'timestamp in MM:SS' Section 'number': 'short title' \n 'content'"
        chunks.append(current_part)

    return chunks


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
    if not os.path.exists(SAVE_DIR_TRANSCRIPT):
        os.makedirs(SAVE_DIR_TRANSCRIPT)

    data = []

    if len(urls) == 0:
        return data

    for url in urls:
        video_id = get_video_id(url)
        transcript = get_transcript(video_id)
        if len(transcript) == 0:
            transcript = whisper_transcribe(video_id)
        data.append({'url': url, 'video_id': video_id,
                    'transcript': transcript})
    return data


def whisper_transcribe(video_id, is_save=True):
    t1 = time.time()
    audio_path = os.path.join(SAVE_DIR_AUDIO, video_id + ".mp3")
    if os.path.exists(audio_path):
        print(f"Transcribing video_id: {video_id}...")

        language = "Vietnamese"
        model = whisper.load_model(WHISPER_MODEL)
        transcribe_options = dict(task="transcribe", language=language)
        result = model.transcribe(audio_path, **transcribe_options)
        if is_save:
            file_path = os.path.join(SAVE_DIR_TRANSCRIPT, f"{video_id}.txt")
            with open(file_path, "w", encoding='utf-8') as file:
                for segment in result['segments']:
                    start = round(float(segment['start']), 2)
                    text = segment['text']
                    file.write(f"{start}: {text}\n")
            print(
                f"Text saved successfully!. Processing time: {time.time()-t1}")
        return result['text']
    else:
        print(f"Cannot find the audio for video_id: {video_id}")
        return ""


def download_video(urls=[]):
    if not os.path.exists(SAVE_DIR_VIDEO):
        os.makedirs(SAVE_DIR_VIDEO)

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


def download_audio():
    AUDIO_CONVERT_FORMAT = {'ar': '16000', 'ac': '1'}
    if not os.path.exists(SAVE_DIR_AUDIO):
        os.makedirs(SAVE_DIR_AUDIO)
    video_files = os.listdir(SAVE_DIR_VIDEO)
    video_files = [os.path.join(SAVE_DIR_VIDEO, video_file)
                   for video_file in video_files]
    video_files = [video_file for video_file in video_files if os.path.splitext(video_file)[
        1] == ".webm"]
    print(video_files)
    for video_file in video_files:
        try:
            basename = os.path.basename(video_file)
            output_audio = os.path.join(
                SAVE_DIR_AUDIO, basename.replace(".webm", ".mp3"))
            ffmpeg.input(video_file).output(
                output_audio, **AUDIO_CONVERT_FORMAT).run(overwrite_output=True)
        except ffmpeg.Error as e:
            print(f'Error processing file: {video_file}')
            print(f"Error in audio extraction: {e}")
            print(f"\nDetail: {e.stderr}")


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


if __name__ == "__main__":
    whisper_transcribe("7oDtFJPpDI8")
