# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import os
import json

'''
Программа с сохранением запросов, при запросе с другими параметрами файл дозапишется.
При одинаковых параметрах должна проводиться проверка на то, что записываемые данные уникальны, 
но структура данных записываемых в json файл и структура доставаемая из файла различаются. 
Пока победить данную проблему не получилось. Как вариант можно задавать файлу при записи временной штамп. 
Это позволит избежать такой проблемы, а при анализе данных в pandas просто сливать таблицы с проверкой на уникальность.

По умолчанию сейвит данные в папку где находится сам файл 'HomeWork_2.py'.
Изменить адрес сохранения файла можно в переменной 'file_path'.

Название сохраняемого файла менеяется в переменной 'file_name'

Родительская ссылка в переменной 'url', Но при смене ссылки, работа всей программы может вызвать ошибки, 
если верстка другого сайта будет отличаться от 'hh.ru'
'''

# https://hh.ru/search/vacancy?area=1&fromSearchLine=true&text=python
file_name = 'job.json'
file_path = os.getcwd() + '\\'

url = 'https://hh.ru'  # Не менять!!!!

# Params for default request
params = {'area': 1,  # 1 - Moscow, 2 - Piter
          'text': 'python',
          'page': 0
          }

# User-Agent
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/74.0.3729.169 Safari/537.36'}


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
    data_list = []
    for job in req:
        job_data = {}
        info = job.find('a')
        name = info.text.replace('\u200e', '')
        link = info.get('href')
        salary = job.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
        if not salary:
            salary_min = None
            salary_max = None
            salary_currency = None
        else:
            salary_fork = [i for i in salary.contents if i != ' ']
            if len(salary_fork) == 3:
                if salary_fork[0] == 'от ':
                    salary_min = int(salary_fork[1].replace('\u202f', '').replace('–', ''))
                    salary_max = None
                elif salary_fork[0] == 'до ':
                    salary_max = int(salary_fork[1].replace('\u202f', '').replace('–', ''))
                    salary_min = None
                salary_currency = salary_fork[2]
            elif len(salary_fork) == 2:
                salary_min = int(salary_fork[0].replace('\u202f', '').replace('–', '').split('  ')[0])
                salary_max = int(salary_fork[0].replace('\u202f', '').replace('–', '').split('  ')[1])
                salary_currency = salary_fork[1]
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
        employer = job.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).text
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
        data_list.append(job_data)
    return data_list


def make_request(data, update, area=None, text=None):
    """
    Функция делающая запрос по ссылке и вызывает обработку данных описанных в функции 'get_data()'
    Функция зациклена пока не пройдет все доступные страницы поискового запроса.
    :param data: Данные, в которые будет производиться запись или обновление значений. Type: 'list'
    :param update: Значения для запуска проверки на уникальность значений (пока в доработке). Type: 'bool'
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
    job_data = get_data(jobs)
    if update is True:
        data.append([i for i in job_data if i not in data])
    else:
        data.append(job_data)
    next_btn = soup.find('a', {'data-qa': 'pager-next'})
    print(params['page'])
    if not next_btn:
        return
    else:
        params['page'] += 1
        make_request(data, update)


def update_data(f_name, f_path):
    """
    Функция записи и обновления файла. Вызывает функцию 'make_request'
    Обновление файла с тем же поисковым запросом !НЕ РАБОТАЕТ!
    :param f_name: Название файла. Type: 'str'
    :param f_path: Адрес расположения файла. Type: 'str'
    :return: None
    """
    file = f_path + f_name
    if os.path.exists(file) is False:
        jobs_list = []
        make_request(jobs_list, False)
        with open(file, 'w') as fw:
            json.dump(jobs_list, fw)
        print(f'File {f_name} in {f_path} created')
        print(jobs_list)
    else:
        with open(file, 'r+') as fw:
            jobs_update = json.load(fw)
            print(jobs_update)
            make_request(jobs_update, True)
        with open(file, 'w') as fw:
            json.dump(jobs_update, fw)
        print(f'File {f_name} in {f_path} updated')
    return


def init():
    update_data(file_name, file_path)


init()
