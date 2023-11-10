from jinja2 import Template
import os
from constants import SAVE_DIR_VIDEO

from flask import Flask, render_template, send_from_directory, request

app = Flask(__name__)


@app.route('/')
def index():
    video_info = []

    for video in os.listdir(SAVE_DIR_VIDEO):
        if os.path.splitext(video)[1] not in [".mp4","mov",".webm"]:
            continue
        print(video)
        video_title = os.path.splitext(video)[0]
        video_info.append((video, video_title))
    print(video_info)
    return render_template('video_gallery.html', video_info=video_info)


@app.route('/videos/<path:filename>')
def serve_video(filename):
    video_folder = 'download/video'
    return send_from_directory(video_folder, filename)

@app.route("/watch_button_cicked", methods=["POST"])
def handle_watch_button():
    input_value = request.form.get('input_name')
    print(input_value)
    return "Action handled success"

@app.route("/like_button_clicked", methods=["POST"])
def handle_like_button():
    return "Action handled success"


@app.route("/not_interested_button_clicked", methods=["POST"])
def handle_not_interested_button():
    return "Action handled success"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5001",debug=True)
