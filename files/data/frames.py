from files.data.db_session import SqlAlchemyBase
from sqlalchemy import Column, String, BigInteger, Integer, orm, ForeignKey


class Frame(SqlAlchemyBase):
    __tablename__ = 'frames'

    id = Column(Integer, autoincrement=True, primary_key=True)
    path = Column(String, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    hash = Column(String, nullable=False)
    user = orm.relationship('User')
