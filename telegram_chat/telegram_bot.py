import asyncio
import logging
import os
from random import random

from telethon import TelegramClient, events
from telethon.events import NewMessage

from openai_helper import OpenAIHelper
from pydub import AudioSegment

class TelegramBotApp:
    """
    Class representing a Chat-GPT3 Telegram Bot.
    """

    def __init__(self, config: dict, openai: OpenAIHelper):
        """
        Initializes the bot with the given configuration and GPT-3 bot object.
        :param config: A dictionary containing the bot configuration
        :param openai: OpenAIHelper object
        """
        self.config = config
        self.openai = openai
        self.client = TelegramClient('.chatgpt-telegram-bot', config["telegram_app_id"], config["telegram_app_hash"])\
            .start(bot_token=config["token"])
        self.disallowed_message = "Sorry, you are not allowed to use this bot. You can check out the source code at " \
                                  "https://github.com/n3d1117/chatgpt-telegram-bot"

    async def help(self, event: NewMessage.Event) -> None:
        """
        Shows the help menu.
        """
        await event.reply("/reset - Reset conversation\n"
                           "/image <prompt> - Generate image\n"
                           "/help - Help menu\n\n"
                           "Open source at https://github.com/n3d1117/chatgpt-telegram-bot",
                           disable_web_page_preview=True)

    async def reset(self, event: NewMessage.Event):
        """
        Resets the conversation.
        """
        if not self.is_allowed(event):
            logging.warning(f'User {event.chat.username} is not allowed to reset the conversation')
            await self.send_disallowed_message(event)
            return

        logging.info(f'Resetting the conversation for user {event.chat.username}...')

        chat_id = event.chat_id
        self.openai.reset_chat_history(chat_id=chat_id)
        await event.send_message(chat_id=chat_id, text='Done!')

    #async def image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #    """
    #    Generates an image for the given prompt using DALL·E APIs
    #    """
    #    if not self.is_allowed(update):
    #        logging.warning(f'User {update.message.from_user.name} is not allowed to generate images')
    #        await self.send_disallowed_message(update, context)
    #        return

    #    logging.info(f'New image generation request received from user {update.message.from_user.name}')

    #    chat_id = update.effective_chat.id
    #    image_query = update.message.text.replace('/image', '').strip()
    #    if image_query == '':
    #        await context.bot.send_message(chat_id=chat_id, text='Please provide a prompt!')
    #        return

    #    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.UPLOAD_PHOTO)
    #    try:
    #        image_url = self.openai.generate_image(prompt=image_query)
    #        await context.bot.send_photo(
    #            chat_id=chat_id,
    #            reply_to_message_id=update.message.message_id,
    #            photo=image_url
    #        )
    #    except:
    #        await context.bot.send_message(
    #            chat_id=chat_id,
    #            reply_to_message_id=update.message.message_id,
    #            text='Failed to generate image'
    #        )

    async def transcribe(self, event: NewMessage.Event):
        """
        Transcribe audio messages.
        """
        if not self.is_allowed(event):
            logging.warning(f'User {event.chat.username} is not allowed to transcribe audio messages')
            await self.send_disallowed_message(event)
            return

        chat = event.chat
        if not event.message.voice and not event.message.audio:
            await self.client.send_message(
                entity=chat,
                message='Unsupported file type',
                reply_to=event.message.id
            )
            return

        logging.info(f'New transcribe request received from user {event.chat.username}')

        async with self.client.action(chat, "typing", delay=5):
            await asyncio.sleep(0.1)
        filename = event.voice.file_unique_id if event.message.voice else event.message.audio.file_unique_id
        filename_ogg = f'{filename}.ogg'
        filename_mp3 = f'{filename}.mp3'

        try:
            if event.message.voice:
                await self.client.download_file(event.message.voice.file_id, filename_ogg)
                ogg_audio = AudioSegment.from_ogg(filename_ogg)
                ogg_audio.export(filename_mp3, format="mp3")

            elif event.message.audio:
                await self.client.download_file(event.message.audio.file_id, filename_mp3)

            # Transcribe the audio file
            transcript = self.openai.transcribe(filename_mp3)

            # Send the transcript
            await self.client.send_message(
                entity=chat,
                message=transcript,
                reply_to=event.message.id
            )
        except:
            await self.client.send_message(
                entity=chat,
                message="Failed to transcribe text",
                reply_to=event.message.id
            )

        finally:
            # Cleanup files
            if os.path.exists(filename_mp3):
                os.remove(filename_mp3)
            if os.path.exists(filename_ogg):
                os.remove(filename_ogg)

    async def prompt(self, event: NewMessage.Event):
        """
        React to incoming messages and respond accordingly.
        """
        if not self.is_allowed(event):
            logging.warning(f'User {event.chat.username} is not allowed to use the bot')
            await self.send_disallowed_message(event)
            return

        logging.info(f'New message received from user {event.chat.username}')
        chat = event.chat
        chat_id = event.chat_id

        async with self.client.action(chat, "typing", delay=5):
            await asyncio.sleep(0.1)
            response = self.openai.get_chat_response(chat_id=chat_id, query=event.message.text, stream=True)

            text = ""
            message = None
            update = False
            for rep in response:
                try:
                    cur_text = rep["choices"][0]["delta"]["content"]
                    text += cur_text
                    update = True
                    if random() > 0.2:
                        continue
                    if not message:
                        message = await self.client.send_message(chat.id, text)
                    else:
                        await self.client.edit_message(
                            entity=message,
                            message=text,
                        )
                        update = False
                except Exception as e:
                    pass

            if text and message and update:
                await self.client.edit_message(
                    entity=message,
                    message=text,
                )

    async def send_disallowed_message(self, event: NewMessage.Event):
        """
        Sends the disallowed message to the user.
        """
        await event.reply(self.disallowed_message)

    async def error_handler(self, event: NewMessage.Event) -> None:
        """
        Handles errors in the telegram-python-bot library.
        """
        logging.debug(f'Exception while handling an update: ') #TODO

    def is_allowed(self, event: NewMessage.Event) -> bool:
        """
        Checks if the user is allowed to use the bot.
        """
        if self.config['allowed_user_ids'] == '*':
            return True
        return str(event.chat_id) in self.config['allowed_user_ids'].split(',')

    async def any_message_arrived_handler(self, event: NewMessage.Event):
        await event.reply(event.chat_id)
        print('We are handling message events')

    def run(self):
        """
        Runs the bot indefinitely until the user presses Ctrl+C
        """
        self.client.on(events.NewMessage())(self.prompt)
        self.client.run_until_disconnected()
