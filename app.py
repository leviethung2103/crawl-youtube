from jinja2 import Template
import os
from constants import SAVE_DIR_VIDEO
from flask import Flask, render_template, send_from_directory, request, jsonify
from loguru import logger
from database import VideoDatabase
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

VIDEO_FOLDER = 'download/video'

database = VideoDatabase(os.getenv("DATABASE"))


@app.route('/')
def index():
    video_info = []

    for video in os.listdir(SAVE_DIR_VIDEO):
        if os.path.splitext(video)[1] not in [".mp4", "mov", ".webm"]:
            continue
        logger.debug(video)
        video_id = os.path.splitext(video)[0]
        print(video_id, video)
        video_info_res = database.get_video_info(video_id)
        if video_info_res.get("title") is not None:
            video_title = video_info_res['title']
            video_info.append((video, video_title))
    logger.debug(video_info)
    return render_template('video_gallery.html', video_info=video_info)


@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)


@app.route("/watch_clicked", methods=["POST"])
def handle_watch_button():
    print('watch button clicked')
    json_data = request.get_json()
    video_name = json_data['video_name']
    video_id = os.path.splitext(video_name)[0]
    database.update_video_info(video_id=video_id, data={"is_watch": 1})

    return {
        "status": "success",
        "message": "Watch button action handled",
        "video_path": video_name
    }


@app.route("/like_clicked", methods=["POST"])
def handle_like_button():
    logger.debug('like button clicked')
    json_data = request.get_json()
    video_name = json_data['video_name']
    video_id = os.path.splitext(video_name)[0]
    database.update_video_info(video_id=video_id, data={"likes": 1})

    return {
        "status": "success",
        "message": "Like button action handled",
        "video_name": video_name
    }


@app.route("/no_interest_clicked", methods=["POST"])
def handle_no_interest():
    logger.debug('not interested button')
    json_data = request.get_json()
    video_name = json_data['video_name']
    video_id = os.path.splitext(video_name)[0]

    os.remove(os.path.join(VIDEO_FOLDER, video_name))

    database.update_video_info(video_id=video_id, data={"no_interest": 1})

    return {
        "status": "success",
        "message": "Not interested button action handled",
        "video_name": video_name
    }


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5001", debug=True)
