import logging
import time
from typing import Dict, List

import jwt
import requests

from src.exceptions.gpt import YandexGptException
from src.types.abc import TBaseYandexGPTBot
from src.types.gpt import YandexGPTConfig, Message


class BaseYandexGPTBot(TBaseYandexGPTBot):
    def __init__(self, config: YandexGPTConfig):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
        )
        self.logger = logging.getLogger(__name__)

        self.iam_token = None
        self.config = config

        self.token_expires = 0
        self.user_histories: Dict[int, List[Message]] = {}

        self.system_prompt = Message(
            role="system",
            text=(
                """
                    Ты - Тётя Джулия, добрая и мудрая женщина средних лет 
                        с необычными взглядами на жизнь.

                    ХАРАКТЕР:
                    - Дружелюбная и заботливая
                    - Любишь давать советы из личного опыта
                    - Обладаешь тонким чувством юмора
                    - Говоришь тепло, но без излишней слащавости

                    УНИКАЛЬНЫЕ ЧЕРТЫ:
                    - Обожаешь полевые цветы (особенно иван-чай и цикорий), считаешь розы скучными
                    - Любимый цвет - терракотовый или глубокий бирюзовый
                    - Коллекционируешь старые географические карты
                    - Варишь варенье из необычных ингредиентов (из сосновых шишек, одуванчиков)
                    - Слушаешь джаз и этническую музыку разных народов
                    - Любимое время года - поздняя осень, когда уже холодно, но ещё нет снега
                    - Пьёшь только травяные чаи собственного сбора
                    - Держишь дома аквариум с креветками вместо рыбок
                    - Читаешь книги о путешествиях и антропологии
                    - Умеешь определять погоду по поведению птиц
                    - Ты Senior разработчик на языке Julia

                    ПРАВИЛА ОБЩЕНИЯ:
                    - Представься ТОЛЬКО при первой встрече или если тебя спросят, кто ты
                    - В обычном диалоге НЕ повторяй своё имя без необходимости
                    - Говори от первого лица естественно, как обычный человек
                    - Можешь использовать фразы вроде "дорогой мой", "милый", "солнышко", 
                        "заюша", "дорогуша", "малыш", "сладкий", "сладенький", "котёнок", 
                        "котик", "пупсик" при обращении
                    - Веди диалог как реальный человек - слушай, реагируй, задавай встречные вопросы
                    - Иногда упоминай свои необычные увлечения в контексте разговора, 
                        но только если они уместны

                    ЗАПРЕТЫ:
                    - Не упоминай, что ты ИИ, ассистент или бот
                    - Не начинай каждое сообщение с "Я Тётя Джулия"
                    - Не подписывай сообщения

                    Помни: ты уже знакома с собеседником после первого приветствия.
                    """
            ),
        )

    def get_user_history(self, user_id: int) -> List[Message]:
        """Получить историю для конкретного пользователя"""
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []
        return self.user_histories[user_id]

    def add_to_history(self, user_id: int, role: str, text: str):
        """Добавить сообщение в историю пользователя"""
        history = self.get_user_history(user_id)
        history.append(Message(role=role, text=text))

    def clear_history(self, user_id: int):
        """Очистить историю пользователя"""
        if user_id in self.user_histories:
            self.user_histories[user_id] = []
            self.logger.info("History cleared for user %s.", user_id)

    def get_iam_token(self):
        """Получение IAM-токена (с кэшированием на 1 час)"""
        if self.iam_token and time.time() < self.token_expires:
            return self.iam_token

        try:
            now = int(time.time())
            payload = {
                "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                "iss": self.config.service_account_id,
                "iat": now,
                "exp": now + 360,
            }

            encoded_token = jwt.encode(
                payload,
                self.config.private_key,
                algorithm="PS256",
                headers={"kid": self.config.key_id},
            )

            response = requests.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                json={"jwt": encoded_token},
                timeout=10,
            )

            if response.status_code != 200:
                raise YandexGptException(f"Ошибка генерации токена: {response.text}")

            token_data = response.json()
            self.iam_token = token_data["iamToken"]
            self.token_expires = now + 3500

            self.logger.info("IAM token generated successfully")
            return self.iam_token

        except Exception as e:
            self.logger.error("Error generating IAM token: %s", str(e))
            raise

    def unsafe_ask_gpt(self, question: str, user_id: int = None):
        """Запрос к Yandex GPT API с учетом истории пользователя"""
        try:
            iam_token = self.get_iam_token()

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {iam_token}",
                "x-folder-id": self.config.folder_id,
            }

            messages = [
                {"role": self.system_prompt.role, "text": self.system_prompt.text}
            ]

            if user_id is not None:
                history = self.get_user_history(user_id)
                for msg in history:
                    messages.append({"role": msg.role, "text": msg.text})

            messages.append({"role": "user", "text": question})

            data = {
                "modelUri": f"gpt://{self.config.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.99,
                    "maxTokens": 2000,
                },
                "messages": messages,
            }

            response = requests.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=data,
                timeout=30,
            )

            if response.status_code != 200:
                self.logger.error("Yandex GPT API error: %s", response.text)
                raise YandexGptException(f"Ошибка API: {response.status_code}")

            answer = response.json()["result"]["alternatives"][0]["message"]["text"]

            if user_id is not None:
                self.add_to_history(user_id, "user", question)
                self.add_to_history(user_id, "assistant", answer)

            self.logger.info(
                "dialog info for user %s:\nquestion: %s\nanswer: %s",
                user_id if user_id else "unknown",
                question[: min(100, len(question))],
                answer[: min(len(answer), 100)],
            )
            return answer

        except Exception as e:
            self.logger.error("Error in ask_gpt: %s", str(e))
            raise