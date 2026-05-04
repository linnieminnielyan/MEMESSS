import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Meme(SqlAlchemyBase):
    __tablename__ = 'memes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    image_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    top_text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    bottom_text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text_color = sqlalchemy.Column(sqlalchemy.String, default='white')
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User', back_populates='memes')

    def __repr__(self):
        return f'<Meme> {self.id} {self.top_text}'