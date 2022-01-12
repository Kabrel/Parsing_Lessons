# -*- coding: utf-8 -*-
from lxml import html
from datetime import datetime
import requests
import asyncio
from pymongo import MongoClient
from pymongo.errors import *
import itertools
import re

# User-Agent
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/74.0.3729.169 Safari/537.36'}
# Web params
url = 'https://news.mail.ru/'

# Mongo DB
client = MongoClient('127.0.0.1', 27017)
db = client['Mail_ru_News']
news_collection = db.news

# Functions


def delete_char(data):
    """
    Function deletes html symbols from data
    :param data: str
    :return: str
    """
    char_list = ['\u200e', '\u0138', '\u200c', '\u202f', '\xa0', '© ']
    right_data = data
    for c in char_list:
        if c == '\xa0':
            right_data = right_data.replace(c, ' ')
        else:
            right_data = right_data.replace(c, '')
    return right_data


def save_to_db(data):
    """
    Function save data to MongoDB
    :param data: vocabulary
    :return: None
    """
    try:
        news_collection.insert_one(data)  # Сохраняем данные в БД
    except DuplicateKeyError:
        # print('Вакансия уже добавлена в базу')
        pass


def get_news_url(data):
    """
    Function retrieves urls from main page
    :param data: html.fromstring (lxml)
    :return: list
    """
    news_data = data.xpath("//td[contains(@class, 'daynews') and not(contains(@class,'spring'))]")
    news_data.append(data.xpath("//td[contains(@class,'daynews')]/../../../../..//li[not(contains(@class,'hidden'))]"))
    url_data = list(itertools.chain(*news_data))
    url_list = [item.xpath("./a/@href")[0] for item in url_data]
    return url_list


def get_news(link):
    """
    Function retrieves data from url and organizes the data
    :param link: str
    :return: None
    """
    news = {}
    data = requests.get(link, headers=headers)
    page = html.fromstring(data.text)
    news_id = re.search(r"\d{1,50}", link).group(0)
    page_data = page.xpath("//div[contains(@data-news-id,{})]".format(news_id))
    try:
        name = delete_char(page_data[0].xpath(".//h1/text()")[0])
        info = delete_char(page_data[0].xpath(".//p/text()")[0])
        source = delete_char(page_data[0].xpath(".//span[contains(@class,'link__text')]/text()")[0])
        date_iso = page_data[0].xpath(".//span[contains(@class,'js-ago')]/@datetime")[0]
        date_data = datetime.fromisoformat(date_iso[:-6])
        year = date_data.date().year
        month = date_data.date().month
        day = date_data.date().day
        hour = date_data.time().hour
        minute = date_data.time().minute
        news['_id'] = news_id
        news['url'] = link
        news['name'] = name
        news['info'] = info
        news['source'] = source
        news['year'] = year
        news['month'] = month
        news['day'] = day
        news['hour'] = hour
        news['minute'] = minute
        print(news)
        save_to_db(news)
    except:
        print("ERORRR~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(link)
        print(page_data[0].xpath(".//h1/text()"))
        print("ERORRR~~~~~~~~~~~~~~~~~~~~~~~~~~~")


def init():
    """
    Program nit function
    :return: None
    """
    response = requests.get(url, headers=headers)
    dom = html.fromstring(response.text)
    news_url = get_news_url(dom)
    for i in news_url:
        get_news(i)


# Body code
init()
