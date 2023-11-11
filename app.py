import os
from constants import SAVE_DIR_VIDEO
from flask import Flask, render_template, send_from_directory, request, jsonify
from loguru import logger
from database import VideoDal
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

VIDEO_FOLDER = 'download/video'

video_dal =VideoDal(os.getenv("DATABASE"))

@app.route('/')
def index():
    video_info = []

    for video in os.listdir(SAVE_DIR_VIDEO):
        if os.path.splitext(video)[1] not in [".mp4", "mov", ".webm", ".mkv"]:
            continue
        video_id = os.path.splitext(video)[0]
        video_info_res = video_dal.get_info(video_id).first()
        if video_info_res is not None:
            video_title = video_info_res.title
            video_info.append((video, video_title))
        else:
            logger.error(f"Video Id was not found: {video_id}")
    return render_template('video_gallery.html', video_info=video_info)


@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)


@app.route("/watch_clicked", methods=["POST"])
def handle_watch_button():
    json_data = request.get_json()
    video_name = json_data['video_name']
    rating = json_data['rating']
    video_id = os.path.splitext(video_name)[0]

    data = {"is_watch": 1, "rating": rating}

    # @TODO: Refactor where likes and no_interest to be opposite
    like_threshold = 4
    if rating >= like_threshold:
        data["likes"] = 1
    elif rating in [1, 2]:
        data["no_interest"] = 1    

    # Update video data based on rating
    video_dal.update(video_id=video_id, data=data)

    # Delete videos
    try:
        os.remove(os.path.join(VIDEO_FOLDER, video_name))
    except Exception as error:
        logger.critical(f"str{error}")

    return {
        "status": "success",
        "message": "Watch button action handled",
        "video_path": video_name
    }


@app.route("/like_clicked", methods=["POST"])
def handle_like_button():
    json_data = request.get_json()
    video_name = json_data['video_name']
    video_id = os.path.splitext(video_name)[0]
    video_dal.update(video_id=video_id, data = {"likes": 1})

    return {
        "status": "success",
        "message": "Like button action handled",
        "video_name": video_name
    }


@app.route("/no_interest_clicked", methods=["POST"])
def handle_no_interest():
    json_data = request.get_json()
    video_name = json_data['video_name']
    video_id = os.path.splitext(video_name)[0]

    # delete videos
    try:
        os.remove(os.path.join(VIDEO_FOLDER, video_name))
    except Exception as error:
        logger.critical(f"str{error}")

    video_dal.update(video_id=video_id, data = {"no_interest": 1})

    return {
        "status": "success",
        "message": "Not interested button action handled",
        "video_name": video_name
    }


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5001", debug=True, threaded=True)
