from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

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


# create an engine and session
engine = create_engine("sqlite:///video_info.db", echo=False)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

video1 = Video("11", "http://fajfls", "osfu32131")
video2 = Video("12", "http://fajfls", "osfu32131")

# session.add(video1)
# session.add(video2)
# session.commit()

# results = session.query(Video).all()
# print("result:", results)

results = session.query(Video).filter(Video.video_id == "11")
for result in results:
    print("result2:", result)

result = session.query(Video).filter(Video.video_id == "U0H_4he2nUY").first()
print(result)
print(type(results))

print("Result--")
data = {"is_download": 25}
session.query(Video).filter(Video.video_id == "VtJLG89xP4M").update(data)


result = session.query(Video).filter(Video.video_id == "VtJLG89xP4M")
print(result.first().is_download)