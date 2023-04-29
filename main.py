from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputFile
from aiogram.utils import executor

from dotenv import load_dotenv

from db_using import *
from msg_funcs import *

load_dotenv()

API_TOKEN = os.environ['TOKEN']
storage = MemoryStorage()
bot = Bot(API_TOKEN)
dp = Dispatcher(bot, storage=storage)
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Fedor\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


class OcrDialog(StatesGroup):
    start = State()
    send_photo = State()
    send_video = State()
    send_lang = State()
    send_lang_to_translate_and_ocr = State()


class HistoryDialog(StatesGroup):
    start = OcrDialog.start
    choose_type_of_history = State()
    show_photo_history = State()
    select_photo = State()
    show_video_history = State()
    select_video = State()


class BackButtonUsageStates(StatesGroup):
    start = HistoryDialog.start
    send_photo = OcrDialog.send_photo
    send_video = OcrDialog.send_video
    choose_type_of_history = HistoryDialog.choose_type_of_history
    show_photo_history = HistoryDialog.show_photo_history
    show_video_history = HistoryDialog.show_video_history


@dp.message_handler(commands="start")
async def start(message: types.Message, state: FSMContext):
    user = message.from_user
    await state.update_data(user_=user)
    buttons = [
        InlineKeyboardButton(text="🖼Отправить картинку!", callback_data='send_photo'),
        InlineKeyboardButton(text="🎬Отправить видео!", callback_data='send_video'),
        InlineKeyboardButton(text='📜История', callback_data='show_history')
    ]
    keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await bot.send_message(message.chat.id,
                           f'👋Привет, [{user.first_name}](tg://user?id={user.id})! Я PicToText - бот. '
                           f'Отправь мне картинку или видео с текстом ,а я отвечу тебе '
                           f'сообщением с текстом, который я смогу там разглядеть.',
                           reply_markup=keyboard, parse_mode='Markdown')
    await state.set_state(OcrDialog.start.state)


@dp.callback_query_handler(state=OcrDialog.start.state, text='send_photo')
async def send_photo_handler(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_text('Отправь мне картинку!', chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    buttons = [
        InlineKeyboardButton(text='↩️Назад', callback_data='back')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id,
                                        reply_markup=keyboard)
    await state.set_state(OcrDialog.send_photo.state)


@dp.callback_query_handler(state=OcrDialog.start.state, text='send_video')
async def send_video_handler(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_text('Отправь мне видео-фрагмент с текстом!', chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    buttons = [
        InlineKeyboardButton(text='↩️Назад', callback_data='back')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id,
                                        reply_markup=keyboard)
    await state.set_state(OcrDialog.send_video.state)


@dp.callback_query_handler(state=BackButtonUsageStates.all_states, text='back')
async def back_button_handler(callback: CallbackQuery, state: FSMContext):
    buttons = [
        InlineKeyboardButton(text="🖼Отправить картинку!", callback_data='send_photo'),
        InlineKeyboardButton(text="🎬Отправить видео!", callback_data='send_video'),
        InlineKeyboardButton(text='📜История', callback_data='show_history')
    ]
    keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await bot.edit_message_text('Выбери действие!', chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=keyboard)
    await state.set_state(OcrDialog.start.state)


@dp.callback_query_handler(state=HistoryDialog.start.state, text=['show_history'])
async def history_button_handler(callback: CallbackQuery, state: FSMContext):
    buttons = [
        InlineKeyboardButton(text="🖼Фото", callback_data='show_photo_history'),
        InlineKeyboardButton(text="🎬Видео", callback_data='show_video_history'),
        InlineKeyboardButton(text='↩️Назад', callback_data='back')
    ]
    keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await bot.edit_message_text('Выбери какую историю ты хочешь посмотреть!', chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=keyboard)
    await state.set_state(HistoryDialog.choose_type_of_history.state)


@dp.callback_query_handler(state=HistoryDialog.choose_type_of_history.state, text=['show_photo_history'])
async def photo_history_button_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = data.get('user_')
    photos_list, texts_list = await get_user_images_and_their_texts(user)
    if photos_list:
        for i, photo in enumerate(photos_list):
            photo = InputFile(photo)
            buttons = [InlineKeyboardButton('Показать текст', callback_data=f'{i}')]
            keyboard = InlineKeyboardMarkup().add(*buttons)
            await bot.send_photo(callback.message.chat.id, photo, f'Фото {i + 1}', reply_markup=keyboard)
        await state.update_data(texts_list=texts_list)
        await state.set_state(HistoryDialog.select_photo.state)
    else:
        await bot.send_message(callback.message.chat.id, 'Вы ещё не отправили мне ни одной картинки!')


@dp.callback_query_handler(state=HistoryDialog.select_photo.state)
async def choose_photo_buttons_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    texts_list = data.get('texts_list')
    await bot.send_message(callback.message.chat.id, texts_list[int(callback.data)])
    await state.finish()


@dp.callback_query_handler(state=HistoryDialog.choose_type_of_history.state, text=['show_video_history'])
async def video_history_button_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = data.get('user_')
    videos_list, texts_list = await get_user_videos_and_their_texts(user)
    if videos_list:
        for i, video in enumerate(videos_list):
            video = InputFile(video)
            buttons = [InlineKeyboardButton('Показать текст', callback_data=f'{i}')]
            keyboard = InlineKeyboardMarkup().add(*buttons)
            await bot.send_video(callback.message.chat.id, video, caption=f'Видео {i + 1}', reply_markup=keyboard)
        await state.update_data(texts_list=texts_list)
        await state.set_state(HistoryDialog.select_video.state)
    else:
        await bot.send_message(callback.message.chat.id, 'Вы ещё не отправили мне ни одного видео!')


@dp.callback_query_handler(state=HistoryDialog.select_video)
async def choose_video_buttons_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    texts_list = data.get('texts_list')
    video_index = int(callback.data)
    for frame_text in texts_list[video_index]:
        await bot.send_message(callback.message.chat.id, frame_text)
    await state.finish()


@dp.message_handler(state=OcrDialog.send_photo.state, content_types=['photo', 'document'])
async def save_picture(message: types.Message, state: FSMContext):
    try:
        if message.content_type == 'photo':
            file_path = await download_photo(message, bot)
            await state.update_data(path='files/' + file_path)
        elif message.content_type == 'document':
            file_path = await download_doc(message, bot)
            await state.update_data(path='files/' + file_path)
        await state.update_data(type='photo')
        await bot.send_message(message.chat.id, 'Картинка сохранена!')
        await bot.send_message(message.chat.id,
                               'Отправьте язык текста на картинке в формате: eng, rus, fra и т.д.\n'
                               'Если в тексте используется несколько языков, то в формате rus+eng, deu+fra и т.д.')
        await state.set_state(OcrDialog.send_lang.state)
    except Exception as e:
        await bot.send_message(message.chat.id, f'Ошибка: {e}')
        await state.finish()


@dp.message_handler(state=OcrDialog.send_video.state, content_types=['document', 'video'])
async def save_video(message: types.Message, state: FSMContext):
    try:
        if message.content_type == 'video':
            file_path = await download_video(message, bot)
            await state.update_data(path='files/' + file_path)
        elif message.content_type == 'document':
            file_path = await download_doc(message, bot)
            await state.update_data(path='files/' + file_path)
        await state.update_data(type='video')
        await bot.send_message(message.chat.id, 'Видео сохранено!')
        await bot.send_message(message.chat.id,
                               'Отправьте язык текста на видео в формате: eng, rus, fra и т.д.\n'
                               'Если в тексте используется несколько языков, то в формате rus+eng, deu+fra и т.д.')
        await state.set_state(OcrDialog.send_lang.state)
    except Exception as e:
        await bot.send_message(message.chat.id, f'Ошибка: {e}')
        await state.finish()


@dp.message_handler(state=OcrDialog.send_lang.state, content_types=['text'])
async def get_lang(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        lang = message.text
        lang_checker = all(True if language in pytesseract.get_languages() else False for language in lang.split('+'))
        _type = data.get('type')
        if _type == 'photo':
            _type = 'картинки'
        elif _type == 'video':
            _type = 'видео'
        if lang_checker:
            await state.update_data(lang=lang)
            buttons = [InlineKeyboardButton('✅Да', callback_data='yes'),
                       InlineKeyboardButton('❌Нет', callback_data='no')]
            keyboard = InlineKeyboardMarkup().add(*buttons)
            await bot.send_message(message.chat.id, f'Нужно перевести текст с {_type} на другой язык?',
                                   reply_markup=keyboard)

        else:
            await bot.send_message(message.chat.id,
                                   'Неверный формат ввода. Проверьте правильность ввода и повторите попытку!')
    except Exception as e:

        await bot.send_message(message.chat.id, f'Ошибка: {e}')
        await state.finish()


@dp.callback_query_handler(state=OcrDialog.send_lang.state, text=['no'])
async def no_button_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang')
    path = data.get('path')
    user = data.get('user_')
    type_of_ocr = data.get('type')
    if type_of_ocr == 'photo':
        img_text = await ocr(path, lang)
        img_text: str
        img_text = img_text.replace('|', 'I')
        await insert_photo_into_db(path, lang, img_text, user)
        await bot.send_message(callback.message.chat.id, img_text)
        await state.finish()
        started = False
    elif type_of_ocr == 'video':
        await bot.send_message(callback.message.chat.id, 'Пожалуйста, подождите. Видео обрабатывается...')
        video_text = await video_ocr(path, lang, user)
        await insert_video_into_db(path, lang, video_text, user)
        for frame_text in video_text:
            frame_text = frame_text.replace('|', 'I')
            await bot.send_message(callback.message.chat.id, frame_text)
        await state.finish()


@dp.callback_query_handler(state=OcrDialog.send_lang.state, text=['yes'])
async def yes_button_handler(callback: CallbackQuery, state: FSMContext):
    await bot.send_message(callback.message.chat.id,
                           'Отправь мне язык на который надо перевести текст в формате en, ru, fr и т.д')
    await state.set_state(OcrDialog.send_lang_to_translate_and_ocr.state)


@dp.message_handler(state=OcrDialog.send_lang_to_translate_and_ocr.state, content_types=['text'])
async def get_lang_to_translate_and_ocr(message: Message, state: FSMContext):
    lang_to_translate = message.text
    data = await state.get_data()
    lang = data.get('lang')
    path = data.get('path')
    type_of_ocr = data.get('type')
    if type_of_ocr == 'photo':
        img_text = await ocr(path, lang)
        img_text = img_text.replace('|', 'I')
        await insert_photo_into_db(path, lang, img_text, message.from_user)
        to_send_text = await translate(img_text, lang_to_translate)
        await bot.send_message(message.chat.id, to_send_text)
        await state.finish()
    elif type_of_ocr == 'video':
        await bot.send_message(message.chat.id, 'Пожалуйста, подождите. Видео обрабатывается...')
        video_text = await video_ocr(path, lang, message.from_user)
        await insert_video_into_db(path, lang, video_text, message.from_user)
        for frame_text in video_text:
            frame_text = frame_text.replace('|', 'I')
            to_send_text = await translate(frame_text, lang_to_translate)
            await bot.send_message(message.chat.id, to_send_text)
        await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
