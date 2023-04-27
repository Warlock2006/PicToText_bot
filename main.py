from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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
started = False


class MySG(StatesGroup):
    start = State()
    send_photo = State()
    send_video = State()
    send_lang = State()
    send_lang_to_translate_and_ocr = State()


@dp.message_handler(lambda x: not started, commands="start")
async def start(message: types.Message, state: FSMContext):
    global started
    started = True
    user = message.from_user
    buttons = [
        InlineKeyboardButton(text="🖼Отправить картинку!", callback_data='send_photo'),
        InlineKeyboardButton(text="🎬Отправить видео-фрагмент!", callback_data='send_video')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await bot.send_message(message.chat.id,
                           f'👋Привет, @{user.username}! Я PicToText - бот. '
                           f'Отправь мне картинку или видео с текстом ,а я отвечу тебе '
                           f'сообщением с текстом, который я смогу там разглядеть.',
                           reply_markup=keyboard)
    await state.set_state(MySG.start.state)


@dp.callback_query_handler(state=MySG.start.state, text='send_photo')
async def send_photo_handler(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_text('Отправь мне картинку!', chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    buttons = [
        InlineKeyboardButton(text='↩️Назад', callback_data='back')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id,
                                        reply_markup=keyboard)
    await state.set_state(MySG.send_photo.state)


@dp.callback_query_handler(state=MySG.all_states, text='back')
async def back_button_handler(callback: CallbackQuery, state: FSMContext):
    global started
    started = False
    buttons = [
        InlineKeyboardButton(text="🖼Отправить картинку!", callback_data='send_photo'),
        InlineKeyboardButton(text="🎬Отправить видео-фрагмент!", callback_data='send_video')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await bot.edit_message_text('Выбери действие', chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=keyboard)
    await state.set_state(MySG.start.state)


@dp.callback_query_handler(state=MySG.start.state, text='send_video')
async def send_video_handler(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_text('Отправь мне видео-фрагмент с текстом!', chat_id=callback.message.chat.id,
                                message_id=callback.message.message_id)
    buttons = [
        InlineKeyboardButton(text='↩️Назад', callback_data='back')
    ]
    keyboard = InlineKeyboardMarkup().add(*buttons)
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id,
                                        reply_markup=keyboard)
    await state.set_state(MySG.send_video.state)


@dp.message_handler(state=MySG.send_photo.state, content_types=['photo', 'document'])
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
        await state.set_state(MySG.send_lang.state)
    except Exception:
        await bot.send_message(message.chat.id, 'Ошибка!')


@dp.message_handler(state=MySG.send_video.state, content_types=['document', 'video'])
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
        await state.set_state(MySG.send_lang.state)
    except Exception:
        await bot.send_message(message.chat.id, 'Ошибка!')


@dp.message_handler(state=MySG.send_lang.state, content_types=['text'])
async def get_lang(message: types.Message, state: FSMContext):
    global started
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
            await state.update_data(user_=message.from_user)
            await bot.send_message(message.chat.id, f'Нужно перевести текст с {_type} на другой язык?',
                                   reply_markup=keyboard)

        else:
            await bot.send_message(message.chat.id,
                                   'Неверный формат ввода. Проверьте правильность ввода и повторите попытку!')
    except Exception as e:

        await bot.send_message(message.chat.id, f'Ошибка: {e}')
        started = False
        await state.finish()


@dp.callback_query_handler(state=MySG.send_lang.state, text=['no'])
async def no_button_handler(callback: CallbackQuery, state: FSMContext):
    global started
    data = await state.get_data()
    lang = data.get('lang')
    path = data.get('path')
    user = data.get('user_')
    type_of_ocr = data.get('type')
    if type_of_ocr == 'photo':
        await insert_photo_into_db(path, lang, user)
        img_text = await ocr(path, lang)
        await bot.send_message(callback.message.chat.id, img_text)
        await state.finish()
        started = False
    elif type_of_ocr == 'video':
        await insert_video_into_db(path, lang, user)
        await bot.send_message(callback.message.chat.id, 'Пожалуйста, подождите. Видео обрабатывается...')
        video_text = await video_ocr(path, lang)
        for frame_text in video_text:
            await bot.send_message(callback.message.chat.id, frame_text)
        await state.finish()
        started = False


@dp.callback_query_handler(state=MySG.send_lang.state, text=['yes'])
async def yes_button_handler(callback: CallbackQuery, state: FSMContext):
    await bot.send_message(callback.message.chat.id,
                           'Отправь мне язык на который надо перевести текст в формате en, ru, fr и т.д')
    await state.set_state(MySG.send_lang_to_translate_and_ocr.state)


@dp.message_handler(state=MySG.send_lang_to_translate_and_ocr.state, content_types=['text'])
async def get_lang_to_translate_and_ocr(message: Message, state: FSMContext):
    global started
    lang_to_translate = message.text
    data = await state.get_data()
    lang = data.get('lang')
    path = data.get('path')
    type_of_ocr = data.get('type')
    if type_of_ocr == 'photo':
        await insert_photo_into_db(path, lang, message.from_user)
        img_text = await ocr(path, lang)
        to_send_text = await translate(img_text, lang_to_translate)
        await bot.send_message(message.chat.id, to_send_text)
        await state.finish()
        started = False
    elif type_of_ocr == 'video':
        await insert_video_into_db(path, lang, message.from_user)
        await bot.send_message(message.chat.id, 'Пожалуйста, подождите. Видео обрабатывается...')
        video_text = await video_ocr(path, lang)
        for frame_text in video_text:
            to_send_text = await translate(frame_text, lang_to_translate)
            await bot.send_message(message.chat.id, to_send_text)
        await state.finish()
        started = False


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
