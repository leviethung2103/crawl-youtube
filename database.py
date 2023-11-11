import sqlite3
import os


class VideoDatabase:
    def __init__(self, database) -> None:
        self.connection = None
        self.database = database
        if not self.database_exists():
            self.create_video_info_table()

    def connect(self):
        self.connection = sqlite3.connect(self.database)

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def table_exists(self):
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        result = cursor.fetchone()
        self.disconnect()

        return result is not None

    def database_exists(self):
        return os.path.exists(self.database)

    def create_video_info_table(self):
        self.connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
                        video_id TEXT PRIMARY KEY,
                        video_url TEXT,
                        title TEXT,
                        description TEXT,
                        is_download INTEGER,
                        publish_time TEXT,
                        likes INTEGER,
                        no_interest INTEGER,
                        is_watch INTEGER,
                        rating INTEGER
                    )''')
        except Exception as e:
            print(f"Error: {str(e)}")

        self.connection.commit()
        self.disconnect()

    def insert_video_info(self, video_id, video_url, title, description, is_download, publish_time, likes=0, no_interest=0, is_watch=0, rating=0):
        self.connect()
        cursor = self.connection.cursor()

        cursor.execute('''INSERT OR REPLACE INTO videos
                          (video_id, video_url, title, description, is_download, publish_time, likes, no_interest, is_watch, rating)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (video_id, video_url, title, description, is_download, publish_time, likes, no_interest, is_watch, rating))

        self.connection.commit()
        self.disconnect()

    def update_video_info(self, video_id, data={}):
        self.connect()
        cursor = self.connection.cursor()

        likes = data.get("likes")
        no_interest = data.get("no_interest")
        is_watch = data.get("is_watch")
        rating = data.get('rating')

        if likes:
            query = f"UPDATE videos SET likes='{likes}' WHERE video_id = '{video_id}'"
            cursor.execute(query)

        if no_interest:
            query = f"UPDATE videos SET no_interest='{no_interest}' WHERE video_id = '{video_id}'"
            cursor.execute(query)

        if is_watch:
            query = f"UPDATE videos SET is_watch='{is_watch}' WHERE video_id = '{video_id}'"
            cursor.execute(query)

        if rating:
            query = f"UPDATE videos SET rating='{rating}' WHERE video_id = '{video_id}'"
            cursor.execute(query)

        self.connection.commit()
        self.disconnect()

    def get_downloaded_flag(self, video_id):
        self.connect()
        cursor = self.connection.cursor()

        cursor.execute(
            "SELECT is_download FROM videos WHERE video_id = ?", (video_id,))
        result = cursor.fetchone()

        self.disconnect()

        if result:
            return result[0]
        else:
            return None

    def get_video_info(self, video_id):
        """ Get the video id based on the video name """
        video_data = {}

        self.connect()
        cursor = self.connection.cursor()

        query = f"SELECT * FROM videos WHERE video_id = '{video_id}'"
        cursor.execute(query)

        result = cursor.fetchone()

        if result:
            keys = ['video_id', 'video_url', 'title', 'description',
                    'is_download', 'publish_time', 'likes', 'no_interest', 'is_watch', 'rating']
            video_data = dict(zip(keys, result))
        else:
            print("No result found")

        self.disconnect()
        return video_data


if __name__ == "__main__":
    # Usage example
    from dotenv import load_dotenv
    load_dotenv()

    DATABASE = os.getenv("DATABASE")

    print(DATABASE)
    print(type(DATABASE))

    database = VideoDatabase(DATABASE)
    # database.create_video_info_table()
    # database.insert_video_info("abc1234", "https://www.youtube.com/watch?v=abc123", "Video Title", "Video Description", 1)
    # downloaded_flag = database.get_downloaded_flag("abc1234")
    # if downloaded_flag is not None:
    #     print(f"Downloaded Flag for video 'abc123': {downloaded_flag}")
    # else:
    #     print("Video not found in the database.")

    # print(database.table_exists())
    # print(database.database_exists())

    # likes = 1
    # is_watch = 2
    # no_interest = 5
    # database.update_video_info("1pYZmoriYOo", likes, no_interest, is_watch)

    print(database.get_video_info("1pYZmoriYOo"))
