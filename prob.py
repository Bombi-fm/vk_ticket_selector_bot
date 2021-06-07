from datetime import datetime, timedelta
from random import randint

citys = ['Москва', 'Питер', 'Варашава', 'Токио']


def flights_generato(citys):
    schedule = []
    dates = [1, 5, 13, 15, 17, 23, 28]
    current_date = datetime.now().date()
    print(current_date)
    for city in citys:
        for city_to in citys:
            if city == city_to:
                continue
            for date in dates:
                date = current_date + timedelta(date)
                schedule.append({'city_from': city, 'date': date, 'city_to': city_to})
    return schedule


aga = flights_generato(citys)

for g in aga:
    print(g)

