from openai import AsyncClient
from pyrogram import Client
from pydantic import SecretStr
from pyrogram.types import Message
from pydantic_settings import BaseSettings, SettingsConfigDict


class DotEnv(BaseSettings):
    OPENAI_KEY: SecretStr
    API_ID: SecretStr
    API_HASH: SecretStr
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )
dotenv = DotEnv()

client = Client(name='Клиентик', api_id=dotenv.API_ID.get_secret_value(), api_hash=dotenv.API_HASH.get_secret_value())
lm = []
channels = ("naebnet", 'gptpublic', 'neurohub', 'killerfeat',
            'tips_ai', 'craftdivision', 'neuro_pushka')
oi = AsyncClient(api_key=dotenv.OPENAI_KEY.get_secret_value())


@client.on_message()
async def copy_to_my_channel(_, message: Message):
    if str(message.chat.username) not in channels:
        return

    if not message.media_group_id:
        caption = ''
        if message.caption:
            completion = await oi.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "developer", "content": "Ты делаешь рерайт этого текста, чтобы он сохранил смысл, но поменял вид."},
                {"role": "user", "content": f"Текст: {message.caption}"}
            ]
            )
            caption = completion.choices[0].message.content
        return await client.copy_message(from_chat_id = message.chat.id, chat_id = 8192300340, message_id = message.id, caption=caption)

    if message.media_group_id not in lm:
        lm.append(message.media_group_id)
        completion = await oi.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "developer", "content": "Ты делаешь рерайт этого текста, чтобы он сохранил смысл, но поменял вид."},
            {"role": "user", "content": f"Текст: {message.caption}"}
        ]
        )
        await client.copy_media_group(from_chat_id = message.chat.id, chat_id = 8192300340, message_id = message.id, captions=completion.choices[0].message.content)
        await client.send_message(8192300340, 'Закончилось')


client.run()
