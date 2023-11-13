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
pm2 start app.py --name web-app
```

## To DO
- Refactor to MVC pattern

## Changelog 
13-11-2023:
- Add login page - authentication
11-11-2023: 
- Fix thread database with flask by using the sqlachemy instead of sqlite 
- Manipulate the database easier than before