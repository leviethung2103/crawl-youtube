# Usage

Install the packages
```python
pip install -r requirements.txt
```

Rename file `.env.example` to `.env`, and then update the value of API_KEY

Run 
```python
python main.py
```

# Run the python as background task
Install node
```
npm install pm2 -g 
```

Activate anaconda environment

```
pm2 start main.py --name youtube-task
```