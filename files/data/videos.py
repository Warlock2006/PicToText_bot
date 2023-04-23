from files.data.db_session import SqlAlchemyBase
import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, Integer, orm, ForeignKey


class Video(SqlAlchemyBase):
    __tablename__ = 'videos'

    id = Column(Integer, autoincrement=True, primary_key=True)
    path = Column(String, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    saved_date = Column(DateTime, default=datetime.datetime.now())
    lang_of_text = Column(String, default='eng')
    user = orm.relationship('User')
