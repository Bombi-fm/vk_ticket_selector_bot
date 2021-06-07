from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from vk_api.bot_longpoll import VkBotMessageEvent, VkBotEventType
from freezegun import freeze_time

from bot import Bot
import settings
from handlers import dispatcher


@freeze_time("2021-05-31")
class Test1(TestCase):
    RAW_EVENT = {'type': 'message_new', 'object': {
        'message': {'date': 1622287311, 'from_id': 125641735, 'id': 721, 'out': 0, 'peer_id': 125641735, 'text': '[fq',
                    'conversation_message_id': 721, 'fwd_messages': [], 'important': False, 'random_id': 0,
                    'attachments': [], 'is_hidden': False}, 'client_info': {
            'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback', 'intent_subscribe',
                               'intent_unsubscribe'], 'keyboard': True, 'inline_keyboard': True, 'carousel': True,
            'lang_id': 0}}, 'group_id': 191030326, 'event_id': '2aeece9e1943d55a6de83c049b9ee981908b9fb8'}

    def test_run(self):
        count = 5
        events = [{}] * count  # [{}, {},  ...]
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock
        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call({})
                assert bot.on_event.call_count == count

    INPUTS = [
        '/ticket',
        'москва',
        'питер',
        '06-06-2021',
        '4',
        '3',
        'nah',
        'да',
        '89115553366'
    ]
    OUTPUTS = {
        'suitable_flights_str': '1)Москва 2021-06-01 Питер \n2)Москва 2021-06-05 Питер \n3)Москва 2021-06-13 Питер '
                                '\n4)Москва 2021-06-15 Питер \n5)Москва 2021-06-17 Питер \n',
        'flight_chose': 'Город отправления - Москва, город прибытия - Питер, дата - 2021-06-15',
        'places_quantity': '3',
        'phone_number': '89115553366'}

    EXPECTED_OUTPUTS = [
        settings.SCENARIOS['booking']['steps']['step1']['text'],
        settings.SCENARIOS['booking']['steps']['step2']['text'],
        settings.SCENARIOS['booking']['steps']['step3']['text'],
        settings.SCENARIOS['booking']['steps']['step4']['text'].format(**OUTPUTS),
        settings.SCENARIOS['booking']['steps']['step5']['text'],
        settings.SCENARIOS['booking']['steps']['step6']['text'],
        settings.SCENARIOS['booking']['steps']['step7']['text'].format(**OUTPUTS),
        settings.SCENARIOS['booking']['steps']['step8']['text'],
        settings.SCENARIOS['booking']['steps']['step9']['text'].format(**OUTPUTS)
    ]

    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])

        assert real_outputs == self.EXPECTED_OUTPUTS
