import copy
import random
from datetime import datetime, timedelta
import logging
from random import randint
import handlers

# from _token import token, group_id
try:
    import settings
except ImportError:
    exit('DO cp settings.py.default settings.py and set token!')

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

log = logging.getLogger('bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(" %(levelname)s %(message)s"))
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler("bot.log", mode='w', encoding='utf8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    file_handler.setLevel(logging.DEBUG)

    log.setLevel(logging.DEBUG)
    log.addHandler(stream_handler)
    log.addHandler(file_handler)


def flights_generator(cities):
    schedule = []
    dates = [1, 5, 13, 15, 17, 23, 28]
    current_date = datetime.now().date()
    for city in cities:
        for city_to in cities:
            if city == city_to:
                continue
            for date in dates:
                date = current_date + timedelta(date)
                schedule.append({'city_from': city, 'date': date, 'city_to': city_to})
    return schedule


class UserState:
    """Состояние пользователья внутри сценария"""

    def __init__(self, scenario_name, step_name, context=None):
        self.scenario_name = scenario_name
        self.step_name = step_name
        self.context = context or {}


class Bot:
    """
    Echo bot для vk.com
    Use python 3.7
    """

    def __init__(self, group_id, token):
        """
        :param group_id: group id из группы ВК
        :param token: скрытый токен из той же группы
        """
        self.group_id = group_id
        self.token = token

        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)

        self.api = self.vk.get_api()
        self.user_states = dict()  # user_id -> UserState

    def run(self):
        """
        Запуск бота
        :return None
        """
        settings.SCHEDULE = flights_generator(settings.CITIES)

        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception as err:
                log.exception("ошибка в обработке события")

    def on_event(self, event: VkBotEventType):
        """
        Отправляет сообщение назад, если это текст
        :param event: VkBotMessageEvent object
        :return None
        """

        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info("мы пока не умеем обрабатывать событие такого типа %s", event.type)
            return

        user_id = event.message['from_id']
        text = str(event.message['text'])

        for intent in settings.INTENTS:
            log.debug(f'User gets {intent}')
            if any(token in text for token in intent['tokens']):
                if intent['answer']:
                    text_to_send = intent['answer']
                if user_id in self.user_states:
                    self.user_states.pop(user_id)

        if user_id in self.user_states:
            text_to_send = self.continue_scenario(user_id, text=text)

        else:
            # search intent
            for intent in settings.INTENTS:
                if any(token in text for token in intent['tokens']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                        break
                    else:
                        text_to_send = self.start_scenario(intent['scenario'], user_id)
                        break
            else:
                text_to_send = settings.DEFAULT_ANSWER

        self.send_message(text_to_send=text_to_send, user_id=user_id)

    def continue_scenario(self, user_id, text):
        state = self.user_states[user_id]
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])

        if handler(text=text, context=state.context) == 'next':
            # next step
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**state.context)

            if next_step['next_step']:
                # switch to next step
                state.step_name = step['next_step']
                return text_to_send

            else:
                # finish scenario
                log.info(
                    'Зарегистрировал {phone_number} {flight_chose}, мест - {places_quantity}'.format(**state.context))
                self.user_states.pop(user_id)
                return text_to_send

        elif handler(text=text, context=state.context) == 'retry':
            # retry current step
            text_to_send = step['failure_text'].format(**state.context)
            return text_to_send

        elif handler(text=text, context=state.context) == 'end':
            # finish scenario
            self.user_states.pop(user_id)
            # self.send_message('Напишите /ticket, если хотите повторить заказ', user_id)
            text_to_send = 'Напишите /ticket, если хотите повторить заказ'
            return text_to_send

    def send_message(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=randint(0, 2 ** 20),
            user_id=user_id)

    def start_scenario(self, scenario_name, user_id):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        self.user_states[user_id] = UserState(scenario_name=scenario_name, step_name=first_step)
        return text_to_send


if __name__ == '__main__':
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
