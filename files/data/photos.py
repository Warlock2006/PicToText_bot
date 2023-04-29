from files.data.db_session import SqlAlchemyBase
from sqlalchemy import Column, DateTime, String, BigInteger, Integer, orm, ForeignKey, Text
import datetime


class Photo(SqlAlchemyBase):
    __tablename__ = 'photos'

    id = Column(Integer, autoincrement=True, primary_key=True)
    path = Column(String, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    saved_date = Column(DateTime, default=datetime.datetime.now())
    text = Column(Text, nullable=False)
    lang_of_text = Column(String, default='eng')
    user = orm.relationship('User')
