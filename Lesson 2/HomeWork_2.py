# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import os
import re
from pymongo import MongoClient
from pymongo.errors import *

'''
Программа с сохранением запросов в базу данных MongoDB, при обновлении БД дозапишется.
Программа добавляет уникальные id вакансий. При обновлении пишется сколько вакансий было добавлено в БД.

Если БД не существует, при первом запуске программа создаст коллекцию и заполнит ее.
После предоставит выбор пользователю относительно последующих действий.

Программа автоматически конвертирует валюты отличные от "руб", актуальный курс берет из google.ru.

При поиске программа выводит результат в форматированном виде, а так же кол-во найденных вакансий.

Родительская ссылка в переменной 'url', Но при смене ссылки, работа всей программы может вызвать ошибки, 
если верстка другого сайта будет отличаться от 'hh.ru'
'''

# https://hh.ru/search/vacancy?area=1&fromSearchLine=true&text=python
# file_name = 'job_2.json'
# file_path = os.getcwd() + '\\'

url = 'https://hh.ru'  # Не менять!!!!

# Params for default request
params = {'area': 1,  # 1 - Moscow, 2 - Piter
          'text': 'python',
          'page': 0,
          'items_on_page': 20
          }

# User-Agent
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/74.0.3729.169 Safari/537.36'}

# Mongo DB
client = MongoClient('127.0.0.1', 27017)

db = client['HH_jobs']

jobs_collection = db.jobs

'''
Структура данных проекта:
{'_id': 'job_id',
 'название':'name',
 'работодатель': 'employer',
 'город': 'city',
 'метро': 'metro',
 'минимальная зарплата': 'salary_min',
 'максимальная зарплата': 'salary_max',
 'валюта зарплаты': 'salary_currency',
 'день размещения вакансии': 'vac_day',
 'месяц размещения вакансии': 'vac_month'
} 
'''
job_counter = {'count': 0}
currency_val = {'USD': 0,
                'EUR': 0
                }


def check_currency():
    usd_resp = requests.get('https://www.google.com/search?q=%D0%BA%D1%83%D1%80%D1%81+%D0%B4%D0%BE%D0%BB%D0%BB%D0%B0'
                             '%D1%80%D0%B0', headers=headers)
    eur_resp = requests.get('https://www.google.com/search?q=%D0%BA%D1%83%D1%80%D1%81+%D0%B5%D0%B2%D1%80%D0%BE',
                            headers=headers)
    usd_soup = BeautifulSoup(usd_resp.text, 'html.parser')
    eur_soup = BeautifulSoup(eur_resp.text, 'html.parser')
    usd = float(usd_soup.find('div', {'class': "b1hJbf"}).get('data-exchange-rate'))
    eur = float(eur_soup.find('div', {'class': "b1hJbf"}).get('data-exchange-rate'))
    currency_val['USD'] = round(usd, 2)
    currency_val['EUR'] = round(eur, 2)


def delete_char(data):
    char_list = ['\u200e', '\u0138', '\u200c', '\u202f', '\xa0']
    right_data = data
    for c in char_list:
        if c == '\xa0':
            right_data = right_data.replace(c, ' ')
        else:
            right_data = right_data.replace(c, '')
    return right_data


def get_data(req):
    """Функция ищет и адаптирует данные полученные из обязательного аргумента 'req'
       Сейчас формируются данные о:
       - Названии вакансии 'name'
       - Названии компании работодателя 'employer'
       - Города, в котором размещена вакансия 'city'
       - (При наличии) Станция метро 'metro'
       - Ссылка на подробное описание вакансии 'link'
       - Зарплата записывается в трех показателях (минимальная зарплата 'salary_min',
         максимальная зарплата 'salary_max', валюта 'salary_currency'. Если один из параметров не указан,
         то недостающие параметры принимают значение 'None'
       - День размещения вакансии 'vac_day'
       - Месяц размещения вакансии 'vac_month
       На вывод функции идет список словарей, каждый элемент списка является данными по отдельной вакансии
    """
    for job in req:
        job_data = {}
        info = job.find('a')
        job_id = re.search(r"\d{1,50}", info.get('href')).group(0)
        name = delete_char(info.text)
        link = 'https://hh.ru/vacancy/' + job_id
        salary = job.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
        if not salary:
            salary_min = None
            salary_max = None
            salary_currency = None
        else:
            salary_fork = [i for i in salary.contents if i != ' ']
            if len(salary_fork) == 3:
                if salary_fork[0] == 'от ':
                    salary_min = int(delete_char(salary_fork[1]).replace('–', ''))
                    salary_max = None
                elif salary_fork[0] == 'до ':
                    salary_max = int(delete_char(salary_fork[1]).replace('–', ''))
                    salary_min = None
                salary_currency = salary_fork[2]
                if salary_currency == 'USD':
                    if salary_min is not None:
                        salary_min = int(salary_min*currency_val['USD'])
                    if salary_max is not None:
                        salary_max = int(salary_max*currency_val['USD'])
                    salary_currency = 'руб.'
                elif salary_currency == 'EUR':
                    if salary_min is not None:
                        salary_min = int(salary_min*currency_val['EUR'])
                    if salary_max is not None:
                        salary_max = int(salary_max*currency_val['EUR'])
                    salary_currency = 'руб.'
            elif len(salary_fork) == 2:
                salary_min = int(delete_char(salary_fork[0]).replace('–', '').split('  ')[0])
                salary_max = int(delete_char(salary_fork[0]).replace('–', '').split('  ')[1])
                salary_currency = salary_fork[1]
                if salary_currency == 'USD':
                    salary_min = int(salary_min*currency_val['USD'])
                    salary_max = int(salary_max*currency_val['USD'])
                    salary_currency = 'руб.'
                elif salary_currency == 'EUR':
                    salary_min = int(salary_min*currency_val['EUR'])
                    salary_max = int(salary_max*currency_val['EUR'])
                    salary_currency = 'руб.'
            else:
                print(f'Wrong data = {salary_fork}')
                salary_min = None
                salary_max = None
                salary_currency = None
        location = job.find('div', {'data-qa': 'vacancy-serp__vacancy-address'}).text
        if ',' in location:
            city_metro = location.split(',')
            city = city_metro[0]
            metro = city_metro[1]
        else:
            city = location
            metro = None
        employer = delete_char(job.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).text)
        vac_date_search = job.find('span', {'data-qa': 'vacancy-serp__vacancy-date'})
        if not vac_date_search:
            vac_day = None
            vac_month = None
        else:
            vac_date = vac_date_search.text
            if vac_date.count('.') == 2:
                vac_date_list = vac_date[-10::].split('.')
                vac_day = vac_date_list[0]
                vac_month = vac_date_list[1]
            elif vac_date.count('.') == 1:
                vac_date_list = vac_date[-5::].split('.')
                vac_day = vac_date_list[0]
                vac_month = vac_date_list[1]
            else:
                print(vac_date)
                vac_day = None
                vac_month = None
        job_data['_id'] = job_id
        job_data['name'] = name
        job_data['employer'] = employer
        job_data['city'] = city
        job_data['metro'] = metro
        job_data['link'] = link
        job_data['salary_min'] = salary_min
        job_data['salary_max'] = salary_max
        job_data['salary_currency'] = salary_currency
        job_data['vac_day'] = vac_day
        job_data['vac_month'] = vac_month
        # Проверяем данные на символы HTML, при ошибке символов, раскомментировать код ниже
        # print(job_data['name'])
        # print(job_data['employer'])
        # print(job_data['city'])
        # print(job_data['metro'])
        # print(job_data['link'])
        # print(job_data['salary_min'])
        # print(job_data['salary_max'])
        # print(job_data['salary_currency'])
        # print(job_data['vac_day'])
        # print(job_data['vac_month'])
        try:
            jobs_collection.insert_one(job_data)  # Сохраняем данные в БД
            job_counter['count'] += 1
        except DuplicateKeyError:
            # print('Вакансия уже добавлена в базу')
            pass
    return


def make_request(area=None, text=None):
    """
    Функция делающая запрос по ссылке и вызывает обработку данных описанных в функции 'get_data()'
    Функция зациклена пока не пройдет все доступные страницы поискового запроса.
    :param area: Аргумент выбора города. (Значения найденые на сайте описап в коментарии к 'params') Type: 'int'
    :param text: Аргумент поиского запроса. Type: 'str'
    :return: None
    """
    if area is not None:
        params['area'] = area
    if text is not None:
        params['text'] = text
    response = requests.get(url + '/search/vacancy', params=params, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = soup.find_all('div', {'class': 'vacancy-serp-item'})
    get_data(jobs)
    next_btn = soup.find('a', {'data-qa': 'pager-next'})
    print(f'Загрузка данных: {params["page"]}%')
    if not next_btn:
        print(f"Загрузка завершена. Добавлено {job_counter['count']} вакансий.")
        print('----------------')
        return
    else:
        params['page'] += 1
        make_request()


def search_vacancy(val):
    result = jobs_collection.find({'$or': [{'salary_min': {'$gte': val}}, {'salary_max': {'$gte': val}}]})
    for doc in result:
        print('----------------')
        print(doc['name'])
        print(doc['employer'])
        print(doc['city'])
        print(doc['link'])
        if doc['salary_max'] is not None and doc['salary_min'] is not None:
            print(f"от {doc['salary_min']} до {doc['salary_max']} руб.")
        if doc['salary_min'] is not None:
            print(f"от {doc['salary_min']} руб.")
        if doc['salary_max'] is not None:
            print(f"до {doc['salary_max']} руб.")

        print(doc['salary_currency'])
        print('----------------')
    print(f"Найдено {jobs_collection.count_documents({'$or': [{'salary_min': {'$gte': val}}, {'salary_max': {'$gte': val}}]})} вакансий.")
    print('----------------')


def init():
    if jobs_collection.count_documents({}) == 0:
        make_request()
        init()
    print(f'На текущий момент в базе {jobs_collection.count_documents({})} вакансий.\n'
          f'"1" - Произвести поиск по базе, задав значение заработной платы\n'
          f'"2" - Обновить значения в базе данных\n'
          f'"3" - Удалить базу данных\n'
          f'"Any" - Выход из программы'
          )
    answer = input('Введите число: ')
    if answer == '1':
        salary_val = input('Введите размер зарплаты в рублях: ')
        search_vacancy(int(salary_val))
    elif answer == '2':
        make_request()
        init()
    elif answer == '3':
        ask = input('Вы точно хотите удалить базу данных? Yes/No: ')
        if ask == 'Yes':
            jobs_collection.delete_many({})
            print('База данных удалена')
        else:
            init()
    else:
        return


check_currency()
init()
