import sqlite3
import os

class VideoDatabse:
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
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
                        is_download INTEGER
                    )''')
        except Exception as e:
            print(f"Error: {str(e)}")

        self.connection.commit()
        self.disconnect()

    def insert_video_info(self, video_id, video_url, title, description, is_download):
        self.connect()
        cursor = self.connection.cursor()

        cursor.execute('''INSERT OR REPLACE INTO videos
                          (video_id, video_url, title, description, is_download)
                          VALUES (?, ?, ?, ?, ?)''',
                       (video_id, video_url, title, description, is_download))
        
        self.connection.commit()
        self.disconnect()

    def get_downloaded_flag(self, video_id):
        self.connect()
        cursor = self.connection.cursor()

        cursor.execute("SELECT is_download FROM videos WHERE video_id = ?", (video_id,))
        result = cursor.fetchone()

        self.disconnect()

        if result:
            return result[0]
        else:
            return None

if __name__ == "__main__":
    # Usage example
    database = VideoDatabse()
    # database.create_video_info_table()
    # database.insert_video_info("abc1234", "https://www.youtube.com/watch?v=abc123", "Video Title", "Video Description", 1)
    # downloaded_flag = database.get_downloaded_flag("abc1234")
    # if downloaded_flag is not None:
    #     print(f"Downloaded Flag for video 'abc123': {downloaded_flag}")
    # else:
    #     print("Video not found in the database.")

    # print(database.table_exists())
    # print(database.database_exists())