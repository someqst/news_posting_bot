import asyncio, json, aiofiles, os
from aiogram import F
from uuid import uuid4
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


TARGET_ACCOUNT = 815294694

class DotEnv(BaseSettings):
    OPENAI_KEY: SecretStr
    API_ID: SecretStr
    API_HASH: SecretStr
    BOT_TOKEN: SecretStr
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

dotenv = DotEnv()


dp = Dispatcher(storage=MemoryStorage())
bot = Bot(token=dotenv.BOT_TOKEN.get_secret_value())


cached_id = []
new_media_group = {}
cached_caption = []


@dp.message(F.text == '/start')
async def answer_start(message: Message):
    await message.answer('Да, я работаю')


@dp.message(F.text)
async def recieve_text(message: Message):
    if message.text and message.text == 'Закончилось':
        mg = MediaGroupBuilder()
        for media in new_media_group[cached_id[0]]:
            key, value = next(iter(media.items()))
            if value == 'video':
                mg.add_video(media=key)
            else:
                mg.add_photo(media=key)
                
        mg.caption = cached_caption[0]
        await bot.send_media_group(TARGET_ACCOUNT, mg.build())

        file_id = str(uuid4())

        final_json = {
            "caption": cached_caption[0],
            "media": new_media_group[cached_id[0]]
        }

        async with aiofiles.open(f'data/posts/{file_id}.json', 'w', encoding='utf-8') as file:
            await file.write(json.dumps(final_json, indent=4, ensure_ascii=False))

        kb = InlineKeyboardBuilder()
        kb.button(text='Отправить в группу ✅', callback_data=f'send_mg_{file_id}')
        await bot.send_message(TARGET_ACCOUNT, 'Отправляем в группу?', reply_markup=kb.as_markup())

        cached_id.clear()
        new_media_group.clear()
        cached_caption.clear()


@dp.message()
async def recieve_media_group(message: Message):
    if message.media_group_id:
        if message.media_group_id in cached_id:
            if message.photo:
                new_media_group[message.media_group_id].append({message.photo[-1].file_id: "photo"})
            elif message.video:
                new_media_group[message.media_group_id].append({message.video.file_id: "video"})
        else:
            cached_id.append(message.media_group_id)
            if message.caption:
                cached_caption.append(message.caption)

            if message.photo:
                new_media_group[message.media_group_id] = [{message.photo[-1].file_id: "photo"}]
            elif message.video:
                new_media_group[message.media_group_id] = [{message.video.file_id: "video"}]
    else:
        kb = InlineKeyboardBuilder()
        kb.button(text='Отправить в группу ✅', callback_data=f'send_msg_{uuid4()}')
        if message.photo:
            return await bot.send_photo(TARGET_ACCOUNT, message.photo[-1].file_id, caption=message.caption, reply_markup=kb.as_markup())
        
        return await bot.send_video(TARGET_ACCOUNT, message.video.file_id, caption=message.caption, reply_markup=kb.as_markup())


@dp.callback_query(F.data.startswith('send_mg_'))
async def send_mediagroup_to_group(call: CallbackQuery):
    await call.answer()
    await call.message.delete()

    async with aiofiles.open(f'data/posts/{(call.data).split("_")[2]}.json', 'r', encoding='utf-8') as file:
        opened_file = await file.read()

    opened_file = json.loads(opened_file)

    os.remove(f'data/posts/{(call.data).split("_")[2]}.json')

    mg = MediaGroupBuilder()
    for media in opened_file['media']:
        key, value = next(iter(media.items()))
        if value == 'video':
            mg.add_video(media=key)
        else:
            mg.add_photo(media=key)
            
    mg.caption = opened_file["caption"]
    await bot.send_media_group("@iigizm", mg.build())


@dp.callback_query(F.data.startswith('send_msg_'))
async def send_mediagroup_to_group(call: CallbackQuery):
    await call.answer()
    await call.message.delete()

    if call.message.photo:
        return await bot.send_photo("@iigizm", caption=call.message.caption, photo=call.message.photo[-1].file_id)
    else:
        return await bot.send_video("@iigizm", caption=call.message.caption, video=call.message.video.file_id)

    



async def main():
    await bot.send_message(7731063219, 'started')
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())