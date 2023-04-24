import datetime

import aiomisc
from aiogram import types

from files.data.photos import Photo
from files.data.users import User
from files.data.videos import Video
from sqlalchemy import select, update, delete
from files.data.db_session import global_init, create_session

global_init('files/db/info.db')
db_sess = create_session()


@aiomisc.threaded
def insert_user_into_db(user: types.User):
    us = User()
    us.user_id = user.id
    db_sess.add(us)
    db_sess.commit()


async def insert_photo_into_db(path: str, lang: str, user: types.User):
    list_of_paths = list(db_sess.scalars(select(Photo.path).where(Photo.user_id == user.id)))
    list_of_user_ids = list(db_sess.scalars(select(User.user_id)))
    if user.id in list_of_user_ids:
        if path not in list_of_paths:
            photo = Photo()
            photo.saved_date = datetime.datetime.now()
            photo.lang_of_text = lang
            photo.path = path
            photo.user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
            db_sess.add(photo)
            db_sess.commit()
    else:
        await insert_user_into_db(user)
        await insert_photo_into_db(path, lang, user)


async def insert_video_into_db(path: str, lang: str, user: types.User):
    list_of_paths = list(db_sess.scalars(select(Video.path).where(Video.user_id == user.id)))
    list_of_user_ids = list(db_sess.scalars(select(User.user_id)))
    if user.id in list_of_user_ids:
        if path not in list_of_paths:
            video = Video()
            video.saved_date = datetime.datetime.now()
            video.lang_of_text = lang
            video.path = path
            video.user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
            db_sess.add(video)
            db_sess.commit()
    else:
        await insert_user_into_db(user)
        await insert_video_into_db(path, lang, user)
