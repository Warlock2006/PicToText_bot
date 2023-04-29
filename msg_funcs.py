import os
from deep_translator import GoogleTranslator
import aiomisc
import imagehash
import numpy
import cv2
import pytesseract
from PIL import Image
from aiogram.types import Message, User
from aiogram import Bot
from db_using import insert_frame_into_db, get_frame_hash, get_user_frames, delete_all_user_frames_from_db


@aiomisc.threaded
def translate(text: str, lang_to_translate: str):
    translator = GoogleTranslator(source='auto', target=lang_to_translate)
    translated_text = translator.translate(text)
    return translated_text


async def download_doc(message: Message, bot: Bot):
    file_info = await bot.get_file(message.document.file_id)
    file_path = file_info.file_path
    await bot.download_file(file_path, destination_dir='files')
    return file_path


async def download_photo(message: Message, bot: Bot):
    file_info = await bot.get_file(message.photo[-1].file_id)
    file_path = file_info.file_path
    await bot.download_file(file_path, destination_dir='files')
    return file_path


async def download_video(message: Message, bot: Bot):
    file_info = await bot.get_file(message.video.file_id)
    file_path = file_info.file_path
    await bot.download_file(file_path, destination_dir='files')
    return file_path


@aiomisc.threaded
def ocr(path: str, lang: str):
    img = Image.open(path)
    img_text = pytesseract.image_to_string(img, lang=lang)
    return img_text


def two_frames_equals(frame_hash, other_frame_path):
    hash1 = str(frame_hash)
    hash2 = get_frame_hash(other_frame_path)
    if hash1 != hash2:
        return False
    return True


def already_saved_frame(frame_path: str, frame_hash, user):
    frame_list = os.listdir('files/frames')
    frame_list_to_check = []
    for frame in frame_list:
        frame_without_tale = frame[:len(frame) - 4]
        user_id_frist_index = frame_without_tale.rfind('_')
        if frame_without_tale[user_id_frist_index + 1:] == str(user.id):
            frame_list_to_check.append(frame)
    frame_list_to_check.remove(frame_path.split('/')[2])
    for other_frame in frame_list_to_check:
        other_frame = 'files/frames/' + other_frame
        has_duplicate = two_frames_equals(frame_hash, other_frame)
        if has_duplicate:
            return True
    return False


async def get_video_frames(path: str, user: User):
    user_frames = await get_user_frames(user)
    for frame in user_frames:
        try:
            os.remove(frame)
        except FileNotFoundError:
            pass
    await delete_all_user_frames_from_db(user)
    video = cv2.VideoCapture(path)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in range(frame_count):
        ret, frame = video.read()
        if not ret:
            break
        path_to_save = f'files/frames/frame_{i}_{user.id}.png'
        if i > 0:
            cv2.imwrite(path_to_save, frame)
            frame_hash = imagehash.average_hash(Image.open(path_to_save))
            has_dup = already_saved_frame(path_to_save, frame_hash, user)
            if has_dup:
                os.remove(path_to_save)
            else:
                await insert_frame_into_db(path_to_save, str(frame_hash), user)
        else:
            cv2.imwrite(path_to_save, frame)
            frame_hash = imagehash.average_hash(Image.open(path_to_save))
            await insert_frame_into_db(path_to_save, str(frame_hash), user)
    video.release()
    cv2.destroyAllWindows()


async def video_ocr(path: str, lang: str, user: User):
    await get_video_frames(path, user)
    video_text = {}
    listdir = sorted(os.listdir('files/frames'), key=lambda x: int(x.split('.')[0].split('_')[-1]))
    to_ocr_list = []
    for frame in listdir:
        frame_without_tale = frame[:len(frame) - 4]
        user_id_frist_index = frame_without_tale.rfind('_')
        if frame_without_tale[user_id_frist_index + 1:] == str(user.id):
            to_ocr_list.append(frame)
    for i, frame in enumerate(to_ocr_list):
        image_txt = await ocr(f'files/frames/{frame}', lang=lang)
        video_text[f'Кадр {i + 1}'] = image_txt
    good_format = [f'{key}\n\n{value}' for key, value in video_text.items()]
    return good_format
