import logging
import os

import cherrypy
import multiprocess as multiprocess
from dotenv import load_dotenv

from api.web.query import DictionApp
from core.openai_helper import OpenAIHelper
from api.telegram.telegram_bot import TelegramBotApp
from api.telegram.telegram_user import TelegramUserApp


def main():
    # Read .env file
    load_dotenv()

    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Check if the required environment variables are set
    required_values = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
    missing_values = [value for value in required_values if os.environ.get(value) is None]
    if len(missing_values) > 0:
        logging.error(f'The following environment values are missing in your .env: {", ".join(missing_values)}')
        exit(1)

    # Setup configurations
    openai_config = {
        'api_key': os.environ['OPENAI_API_KEY'],
        'show_usage': os.environ.get('SHOW_USAGE', 'false').lower() == 'true',
        'proxy': os.environ.get('PROXY', None),

        # 'gpt-3.5-turbo' or 'gpt-3.5-turbo-0301'
        'model': 'gpt-3.5-turbo',

        # A system message that sets the tone and controls the behavior of the assistant.
        'assistant_prompt': 'You are a helpful assistant.',

        # Number between 0 and 2. Higher values like 0.8 will make the output more random,
        # while lower values like 0.2 will make it more focused and deterministic.
        'temperature': 1,

        # How many chat completion choices to generate for each input message.
        'n_choices': 1,

        # The maximum number of tokens allowed for the generated answer
        'max_tokens': 1200,

        # Number between -2.0 and 2.0. Positive values penalize new tokens based on whether
        # they appear in the text so far, increasing the model's likelihood to talk about new topics.
        'presence_penalty': 0,

        # Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing
        # frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
        'frequency_penalty': 0,

        # The DALL·E generated image size
        'image_size': '512x512'
    }

    telegram_bot_config = {
        'token': os.environ['TELEGRAM_BOT_TOKEN'],
        'allowed_user_ids': os.environ.get('ALLOWED_TELEGRAM_USER_IDS', '*'),
        'proxy': os.environ.get('PROXY', None),
        "telegram_app_id": int(os.environ['TELEGRAM_APP_ID']),
        "telegram_app_hash": os.environ['TELEGRAM_APP_HASH'],
    }

    telegram_user_config = {
        "telegram_app_id": int(os.environ['TELEGRAM_APP_ID']),
        "telegram_app_hash": os.environ['TELEGRAM_APP_HASH'],
        'token': os.environ['TELEGRAM_BOT_TOKEN'],
    }

    # Setup and run ChatGPT and Telegram bot
    openai_helper = OpenAIHelper(config=openai_config)

    cherrypy.config.update(".\\resources\\web_api.ini")

    def web_api():
        cherrypy.config.update(".\\resources\\web_api.ini")
        cherrypy.quickstart(DictionApp(openai_helper))
    multiprocess.Process(target=web_api).start()

    telegram_user_app = TelegramUserApp(telegram_user_config, openai_helper)
    telegram_bot = TelegramBotApp(config=telegram_bot_config, openai=openai_helper)
    telegram_bot.add_decorator(telegram_user_app=telegram_user_app)

    telegram_bot.run()


if __name__ == '__main__':
    main()
