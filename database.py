import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger


Base = declarative_base()


class Video(Base):
    __tablename__ = 'videos'
    video_id = Column("video_id", Integer, primary_key=True)
    video_url = Column("video_url", String)
    title = Column("title", String)
    description = Column("description", String)
    is_download = Column("is_download", Integer)
    publish_time = Column("publish_time", String)
    likes = Column("likes", Integer)
    no_interest = Column("no_interest", Integer)
    is_watch = Column("is_watch", Integer)
    rating = Column("rating", Integer)

    def __init__(self, video_id, video_url="", title="", description="", is_download=0, publish_time="", likes=0, no_interest=0, is_watch=0, rating=0):
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

    def __repr__(self):
        """ used for debug, to print all the properties of this class """
        return f"({self.video_id} {self.video_url} {self.title} {self.description})"


class VideoDal:
    def __init__(self, database) -> None:
        engine = create_engine(f"sqlite:///{database}", echo=False)
        # Base.meta.create_all(bind=engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()

    def get_downloaded_flag(self, video_id):
        """" Return tupple of __repr__ or None """
        return self.session.query(Video).filter(Video.is_download == True, Video.video_id == video_id)

    def get_info(self, video_id):
        return self.session.query(Video).filter(Video.video_id == video_id)

    def insert(self, video_id, video_url="", title="", description="", is_download=0, publish_time="", likes=0, no_interest=0, is_watch=0, rating=0):
        video = Video(video_id, video_url, title, description, is_download,
                      publish_time, likes, no_interest, is_watch, rating)
        self.session.add(video)
        self.session.commit()
        logger.info(f"Inserted {video_id}")
    
    def update(self,video_id, data: dict):
        """ data (dict): {"video_id": "new_video_id"} """
        self.session.query(Video).filter(Video.video_id == video_id).update(data)
        self.session.commit()
        logger.info(f"Updated {video_id}")

    def get_all(self):
        return self.session.query(Video).all()

if __name__ == "__main__":
    # Usage example
    from dotenv import load_dotenv
    load_dotenv()

    DATABASE = os.getenv("DATABASE")

    database = VideoDal(DATABASE)
    result = database.get_info("1pYZmoriYOo").first()
    print(result)
