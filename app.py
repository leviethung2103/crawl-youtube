from jinja2 import Template
import os
from constants import SAVE_DIR_VIDEO

from flask import Flask, render_template, send_from_directory

app = Flask(__name__)


@app.route('/')
def index():
    video_info = []

    for video in os.listdir(SAVE_DIR_VIDEO):
        print(video)
        video_title = os.path.splitext(video)[0]
        video_info.append((video, video_title))
    print(video_info)
    return render_template('video_gallery.html', video_info=video_info)


@app.route('/videos/<path:filename>')
def serve_video(filename):
    video_folder = 'download/video'
    return send_from_directory(video_folder, filename)


if __name__ == '__main__':
    app.run(debug=True)
