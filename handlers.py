"""
Handler - функция, которая принимает на вход text(текст входящего сообщения) и context (dict), а возвращает bool:
True если шаг пройден, False если данные введены неправльно.
"""
import re
from datetime import datetime
from operator import itemgetter

import settings


def five_flights(flights, city_from, city_to, date):
    date = datetime.strptime(date, '%d-%m-%Y').date()
    the_flight = {'city_from': city_from, 'date': date, 'city_to': city_to}

    flights = sorted(flights, key=itemgetter('date'))

    if len(flights) < 6:
        return flights

    elif len(flights) == 0:
        return "non"
    else:
        flights.append(the_flight)
        flights = sorted(flights, key=itemgetter('date'))

        while len(flights) > 6:
            if abs(flights[0]['date'] - the_flight['date']).days < abs(flights[-1]['date'] - the_flight['date']).days:
                flights.pop(flights.index(flights[-1]))
            else:
                flights.pop(flights.index(flights[0]))

        flights.pop(flights.index(the_flight))
        return flights


def dispatcher(schedule, city_from, city_to, date):
    suitable_flights = []

    for flight in schedule:
        if flight['city_from'] == city_from and flight['city_to'] == city_to:
            suitable_flights.append(flight)

    str_flight = ''
    iterator = 1
    suitable_flights = five_flights(suitable_flights, city_from=city_from, city_to=city_to, date=date)

    for flight in suitable_flights:
        str_flight += f"{iterator}){flight['city_from']} {flight['date']} {flight['city_to']} " + '\n'
        iterator += 1

    return suitable_flights, str_flight


def handle_city_from(text, context):
    match = re.match(r'[Пп]итер|[Мм]оскв\w|[Тт]окио|[Вв]аршав\w', text)
    text = text.capitalize()
    if match:
        context['city_from'] = text
        return 'next'
    else:
        return 'retry'


def handle_to_city(text, context):
    match = re.match(r'[Пп]итер|[Мм]оскв\w|[Тт]окио|[Вв]аршав\w', text)
    text = text.capitalize()
    if match:
        context['city_to'] = text
        return 'next'
    else:
        return 'retry'


def handle_date(text, context):
    match = re.match(r'\d{2}-\d{2}-\d{4}', text)
    if match:
        context['date'] = text
        context['suitable_flights'], context['suitable_flights_str'] = dispatcher(schedule=settings.SCHEDULE,
                                                                                  city_from=context['city_from'],
                                                                                  city_to=context['city_to'],
                                                                                  date=context['date'])
        return 'next'
    else:
        return 'retry'


def handle_number(text, context):
    match = re.match(r'\d+', text)
    if match:
        context['phone_number'] = text
        return 'next'
    else:
        return 'retry'


def handle_flight_chose(text, context):
    match = re.match(r'\d', text)

    if match and (0 < int(text) <= len(context['suitable_flights'])):
        flight_chose = context['suitable_flights'][int(text) - 1]
        context['flight_chose'] = f"Город отправления - {flight_chose['city_from']}," \
                                  f" город прибытия - {flight_chose['city_to']}," \
                                  f" дата - {flight_chose['date']}"

        return 'next'
    else:
        return 'retry'


def handle_places(text, context):
    match = re.match(r'\d', text)
    if match:
        if 0 < int(text) < 6:
            context['places_quantity'] = text
            return 'next'
        else:
            return 'retry'
    else:
        return 'retry'


def handle_comment(text, context):
    if text:
        context['comment'] = text
        return 'next'
    else:
        return 'retry'


def handle_all_data(text, context):
    if text == 'да':
        return 'next'
    elif text == 'нет':
        return 'end'
    else:
        return 'retry'
