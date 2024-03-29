import logging
from datetime import datetime

import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from lateness.core.config import Database as Database_

log = logging.getLogger(__name__)


class Lateness(declarative_base()):  # type: ignore
    __tablename__ = "lateness_log"

    id = db.Column(db.Integer, primary_key=True)
    upn = db.Column(db.String)
    reason = db.Column(db.String)
    timestamp = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Database:
    def __init__(self, config: Database_) -> None:
        if config.engine == "postgres":
            engine_string = f"{config.username}:{config.password}@{config.host}:{config.port}/{config.name}"
            self.engine = db.create_engine("postgresql+psycopg2://" + engine_string)
        elif config.engine == "sqlite":
            self.engine = db.create_engine(
                "sqlite:///" + config.name + ".db?check_same_thread=false"
            )
        else:
            raise Exception(f"{config.engine} setup has not been defined")

        log.info(f"{config.engine} loaded")

        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.Base = declarative_base()

        class Lateness(self.Base):  # type: ignore
            __tablename__ = "lateness_log"

            id = db.Column(db.Integer, primary_key=True)
            upn = db.Column(db.String)
            reason = db.Column(db.String)
            timestamp = db.Column(
                db.DateTime, default=datetime.now, onupdate=datetime.now
            )

        self.Base.metadata.create_all(self.engine)  # type: ignore
        log.info("database tables loaded")

    def get_table_object(self, table_name: str):
        self.Base.metadata.reflect(self.engine)  # type: ignore
        return self.Base.metadata.tables.get(table_name)  # type: ignore

    def get_last_lateness(self, upn: str):
        table_object = self.get_table_object(table_name="lateness_log")
        return self.session.query(table_object).filter_by(upn=upn).first()

    def insert_lateness(self, upn: str, reason: str):
        new_entry = Lateness(upn=upn, reason=reason)
        self.session.add(new_entry)
        self.session.commit()
        log.info(f"Inserted into lateness_log. UPN: {upn}, Reason: {reason}")
