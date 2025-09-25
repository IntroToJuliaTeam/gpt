from ..mytypes.abc import TYandexGPTBot
from .answer_validator import AnswerValidator
from .base_yandex_gpt import BaseYandexGPTBot
from .prompt_validator import PromptValidator


class YandexGPTBot(BaseYandexGPTBot, TYandexGPTBot):
    def __init__(self, config):
        super().__init__(config)
        self.prompt_validator = PromptValidator(config)
        self.answer_validator = AnswerValidator(config)

    def ask_gpt(self, question: str, user_id: int) -> str:
        """Задать вопрос GPT с валидацией и историей пользователя"""
        is_valid_prompt = self.prompt_validator.check_prompt(question)
        if not is_valid_prompt:
            return "Как Тётя Джулия, я не могу ответить на этот вопрос."

        answer = super().unsafe_ask_gpt(question, user_id)

        is_valid_answer = self.answer_validator.check_answer(answer)
        if not is_valid_answer:
            return "Не заставляй Тётушку Джулию говорить плохие вещи!"

        return answer

    def reset_user_history(self, user_id: int):
        """Сбросить историю пользователя"""
        self.clear_history(user_id)
