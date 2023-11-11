# Usage

Install the packages

```python
pip install -r requirements.txt
```

Rename file `.env.example` to `.env`, and then update the value of API_KEY

Run

```python
# run background task
python main.py
# run Flask app
python app.py
```

# Run the python as background task

Install node

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
11-11-2023: 
- Fix thread database with flask by using the sqlachemy instead of sqlite 
- Manipulate the database easier than before