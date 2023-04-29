import datetime

import aiomisc
from aiogram import types

from files.data.frames import Frame
from files.data.photos import Photo
from files.data.users import User
from files.data.videos import Video
from sqlalchemy import select, delete
from files.data.db_session import global_init, create_session

global_init('files/db/info.db')
db_sess = create_session()


@aiomisc.threaded
def insert_user_into_db(user: types.User):
    us = User()
    us.user_id = user.id
    db_sess.add(us)
    db_sess.commit()


async def insert_photo_into_db(path: str, lang: str, text: str, user: types.User):
    user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
    list_of_paths = list(db_sess.scalars(select(Photo.path).join(User).where(Photo.user_id == user_id)))
    list_of_user_ids = list(db_sess.scalars(select(User.user_id)))
    if user.id in list_of_user_ids:
        if path not in list_of_paths:
            photo = Photo()
            photo.saved_date = datetime.datetime.now()
            photo.lang_of_text = lang
            photo.path = path
            photo.text = text
            photo.user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
            db_sess.add(photo)
            db_sess.commit()
        else:
            photo = db_sess.scalar(select(Photo).join(User).where(Photo.user_id == user_id).where(Photo.path == path))
            photo.saved_date = datetime.datetime.now()
            db_sess.commit()
    else:
        await insert_user_into_db(user)
        await insert_photo_into_db(path, lang, text, user)


async def insert_video_into_db(path: str, lang: str, text: str, user: types.User):
    user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
    list_of_paths = list(db_sess.scalars(select(Video.path).join(User).where(Video.user_id == user_id)))
    list_of_user_ids = list(db_sess.scalars(select(User.user_id)))
    if user.id in list_of_user_ids:
        if path not in list_of_paths:
            video = Video()
            video.saved_date = datetime.datetime.now()
            video.lang_of_text = lang
            video.text = text
            video.path = path
            video.user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
            db_sess.add(video)
            db_sess.commit()
    else:
        await insert_user_into_db(user)
        await insert_video_into_db(path, lang, text, user)


async def insert_frame_into_db(path: str, hash: str, user: types.User):
    user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
    list_of_user_ids = list(db_sess.scalars(select(User.user_id)))
    if user.id in list_of_user_ids:
        frame = Frame()
        frame.path = path
        frame.hash = hash
        frame.user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
        db_sess.add(frame)
        db_sess.commit()
    else:
        await insert_user_into_db(user)
        await insert_frame_into_db(path, hash, user)


@aiomisc.threaded
def get_user_images_and_their_texts(user: types.User):
    user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
    photos_list = list(
        db_sess.scalars(
            select(Photo.path).join(User).where(Photo.user_id == user_id).order_by(Photo.saved_date)))
    texts_list = []
    for p in photos_list:
        texts_list.append(db_sess.scalar(select(Photo.text).where(Photo.path == p)))
    return photos_list, texts_list


@aiomisc.threaded
def get_user_videos_and_their_texts(user: types.User):
    user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
    videos_list = list(
        db_sess.scalars(select(Video.path).join(User).where(Video.user_id == user_id).order_by(Video.saved_date)))
    texts_list = []
    for v in videos_list:
        texts_list.append(db_sess.scalar(select(Video.text).where(Video.path == v)))
    return videos_list, texts_list


@aiomisc.threaded
def get_user_frames(user: types.User):
    user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
    frames_list = list(db_sess.scalars(select(Frame.path).join(User).where(Frame.user_id == user_id)))
    return frames_list


async def delete_all_user_frames_from_db(user: types.User):
    user_id = db_sess.scalar(select(User.id).where(User.user_id == user.id))
    user_frames = db_sess.scalars(select(Frame).join(User).where(Frame.user_id == user_id))
    for frame in user_frames:
        db_sess.delete(frame)


def get_frame_hash(path: str):
    frame_hash = db_sess.scalar(select(Frame.hash).where(Frame.path == path))
    return frame_hash
