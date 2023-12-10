import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from sqlalchemy.engine import reflection
from datetime import datetime, timedelta

Base = declarative_base()


class Podcast(Base):
    __tablename__ = 'podcasts'
    podcast_url = Column("url", String, primary_key=True)
    title = Column("title", String)
    description = Column("description", String)
    is_download = Column("is_download", Integer)
    is_watch = Column("is_watch", Integer)
    category = Column("category", String)

    def __init__(self, podcast_url, title="", description="", is_download=0, is_watch=0, category=""):
        self.podcast_url = podcast_url
        self.title = title
        self.description = description
        self.is_download = is_download
        self.is_watch = is_watch
        self.category = category

    def __repr__(self):
        """ used for debug, to print all the properties of this class """
        return f"({self.podcast_url} {self.title} {self.description})"


class PodcastDal:
    def __init__(self, database, table_name="podcasts") -> None:
        engine = create_engine(f"sqlite:///{database}", echo=False)

        # Create an inspector object
        inspector = reflection.Inspector.from_engine(engine)
        # Check if the table exists
        table_exists = inspector.has_table(table_name)

        if table_exists:
            print("The table exists.")
        else:
            print("The table does not exist.")
            Base.metadata.create_all(bind=engine)

        session = sessionmaker(bind=engine)
        self.session = session()

    def get_unwatched_podcast(self):
        return self.session.query(Podcast).filter(Podcast.is_watch == False).all()

    def get_downloaded_flag(self, podcast_url):
        """" Return tupple of __repr__ or None """
        return self.session.query(Podcast).filter(Podcast.is_download == True, Podcast.podcast_url == podcast_url)

    def get_info(self, podcast_url):
        return self.session.query(Podcast).filter(Podcast.podcast_url == podcast_url)

    def insert(self, podcast_url, title="", description="", is_download=0, category=""):
        podcast = Podcast(podcast_url, title, description,
                          is_download, category=category)
        self.session.add(podcast)
        self.session.commit()
        logger.info(f"Inserted {podcast_url}")

    def update(self, podcast_url, data: dict):
        """ data (dict): {"podcast_url": "new_podcast_url"} """
        self.session.query(Podcast).filter(
            Podcast.podcast_url == podcast_url).update(data)
        self.session.commit()
        logger.info(f"Updated {podcast_url}")

    def delete(self, podcast_url):
        podcast_to_delete = self.session.query(Podcast).filter(
            Podcast.podcast_url == podcast_url).first()

        if podcast_to_delete:
            # Delete the entry
            self.session.delete(podcast_to_delete)
            self.session.commit()
        else:
            print("Entry not found")


if __name__ == "__main__":
    # Usage example
    from dotenv import load_dotenv
    load_dotenv()

    DATABASE = os.getenv("PODCAST_DATABASE")

    database = PodcastDal(DATABASE)

    database.insert(podcast_url="https://212321",
                    title='Title1', description="descritpion 1")

    # print(database.get_unwatched_video())

    # result = database.get_info("1pYZmoriYOo").first()
    # print(result.publish_time)

    # print(database.parse_datetime(result.publish_time))
    # print(database.compare_date(result.publish_time))

    # database.delete("WTorthH4WHw")
