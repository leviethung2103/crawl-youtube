# Video Recommendation

Tech stack: Python, SQL, Flask, Jinja2, HTML, CSS, Javascript

![Alt text](<images/CleanShot 2023-11-11 at 22.49.52.png>)

# Setup

Install the packages

```python
pip install -r requirements.txt
# Rename file `.env.example` to `.env`,
cp .env.example .env
```

Update the value of `API_KEY`. Refer to https://developers.google.com/youtube/v3

Enable the Youtube API v3 in your google account and get the `API_KEY`.

Add the secret key into .env

## Get channel ID
https://www.streamweasels.com/tools/youtube-channel-id-and-user-id-convertor/

## Development

```python
# run background task
python main.py
# run Flask app
python app.py
```

## Deployment 

PLease install node and npm before process this step. 
Install pm2 app in order to run the python apps as background services.

Install PM2 App
```
npm install pm2 -g
```

Activate anaconda environment
```
pm2 start main.py --name youtube-task
pm2 start web_app.py --name web-app

nohup jupyter-lab --no-browser --ip 0.0.0.0 --port=8888 &
# check the PID of process
lsof nohup.out
# find the process between all the running processes of the computer
ps au | grep jupyter
kill -9 <PID>
```

## Next features
- Share button
- Popup show off the transcript 

## To DO
- Refactor to MVC pattern

- Send to chatgpt to extract the description, update long description into database
- Split the long video into small chunks -> 
  video 20mins: auto split into different small sections 
- Summarize the sections 
- Show the descriptions button  


## Converting 
ffmpeg -i <input_path> -c:v h264_nvenc -c:a aac <output_path>


## Changelog 
10-12-2023:
- Add channel management
- Add podcast feature
- Get the chunks of 'Toàn cảnh' videos 
- Refactor code 
- Remove iframe, use Youtube Player instead
- Add Whisper transcribe

03-12-2023:
- Remove downloading youtube videos
- Use directly yoiutube url 
- Optimize loading page
- Play the video on Iphone
- Add share button

20-11-2023:
- Transcribe the audio
- Convert video -> audio
- Save the transcription into file 
- Save transcription into database

19-11-2023:
- Installed Underthesea for recommendation
- Fix bug convert video to mp4 
- Add recommend feature into video
- Add thumbnail for video
- Add feature download transcript if available
- Add VideoRating class for Recommendation 
- Add function download and transcribe the audio -> script
- Add delete feature for database

13-11-2023:
- Add login page - authentication
11-11-2023: 
- Fix thread database with flask by using the sqlachemy instead of sqlite 
- Manipulate the database easier than before