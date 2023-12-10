import os
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session
from loguru import logger
from database import VideoDal
from dotenv import load_dotenv
from VideoRating import VideoRatingPredictor
from podcast_database import PodcastDal
from channel_database import ChannelDal
from flask_cors import CORS
from datetime import datetime
from main import get_latest_video


load_dotenv()

app = Flask(__name__)
CORS(app)

app.secret_key = os.getenv("SECRET_KEY")

VIDEO_FOLDER = "download/video"
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

video_dal = VideoDal(os.getenv("DATABASE"))
rating_predictor = VideoRatingPredictor(csv_path=None, database=os.getenv("DATABASE"))

podcast_dal = PodcastDal(os.getenv("PODCAST_DATABASE"))
channel_dal = ChannelDal(os.getenv("DATABASE"))


@app.route("/info")
def info():
    return render_template("info.html")


@app.route("/train_model")
def train_recommender():
    rating_predictor.train_model()
    return "Trained recommender"


@app.route("/about")
def about():
    return redirect(url_for("login"))


@app.route("/")
def index():
    # check if user is already loggin in
    if "username" in session:
        return redirect(url_for("video_rec"))

    return redirect(url_for("info"))


@app.route("/video-management")
def video_management():
    channels = channel_dal.get_all()
    return render_template("video_management.html", channels=channels)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if "username" in session:
        return redirect(url_for("video_rec"))

    if request.method == "POST":
        form_data = request.form
        if bool(form_data):
            if request.form["username"] != USERNAME or request.form["password"] != PASSWORD:
                error = "Invalid Credentials. Please try again."
                logger.debug("Wrong username and password")
            else:
                logger.debug("Login successfully")
                # Store the username in ession to indicate user is loggin in
                session["username"] = request.form["username"]
                return redirect(url_for("video_rec"))
        else:
            print("Form data is empty")
    # return login page
    return render_template("login.html", error=error)


@app.route("/logout", methods=["GET"])
def logout():
    if request.method == "GET":
        session.pop("username", None)

        logger.debug("Logged out successfully")

        return redirect(url_for("info"))


def parse_datetime(publish_time):
    parsed_publish_time = datetime.strptime(publish_time, "%Y-%m-%dT%H:%M:%SZ")
    return parsed_publish_time


@app.route("/add_video", methods=["POST"])
def add_video():
    """Video Management"""
    data = request.get_json()

    channel_name = data.get("channel_name")
    channel_id = data.get("channel_id")
    status = data.get("status")

    channel_dal.insert(channel_name=channel_name, channel_id=channel_id, status=status)

    logger.debug(f"Added new channel: {channel_name} {channel_id} {status}")

    return {"status": "success"}


@app.route("/video-rec")
def video_rec():
    if "username" not in session:
        return redirect(url_for("login"))
    video_infos = []
    process_data = []

    # query unwatched videos
    unwatched_videos = video_dal.get_unwatched_video()

    for video in unwatched_videos:
        video_id = video.video_id
        generate_url = f"https://www.youtube.com/embed/{video_id}"

        video_title = video.title
        # generate_url = generate_url.split("&end=")[0]
        # generate_url = generate_url.split("?start=")[0]

        video_desc = video.description
        predicted_rating = rating_predictor.predict_ratings(video_desc)
        thumbnail = video.medium_thumbnail
        publish_time = video.publish_time
        publish_time = parse_datetime(publish_time)

        process_data.append(
            {
                "video_path": generate_url,
                "video_id": video_id,
                "video_title": video_title,
                "thumbnail": thumbnail,
                "publish_time": publish_time,
                "rating": predicted_rating,
            }
        )

    # sort recommend by rating and time
    sorted_process_data = sorted(process_data, key=lambda x: (-x["rating"], x["publish_time"]))

    video_infos = [
        (item["video_path"], item["video_title"], item["rating"], item["thumbnail"]) for item in sorted_process_data
    ]

    video_infos = video_infos[0:10] 

    return render_template("video_gallery.html", video_info=video_infos, total_videos=len(unwatched_videos))


@app.route("/videos/<path:filename>")
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)


@app.route("/watch_clicked", methods=["POST"])
def handle_watch_button():
    json_data = request.get_json()
    video_name = json_data["video_name"]
    rating = json_data["rating"]
    video_id = video_name.split("/")[-1]
    print("video_id:", video_id)

    data = {"is_watch": 1, "rating": rating}

    # @TODO: Refactor where likes and no_interest to be opposite
    like_threshold = 4
    if rating >= like_threshold:
        data["likes"] = 1
    elif rating in [1, 2]:
        data["no_interest"] = 1

    # Update video data based on rating
    data_type = json_data.get("type")
    if data_type == "audio":
        data = {"is_watch": 1}
        podcast_dal.update(podcast_url=json_data["video_name"], data=data)
    else:
        # video_dal.update(video_id=video_id, data=data)
        # video_name -> embed url
        # not the video url
        logger.debug(json_data["video_name"])
        video_url = json_data["video_name"].replace("embed/", "watch?v=")
        video_dal.update_by_url(video_url=video_url, data=data)

    return {"status": "success", "message": "Watch button action handled", "video_path": video_name}


@app.route("/fetch_video", methods=["POST"])
def fetch_video():
    json_data = request.get_json()
    channel_id = json_data["channel_id"]
    get_latest_video(channel_id)
    return {"status": "success", "message": "Triggered fetching video"}


@app.route("/audio")
def get_audio():
    # query unwatched podcasts
    unwatched_podcasts = podcast_dal.get_unwatched_podcast()
    audio_files1 = []
    audio_files2 = []
    for podcast in unwatched_podcasts:
        if podcast.category == "tien-lam-gi":
            audio_files1.append(
                {
                    "title": podcast.title,
                    "description": podcast.description,
                    "url": podcast.podcast_url,
                    "category": "Tien Lam Gi",
                }
            )
        elif podcast.category == "tai-chinh-ca-nhan":
            audio_files2.append(
                {
                    "title": podcast.title,
                    "description": podcast.description,
                    "url": podcast.podcast_url,
                    "category": "Tai Chinh Ca Nha",
                }
            )

    return render_template("audio.html", audio_files1=audio_files1, audio_files2=audio_files2)


# @app.route("/like_clicked", methods=["POST"])
# def handle_like_button():
#     json_data = request.get_json()
#     video_name = json_data['video_name']
#     video_id = os.path.splitext(video_name)[0]
#     video_dal.update(video_id=video_id, data={"likes": 1})

#     return {
#         "status": "success",
#         "message": "Like button action handled",
#         "video_name": video_name
#     }


# @app.route("/no_interest_clicked", methods=["POST"])
# def handle_no_interest():
#     json_data = request.get_json()
#     video_name = json_data['video_name']
#     video_id = os.path.splitext(video_name)[0]

#     # delete videos
#     try:
#         os.remove(os.path.join(VIDEO_FOLDER, video_name))
#     except Exception as error:
#         logger.critical(f"str{error}")

#     video_dal.update(video_id=video_id, data={"no_interest": 1})

#     return {
#         "status": "success",
#         "message": "Not interested button action handled",
#         "video_name": video_name
#     }

# ---------------------------- USE FOR LOCAL VIDEO --------------------------- #
# @app.route('/video-rec-debug')
# def video_rec_debug():
#     if 'username' not in session:
#         return redirect(url_for('login'))
#     video_infos = []
#     process_data = []

#     for video in os.listdir(SAVE_DIR_VIDEO):
#         if os.path.splitext(video)[1] not in [".mp4", "mov", ".webm", ".mkv"]:
#             continue
#         video_id = os.path.splitext(video)[0]
#         video_info_res = video_dal.get_info(video_id).first()
#         if video_info_res is not None:
#             video_title = video_info_res.title
#             video_desc = video_info_res.description
#             predicted_rating = rating_predictor.predict_ratings(video_desc)
#             thumbnail = video_info_res.medium_thumbnail
#             publish_time = video_info_res.publish_time
#             process_data.append(
#                 {"video_path": video, "video_id": video_id, "video_title": video_title,
#                  "thumbnail": thumbnail, "publish_time": publish_time,
#                  "rating": predicted_rating})
#         else:
#             logger.error(f"Video Id was not found: {video_id}")

#     # sort recommend by rating and time
#     sorted_process_data = sorted(
#         process_data, key=lambda x: (-x['rating'], x['publish_time']))

#     video_infos = [(item["video_path"], item["video_title"], item[
#         "rating"], item["thumbnail"]) for item in sorted_process_data]

#     return render_template('video_gallery_debug.html', video_info=video_infos)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5001", debug=True, threaded=True)
