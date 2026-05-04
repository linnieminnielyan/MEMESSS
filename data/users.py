import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String,
                                 index=True, unique=True, nullable=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    memes = orm.relationship("Meme", back_populates='user')

    def __repr__(self):
        return f'<User> {self.id} {self.username}'