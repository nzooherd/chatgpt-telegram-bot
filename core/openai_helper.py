import logging
from typing import Iterator, Union

import openai


class OpenAIHelper:
    """
    ChatGPT helper class.
    """

    def __init__(self, config: dict):
        """
        Initializes the OpenAI helper class with the given configuration.
        :param config: A dictionary containing the GPT configuration
        """
        openai.api_key = config['api_key']
        openai.proxy = config['proxy']
        self.config = config
        self.sessions: dict[int: dict[str: list]] = dict() # {chat_id: history}
        self.functions = {"assistant", "polish", "translate", "diction"}

    def get_function(self) -> str:
        # TODO
        pass

    def get_chat_response(self, chat_id: int, function: str, query: str, stream: bool = False) ->  Union[str, Iterator[str]]:
        """
        Gets a response from the GPT-3 model.
        :param chat_id: The chat ID
        :param query: The query to send to the model
        :param function: #TODO
        :return: The answer from the model
        """
        try:
            if chat_id not in self.sessions:
                self.reset_chat_history(chat_id)

            self.__add_to_history(chat_id, "user", function, content=query)

            response = openai.ChatCompletion.create(
                model=self.config['model'],
                messages=self.sessions[chat_id][function],
                temperature=self.config['temperature'],
                n=self.config['n_choices'],
                max_tokens=self.config['max_tokens'],
                presence_penalty=self.config['presence_penalty'],
                frequency_penalty=self.config['frequency_penalty'],
                stream=stream
            )

            if stream:
                #TODO
                return response

            if len(response.choices) > 0:
                answer = ''

                if len(response.choices) > 1 and self.config['n_choices'] > 1:
                    for index, choice in enumerate(response.choices):
                        if index == 0:
                            self.__add_to_history(chat_id, "assistant", function, content=choice['message']['content'])
                        answer += f'{index+1}\u20e3\n'
                        answer += choice['message']['content']
                        answer += '\n\n'
                else:
                    answer = response.choices[0]['message']['content']
                    self.__add_to_history(chat_id, "assistant", function, content=answer)

                if self.config['show_usage']:
                    answer += "\n\n---\n" \
                              f"💰 Tokens used: {str(response.usage['total_tokens'])}" \
                              f" ({str(response.usage['prompt_tokens'])} prompt," \
                              f" {str(response.usage['completion_tokens'])} completion)"

                return answer
            else:
                logging.error('No response from GPT-3')
                return "⚠️ _An error has occurred_ ⚠️\nPlease try again in a while."

        except openai.error.RateLimitError as e:
            logging.exception(e)
            return f"⚠️ _OpenAI Rate Limit exceeded_ ⚠️\n{str(e)}"

        except openai.error.InvalidRequestError as e:
            logging.exception(e)
            return f"⚠️ _OpenAI Invalid request_ ⚠️\n{str(e)}"

        except Exception as e:
            logging.exception(e)
            return f"⚠️ _An error has occurred_ ⚠️\n{str(e)}"


    def generate_image(self, prompt: str) -> str:
        """
        Generates an image from the given prompt using DALL·E model.
        :param prompt: The prompt to send to the model
        :return: The image URL
        """
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size=self.config['image_size']
            )
            return response['data'][0]['url']

        except Exception as e:
            logging.exception(e)
            raise e

    def transcribe(self, filename):
        """
        Transcribes the audio file using the Whisper model.
        """
        try:
            with open(filename, "rb") as audio:
                result = openai.Audio.transcribe("whisper-1", audio)
                return result.text
        except Exception as e:
            logging.exception(e)
            raise e

    def reset_chat_history(self, chat_id):
        """
        Resets the conversation history.
        """
        self.sessions[chat_id] = {function: [{"role": "system", "content": self.config['assistant_prompt']}]
                                  for function in self.functions}


    def __add_to_history(self, chat_id, role, function: str, content):
        """
        Adds a message to the conversation history.
        :param chat_id: The chat ID
        :param role: The role of the message sender
        :param content: The message content
        """
        self.sessions[chat_id][function].append({"role": role, "content": content})
