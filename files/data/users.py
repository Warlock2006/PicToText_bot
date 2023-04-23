from files.data.db_session import SqlAlchemyBase
from sqlalchemy import Column, BigInteger, Integer


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger)
