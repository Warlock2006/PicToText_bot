import datetime

from aiogram import types

from files.data.photos import Photo
from files.data.users import User
from files.data.videos import Video
from sqlalchemy import select, update, delete
from main import db_sess


def insert_user_into_db(user: types.User):
    us = User()
    us.user_id = user.id
    db_sess.add(us)
    db_sess.commit()


def insert_photo_into_db(path: str, lang: str, user: types.User):
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
        insert_user_into_db(user)
        insert_photo_into_db(path, lang, user)


def insert_video_into_db(path: str, lang: str, user: types.User):
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
        insert_user_into_db(user)
        insert_video_into_db(path, lang, user)
