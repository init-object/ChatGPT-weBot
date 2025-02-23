import json
import logging
import requests
import tiktoken
from pygtrans import Translate, Null

transClient = Translate()

class ChatbotError(Exception):
    """
    Base class for exceptions in this module.
    Error codes:
    -3: response runtime error
    -2: API busy error
    -1: User error
    0: Unknown error
    """

    error: str
    message: str
    code: int

    def __init__(self, source: str, message: str, code: int = 0) -> None:
        self.error = source
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"{self.error}: {self.message} (code: {self.code})"


class Chatbot:
    """
    Chatbot class for ChatGPT
    """

    def __init__(
            self,
            config,
    ) -> None:
        """
        Initialize Chatbot with API key (from https://platform.openai.com/account/api-keys)
        """
        self.api_key = config["api_key"]
        self.engine = config["engine"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]
        self.top_p = config["top_p"]
        self.presence_penalty = config["presence_penalty"]
        self.frequency_penalty = config["frequency_penalty"]
        self.reply_count = config["reply_count"]
        self.system_character = config["system_character"]
        self.default = self.system_character

        self.proxy = config["proxy"]

        self.session = requests.Session()
        if len(self.proxy) != 0:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }

        self.conversation = [{"role": "system", "content": self.system_character}]
        self.prev_question = []
        self.question_num = 0

    def set_system_character(self, role: str) -> None:
        with open(".config/sys_character.json", encoding="utf-8") as f:
            sys_char: dict = json.load(f)
        f.close()

        if role not in sys_char:
            raise ChatbotError("KeyError", f"{role} isn't in sys_character.json!", -1)
        else:
            self.system_character = sys_char[role]
            self.conversation[0] = {"role": "system", "content": self.system_character}
        del sys_char

    def __add_to_conversation(self, message: str, role: str) -> None:
        """
        Add a message to the conversation
        """
        self.conversation.append({"role": role, "content": message})

    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    def __get_token_count(self) -> int:
        """
        Get token count
        """

        tiktoken.model.MODEL_PREFIX_TO_ENCODING["gpt-4-"] = "cl100k_base"
        tiktoken.model.MODEL_TO_ENCODING["gpt-4"] = "cl100k_base"

        encoding = tiktoken.encoding_for_model(self.engine)

        num_tokens = 0
        for message in self.conversation:
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            num_tokens += 4
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += 1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def __truncate_conversation(self) -> None:
        """
        Truncate the conversation
        """
        while True:
            if (self.__get_token_count() > self.max_tokens) and (len(self.conversation) > 1):
                self.conversation.pop(1)
                # Don't remove the system character
            else:
                break

    def get_rest_tokens(self) -> int:
        """
        Get rest tokens to max tokens
        """
        # logging.exception("rest token:" + str(self.max_tokens - self.get_token_count()))
        return self.max_tokens - self.__get_token_count()

    def ask(self, prompt: str, timeout: float = 120, access_internet=False, access_result=3) -> str:
        """
        Ask a question
        """
        if prompt is not None:
            if access_internet:
                params = (
                    ('q', f'{prompt}'),
                    ('max_results', f'{access_result}'),
                    ('region', 'wt-wt'),
                )

                headers = {
                    'authority': 'ddg-webapp-aagd.vercel.app',
                    'accept': '*/*',
                    'accept-language': 'pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                    'content-type': 'application/json',
                    'origin': 'https://chat.openai.com',
                    'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Microsoft Edge";v="110"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.57',
                }
                try:
                    response = requests.get('https://ddg-webapp-aagd.vercel.app/search', headers=headers, params=params,
                                            timeout=10)
                except Exception as e:
                    # logging.exception(u"【ddg-webapp Exception】: {}".format(e))
                    raise ChatbotError("ConnectionError", "ddg-webapp API Error", -2)

                if response.status_code != 200:
                    raise ChatbotError("ConnectionError", "Cannot access internet info", response.status_code)
                else:
                    json_data = json.loads(response.content)

                result = ""
                try:
                    for item in json_data:
                        result += item["title"] + "\n"
                        result += item["body"] + "\n"
                        result += "URL: " + item["href"] + "\n\n"
                except Exception as e:
                    raise ChatbotError("Json Parse Error", e.__str__(), -1)
                    # logging.exception(u"parse json_data error: {}".format(e)

                result = result.strip()
                if result != '':
                    self.__add_to_conversation(result.strip(), "system")
                    self.prev_question.append([result.strip(), prompt])
                else:
                    self.prev_question.append([prompt])

            else:
                self.prev_question.append([prompt])

            self.__add_to_conversation(prompt, "user")
            self.question_num += 1

        else:
            self.conversation.pop()

        self.__truncate_conversation()

        times = 3
        while times > 0:

            try:
                response = self.session.post(
                    url="https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.engine,
                        "messages": self.conversation,
                        "temperature": self.temperature,
                        "top_p": self.top_p,
                        "presence_penalty": self.presence_penalty,
                        "frequency_penalty": self.frequency_penalty,
                        "n": self.reply_count,
                        "user": "user",
                        "max_tokens": self.get_rest_tokens(),
                    },
                    timeout=timeout
                )
            except Exception as e:
                # logging.exception(u"ChatGPT Exception: {}".format(e))
                raise ChatbotError("ConnectionError", f'ChatGPT API error {e.__str__()}', -3)

            times -= 1

            if times == 0 and response.status_code != 200:
                raise ChatbotError("ConnectionError", response.text, response.status_code)
            else:
                try:
                    content = json.loads(response.content)
                    # logging.info(content)
                    response_text = content["choices"][0]["message"]
                    response_role = response_text["role"]
                    assist_text = response_text["content"]

                    self.__add_to_conversation(assist_text, response_role)
                    return assist_text
                except Exception as e:
                    logging.info(content)
                    logging.exception(u"ChatGPT Exception: {}".format(e))
                    raise ChatbotError("ConnectionError", response.text, response.status_code)

    def image_create(self, prompt: str, timeout: float = 120) -> str:
        """
        create img
        """
        times = 3
        while times > 0:

            try:
                response = self.session.post(
                    url="https://api.openai.com/v1/images/generations",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "prompt": prompt,
                        "n": 1,
                        "size": "512x512",
                        "response_format": "b64_json"
                    },
                    timeout=timeout
                )
            except Exception as e:
                # logging.exception(u"ChatGPT Exception: {}".format(e))
                raise ChatbotError("ConnectionError", f'ChatGPT API error {e.__str__()}', -3)

            times -= 1

            if times == 0 and response.status_code != 200:
                raise ChatbotError("ConnectionError", response.text, response.status_code)
            else:
                try:
                    content = json.loads(response.content)
                    b64_json = content["data"][0]["b64_json"]
                    
                    return b64_json
                except Exception as e:
                    logging.info(content)
                    logging.exception(u"ChatGPT Exception: {}".format(e))
                    raise ChatbotError("ChatGPT Exception", response.text, response.status_code)

    def image_create_sdi(self, prompt: str, negivate_prompt: str = "", timeout: float = 120) -> str:
        """
        create img
        """
        d = transClient.detect(prompt)
        if d.language == 'zh-CN':
            text = transClient.translate(prompt, target='en')
            if not isinstance(text, Null):
                prompt = text.translatedText
        d = transClient.detect(negivate_prompt)
        if d.language == 'zh-CN':
            text_ne = transClient.translate(negivate_prompt, target='en')
            if not isinstance(text_ne, Null):
                negivate_prompt = text_ne.translatedText
        times = 3
        while times > 0:

            try:
                response = self.session.post(
                    url="http://192.168.10.129:7860/sdapi/v1/txt2img",
                    json={
                        "prompt": prompt + ", RAW photo, *subject*, (high detailed skin:1.2), 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT3",
                        "negative_prompt": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck" + negivate_prompt,
                        "steps": 40,
                        "width": 512,
                        "height": 512,
                        "cfg_scale": 7,
                        "sampler": "Euler a",
                        "sed": -1
                        
                    },
                    timeout=timeout
                )
            except Exception as e:
                # logging.exception(u"ChatGPT Exception: {}".format(e))
                raise ChatbotError("ConnectionError", f'ChatGPT API error {e.__str__()}', -3)

            times -= 1

            if times == 0 and response.status_code != 200:
                raise ChatbotError("ConnectionError", response.text, response.status_code)
            else:
                try:
                    content = json.loads(response.content)
                    b64_json = content["images"][0]
                    
                    return b64_json
                except Exception as e:
                    logging.info(content)
                    logging.exception(u"ChatGPT Exception: {}".format(e))
                    raise ChatbotError("ChatGPT Exception", response.text, response.status_code)

    def rollback_conversation(self, n: int = 1) -> None:
        """
        Rollback the conversation.
        :param n: Integer. The number of messages to rollback
        :return: None
        """
        iterable = 0
        while n > 0:
            iterable += len(self.prev_question[-1]) + 1
            self.question_num -= 1
            self.prev_question.pop()
            n -= 1

        while iterable > 0:
            if len(self.conversation) == 1:
                break
            self.conversation.pop()
            iterable -= 1

    def reset(self) -> None:
        """
        Reset the conversation.
        :return: None
        """
        self.conversation = [{"role": "system", "content": self.default}]
        self.prev_question.clear()
        self.question_num = 0

    def conclusion(self) -> str:
        """
        conclude the conversation.
        :return: Str
        """
        try:
            self.ask(prompt="用150字内总结全部对话")
        except ChatbotError as CE:
            return CE.__str__()
        conclude = self.conversation.pop()
        self.reset()
        self.conversation.append(conclude)
        return conclude["content"]
