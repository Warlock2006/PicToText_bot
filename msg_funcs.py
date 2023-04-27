import os
from deep_translator import GoogleTranslator
import aiomisc
import imagehash
import numpy
import cv2
import pytesseract
from PIL import Image
from aiogram.types import Message
from aiogram import Bot


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


def two_image_equals(img1: Image, img2: Image):
    hash1 = imagehash.average_hash(img1)
    hash2 = imagehash.average_hash(img2)
    if hash1 != hash2:
        return False
    return True


def already_saved_frame(frame_path: str):
    frame = Image.open(frame_path)
    frame_list = os.listdir('files/frames')
    frame_list_to_check = frame_list.copy()
    frame_list_to_check.remove(frame_path.split('/')[2])
    for other_frame in frame_list_to_check:
        other_frame = Image.open(f'files/frames/{other_frame}')
        has_duplicate = two_image_equals(frame, other_frame)
        if has_duplicate:
            return True
    return False


def get_video_frames(path: str):
    for file in os.listdir('files/frames'):
        os.remove(f'files/frames/{file}')
    os.rmdir('files/frames')
    if not os.path.exists('files/frames'):
        os.mkdir('files/frames')

    video = cv2.VideoCapture(path)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in range(frame_count):
        ret, frame = video.read()
        if not ret:
            break
        path_to_save = f'files/frames/frame_{i}.png'
        if i > 0:
            cv2.imwrite(path_to_save, frame)
            has_dup = already_saved_frame(path_to_save)
            if has_dup:
                os.remove(path_to_save)
        else:
            cv2.imwrite(path_to_save, frame)
    video.release()
    cv2.destroyAllWindows()


async def video_ocr(path: str, lang: str):
    get_video_frames(path)
    video_text = {}
    listdir = sorted(os.listdir('files/frames'), key=lambda x: int(x.split('.')[0].split('_')[-1]))
    for i, frame in enumerate(listdir):
        image_txt = await ocr(f'files/frames/{frame}', lang=lang)
        video_text[f'Кадр {i + 1}'] = image_txt
    good_format = [f'{key}\n\n{value}' for key, value in video_text.items()]
    return good_format
