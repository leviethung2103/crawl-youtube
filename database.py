import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from sqlalchemy.engine import reflection
from datetime import datetime, timedelta

Base = declarative_base()


class Video(Base):
    __tablename__ = "videos"
    video_id = Column("video_id", String, primary_key=True)
    video_url = Column("video_url", String)
    title = Column("title", String)
    description = Column("description", String)
    is_download = Column("is_download", Integer)
    publish_time = Column("publish_time", String)
    likes = Column("likes", Integer)
    no_interest = Column("no_interest", Integer)
    is_watch = Column("is_watch", Integer)
    rating = Column("rating", Integer)
    high_thumbnail = Column("high_thumbnail", String)
    medium_thumbnail = Column("medium_thumbnail", String)
    default_thumbnail = Column("default_thumbnail", String)
    transcript = Column("transcript", String)

    def __init__(
        self,
        video_id,
        video_url="",
        title="",
        description="",
        is_download=0,
        publish_time="",
        likes=0,
        no_interest=0,
        is_watch=0,
        rating=0,
        high_thumbnail="",
        medium_thumbnail="",
        default_thumbnail="",
        transcript="",
    ):
        self.video_id = video_id
        self.video_url = video_url
        self.title = title
        self.description = description
        self.is_download = is_download
        self.publish_time = publish_time
        self.likes = likes
        self.no_interest = no_interest
        self.is_watch = is_watch
        self.rating = rating
        self.high_thumbnail = high_thumbnail
        self.medium_thumbnail = medium_thumbnail
        self.default_thumbnail = default_thumbnail
        self.transcript = transcript

    def __repr__(self):
        """used for debug, to print all the properties of this class"""
        return f"({self.video_id} {self.video_url} {self.title} {self.description})"


class VideoDal:
    def __init__(self, database) -> None:
        engine = create_engine(f"sqlite:///{database}", echo=False)

        # Create an inspector object
        inspector = reflection.Inspector.from_engine(engine)
        # Check if the table exists
        table_exists = inspector.has_table("videos")

        if table_exists:
            print("The table exists.")
        else:
            print("The table does not exist.")
            Base.metadata.create_all(bind=engine)

        session = sessionmaker(bind=engine)
        self.session = session()

    def get_unwatched_video(self):
        return self.session.query(Video).filter(Video.is_watch == False).all()

    def get_downloaded_flag(self, video_id):
        """ " Return tupple of __repr__ or None"""
        return self.session.query(Video).filter(Video.is_download == True, Video.video_id == video_id)

    def get_info(self, video_id):
        return self.session.query(Video).filter(Video.video_id == video_id)

    def insert(
        self,
        video_id,
        video_url="",
        title="",
        description="",
        is_download=0,
        publish_time="",
        likes=0,
        no_interest=0,
        is_watch=0,
        rating=0,
        high_thumbnail="",
        medium_thumbnail="",
        default_thumbnail="",
    ):
        video = Video(
            video_id,
            video_url,
            title,
            description,
            is_download,
            publish_time,
            likes,
            no_interest,
            is_watch,
            rating,
            high_thumbnail,
            medium_thumbnail,
            default_thumbnail,
        )
        self.session.add(video)
        self.session.commit()
        logger.info(f"Inserted {video_id}")

    def update(self, video_id, data: dict):
        """data (dict): {"video_id": "new_video_id"}"""
        self.session.query(Video).filter(Video.video_id == video_id).update(data)
        self.session.commit()
        logger.info(f"Updated {video_id}")

    def update_by_url(self, video_url, data: dict):
        """Query by video_url"""
        self.session.query(Video).filter(Video.video_url == video_url).update(data)
        self.session.commit()
        logger.info(f"Updated {video_url}")

    def delete(self, video_id):
        video_to_delete = self.session.query(Video).filter(Video.video_id == video_id).first()

        if video_to_delete:
            # Delete the entry
            self.session.delete(video_to_delete)
            self.session.commit()
        else:
            print("Entry not found")

    @staticmethod
    def parse_datetime(publish_time):
        parsed_publish_time = datetime.strptime(publish_time, "%Y-%m-%dT%H:%M:%SZ")
        return parsed_publish_time

    def compare_date(self, publish_time):
        parsed_publish_time = self.parse_datetime(publish_time)
        current_date = datetime.now()

        if (current_date - parsed_publish_time).days > 3:
            return True
        return False

    def get_all(self):
        return self.session.query(Video).all()


if __name__ == "__main__":
    # Usage example
    from dotenv import load_dotenv

    load_dotenv()

    DATABASE = os.getenv("DATABASE")

    database = VideoDal(DATABASE)

    print(database.get_unwatched_video())

    # result = database.get_info("1pYZmoriYOo").first()
    # print(result.publish_time)

    # print(database.parse_datetime(result.publish_time))
    # print(database.compare_date(result.publish_time))

    # database.delete("WTorthH4WHw")
