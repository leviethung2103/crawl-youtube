import os
from constants import SAVE_DIR_VIDEO
from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for, session
from loguru import logger
from database import VideoDal
from dotenv import load_dotenv
from pprint import pprint
from VideoRating import VideoRatingPredictor
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

VIDEO_FOLDER = 'download/video'
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

video_dal = VideoDal(os.getenv("DATABASE"))
rating_predictor = VideoRatingPredictor(
    csv_path=None, database=os.getenv("DATABASE"))


@app.route("/info")
def info():
    return render_template('info.html')


@app.route("/train_model")
def train_recommender():
    rating_predictor.train_model()
    return "Trained recommender"


@app.route("/about")
def about():
    return redirect(url_for("login"))


@app.route('/')
def index():
    # check if user is already loggin in
    if 'username' in session:
        return redirect(url_for('video_rec'))

    return redirect(url_for('info'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if 'username' in session:
        return redirect(url_for('video_rec'))

    if request.method == 'POST':
        form_data = request.form
        if bool(form_data):
            if request.form['username'] != USERNAME or request.form['password'] != PASSWORD:
                error = 'Invalid Credentials. Please try again.'
                logger.debug("Wrong username and password")
            else:
                logger.debug("Login successfully")
                # Store the username in ession to indicate user is loggin in
                session['username'] = request.form['username']
                return redirect(url_for('video_rec'))
        else:
            print("Form data is empty")
    # return login page
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
def logout():
    if request.method == 'GET':
        session.pop('username', None)

        logger.debug("Logged out successfully")

        return redirect(url_for('info'))


@app.route('/video-rec-debug')
def video_rec_debug():
    if 'username' not in session:
        return redirect(url_for('login'))
    video_infos = []
    process_data = []

    for video in os.listdir(SAVE_DIR_VIDEO):
        if os.path.splitext(video)[1] not in [".mp4", "mov", ".webm", ".mkv"]:
            continue
        video_id = os.path.splitext(video)[0]
        video_info_res = video_dal.get_info(video_id).first()
        if video_info_res is not None:
            video_title = video_info_res.title
            video_desc = video_info_res.description
            predicted_rating = rating_predictor.predict_ratings(video_desc)
            thumbnail = video_info_res.medium_thumbnail
            publish_time = video_info_res.publish_time
            process_data.append(
                {"video_path": video, "video_id": video_id, "video_title": video_title,
                 "thumbnail": thumbnail, "publish_time": publish_time,
                 "rating": predicted_rating})
        else:
            logger.error(f"Video Id was not found: {video_id}")

    # sort recommend by rating and time
    sorted_process_data = sorted(
        process_data, key=lambda x: (-x['rating'], x['publish_time']))

    video_infos = [(item["video_path"], item["video_title"], item[
        "rating"], item["thumbnail"]) for item in sorted_process_data]

    return render_template('video_gallery_debug.html', video_info=video_infos)


@app.route('/video-rec')
def video_rec():
    if 'username' not in session:
        return redirect(url_for('login'))
    video_info = []

    for video in os.listdir(SAVE_DIR_VIDEO):
        if os.path.splitext(video)[1] not in [".mp4", "mov", ".webm", ".mkv"]:
            continue
        video_id = os.path.splitext(video)[0]
        video_info_res = video_dal.get_info(video_id).first()
        if video_info_res is not None:
            video_title = video_info_res.title
            video_desc = video_info_res.description
            predicted_rating = rating_predictor.predict_ratings(video_desc)
            thumbnail = video_info_res.medium_thumbnail
            video_info.append(
                (video, video_title, predicted_rating, thumbnail))
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
    video_dal.update(video_id=video_id, data={"likes": 1})

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

    video_dal.update(video_id=video_id, data={"no_interest": 1})

    return {
        "status": "success",
        "message": "Not interested button action handled",
        "video_name": video_name
    }


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5001", debug=True, threaded=True)
