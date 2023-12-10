import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from sqlalchemy.engine import reflection
from datetime import datetime, timedelta

Base = declarative_base()


class Channel(Base):
    __tablename__ = "channels"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    channel_name = Column("channel_name", String)
    channel_id = Column("channel_id", String)
    created_at = Column("create_at", DateTime, default=lambda: datetime.utcnow() + timedelta(hours=7))
    status = Column("status", String)
    updated_at = Column("updated_at", DateTime, default=lambda: datetime.utcnow() + timedelta(hours=7))
    limit_num = Column("limit_num", Integer, default=50)
    daily_count = Column("daily_count", Integer, default=0)

    def __init__(self, channel_name, channel_id, status):
        self.channel_name = channel_name
        self.channel_id = channel_id
        self.status = status

    def __repr__(self):
        """used for debug, to print all the properties of this class"""
        return f"({self.channel_name} {self.channel_id} {self.created_at})"


class ChannelDal:
    def __init__(self, database, table_name="podcasts") -> None:
        engine = create_engine(f"sqlite:///{database}", echo=False)

        # Create an inspector object
        inspector = reflection.Inspector.from_engine(engine)
        # Check if the table exists
        table_exists = inspector.has_table(table_name)

        if table_exists:
            logger.debug("The table exists.")
        else:
            logger.debug("The table does not exist.")
            Base.metadata.create_all(bind=engine)

        session = sessionmaker(bind=engine)
        self.session = session()

    def get_info(self, channel_id):
        return self.session.query(Channel).filter(Channel.channel_id == channel_id).first()

    def insert(self, channel_name, channel_id, status="Healthy"):
        exists = self.session.query(Channel).filter((Channel.channel_id == channel_id)).first()
        if exists:
            logger.info(f"Channel {channel_name} or ID {channel_id} already exists.")
        else:
            channel = Channel(channel_name, channel_id, status)
            self.session.add(channel)
            self.session.commit()
            logger.info(f"Inserted {channel_name}")

    def update(self, channel_id, data: dict):
        """data (dict): {"channel_id": "new_channel_id"}"""
        self.session.query(Channel).filter(Channel.channel_id == channel_id).update(data)
        self.session.commit()
        logger.info(f"Updated {channel_id}")

    def get_all(self):
        return self.session.query(Channel).all()

    def delete(self, channel_id):
        channel_to_delete = self.session.query(Channel).filter(Channel.channel_id == channel_id).first()

        if channel_to_delete:
            # Delete the entry
            self.session.delete(channel_to_delete)
            self.session.commit()
            logger.info(f"Delete channel id {channel_id} succesfully")
        else:
            logger.info("Entry not found")


if __name__ == "__main__":
    # Usage example
    from dotenv import load_dotenv

    load_dotenv()

    DATABASE = os.getenv("DATABASE")

    database = ChannelDal(DATABASE)

    database.insert(channel_name="vtv24", channel_id="32312", status="Healthy")
    database.insert(channel_name="chanenlB", channel_id="33212312", status="Healthy")
    database.insert(channel_name="chanenlC", channel_id="33212312asdas", status="Healthy")
    print(database.get_info(channel_id="33212312asdas"))
    # database.delete(channel_id="33212312")

    print(database.get_all())
    for item in database.get_all():
        print(item.channel_id)
    # database.update(channel_id="33212312", data={"channel_name": "hung"})

    # result = database.get_info("1pYZmoriYOo").first()
    # print(result.publish_time)

    # print(database.parse_datetime(result.publish_time))
    # print(database.compare_date(result.publish_time))

    # database.delete("WTorthH4WHw")
