import requests
from bs4 import BeautifulSoup
import re

import telebot
from telebot import apihelper, types

# создаем "заглушку" для Ростелекома
# proxies = {
#
#     'http': 'http://80.250.14.236:41737',
#     'https': 'http://80.250.14.236:41737',
#
#     # 'http': 'http://167.86.96.4:3128',
#     # 'https': 'http://167.86.96.4:3128',
# }
#
# # и применяем "заглушку"
# apihelper.proxy = proxies

# подключаем бота, передава его токен
python_course_bot = telebot.TeleBot('992535871:AAGK5ES4auVfkV4F4cB0Dq1HXMxlitMaqBE')

# задаем путь к разделу Газеты сайта rbc.ru
url = 'https://www.rbc.ru/newspaper/?utm_source=topline'

# передаем в request путь и получаем в ответ содержимое сайта
response = requests.get(url)

# создаем экземпляр BeautifulSoup, передаем ему содержимое сайта
url_soup = BeautifulSoup(response.text, 'html.parser')

# создаем пустой словарь для хранения ссылок на статьи в разделе Газеты сайта rbc.ru
newspapers_dict = {}

# заполняем словарь ссылками, ища все ссылки, которые содержат подстроку http и newspaper
for each_url in url_soup.find_all('a', class_='newspaper-page__news'):
    if 'https' and 'newspaper' in str(each_url):
        newspapers_dict[' '.join(re.findall(r'\w+', each_url.get_text()))] = each_url.get('href')

# создаем словарь для хранения ссылки на статью и вложенного словаря
#  для хранения заголовка статьи, текста статьи, даты публикации статьи
text_data_dict = {}

# заполняем словарь ссылками на статью
for each_url in newspapers_dict.values():
    text_data_dict[each_url] = {
        'title': '',
        'text': '',
        'data': ''
    }

# в цикле
for each_url in newspapers_dict.values():

    # для каждой ссылки из словаря создаем экземпляр BeautifulSoup
    response_each_url = requests.get(each_url)
    each_url_soup = BeautifulSoup(response_each_url.text, 'html.parser')

    # для каждой ссылки заполняем словарь текстом статьи
    for element in each_url_soup.find_all('div', class_='article__content'):
        for text in element.find_all('p'):
            text_data_dict[each_url]['text'] += text.get_text()

    # для каждой ссылки заполняем словарь датой публикации статьи
    # [:-6] - в дате "отрезаем" часы и минуты
    for element in each_url_soup.find_all('span', class_='article__header__date'):
        text_data_dict[each_url]['data'] = ' '.join(re.findall(r'\w+', element.get_text()))[:-6]

    # для каждой ссылки заполняем словарь заголовком статьи
    for element in each_url_soup.find_all('span', class_='js-slide-title'):
        text_data_dict[each_url]['title'] = ' '.join(re.findall(r'\w+', element.get_text()))

    # из-за особенности rbc.ru (перед каждым символом "-" при парсинге) заменяем "\xa0" на пробел
    text_data_dict[each_url]['text'] = text_data_dict[each_url]['text'].replace('\xa0', ' ')

# создаем список для хранения дат публикаций всех статей
data_list = []

# в цикле заполняем список датами публикации всех статей
for each_key in text_data_dict.keys():
    if text_data_dict[each_key]['data'] not in data_list:
        data_list.append(text_data_dict[each_key]['data'])

# создаем уникальный список из дат публикации статей
unique_data_list = set(data_list)

# создаем изначально пустой список (для использования в дальнейшем)
# из ссылок на опубликованные статьи за выбранную пользователем дату
article_choice_list = []

# создаем обработчик команды start в боте
@python_course_bot.message_handler(commands=['start'])
def send_hello(message):
    python_course_bot.reply_to(message, 'Hello!')


@python_course_bot.message_handler(commands=['help'])
def send_help(message):
    help_string = 'Этот парсер выводит газетные статьи с rbc.ru' \
                  ' и позволяет делать выбор статьи сначала по дате ее публикации,' \
                  'затем выводит все статьи за выбранную дату'
    python_course_bot.reply_to(message, help_string)

# создаем обработчик команды rbc в боте
@python_course_bot.message_handler(commands=['rbc'])
def send_rbc(message):

    # выводим информационное сообщени
    python_course_bot.send_message(message.chat.id, 'Данный парсер выводит статьи из раздела Газеты сайта rbc.ru')

    python_course_bot.send_message(message.chat.id, 'Идет загрузка статей...')

    # выводим информационное сообщение об общем кол-ве статье в разделе Газеты сайта rbc.ru
    python_course_bot.send_message(message.chat.id,
                               'Сейчас в разделе Газеты сайта rb.cru {} статей'.format(len(text_data_dict.keys())))

    # создаем переменную для формирования стоки, состоящей из дат публикаций статей
    article_date_for_bot = ' '

    # выводим сообщение в чат
    python_course_bot.send_message(message.chat.id, 'Статьи публиковались: ')

    # заполняем строку датами публикаций статей и выводим в чат
    for unique_data in sorted(unique_data_list):
        article_date_for_bot += f'{sorted(unique_data_list).index(unique_data) + 1}.  {unique_data}\n'

    python_course_bot.reply_to(message, article_date_for_bot)

    # создаем экземпляр класса ReplyKeyboardMarkup
    # для обработки событий в чате
    markup = types.ReplyKeyboardMarkup(row_width=1)

    # создаем кол-во кнопок для выбора даты прочтения статей
    # равное кол-ву уникальных дат публикаций статей
    for data in sorted(unique_data_list):
        data_index = sorted(unique_data_list).index(data)
        markup.add(types.KeyboardButton(data_index + 1))

    # запрашиваем выбор пользователя в чате на выведенный
    # список дат публикаций статей
    data_choice = python_course_bot.send_message(message.chat.id,
                    'За какую дату вы хотели бы просмотреть список статей (введите номер)? ', reply_markup=markup)

    # "ловим" выбор пользователя, вызываем функцию data_choice_step
    # и передаем ей выбранную пользователем дату
    python_course_bot.register_next_step_handler(data_choice, data_choice_step)


# создаем функцию для вывода текста статьи в чат
# по выбранной пользователем дате
def data_choice_step(message):

    # # выводим уникальный список дат публикации статей в терминал
    # print('Статьи публиковались: ')
    # for published_date in sorted(unique_data_list):
    #     print(f'{sorted(unique_data_list).index(published_date) + 1}. ', published_date)

    # формируем индекс (по дате публикации выбранной пользователем)
    # для вывода списка статей по выбранной дате
    data_for_read = sorted(list(unique_data_list))[int(message.text) - 1]

    # выводим в чат список статей за выбранную пользователем дату
    python_course_bot.send_message(message.chat.id, f'Список статей за {data_for_read}:')

    # заполняем список (созданный в начале программы)
    # заголовками статей за выбранную дату
    # список предварительно очищаем, т.к. если на сервере программа запущена
    # на сервере, лист будет хранить "мусорные" значения для одного пользователя
    # при нескольких вызовах команды rbc
    article_choice_list.clear()
    # article_list_string = ''

    for each_key in text_data_dict.keys():
        if text_data_dict[each_key]['data'] == data_for_read:
            article_choice_list.append(each_key)
            list_number = article_choice_list.index(each_key)
            article_title = text_data_dict[each_key]['title']
            # article_list_string += f'{list_number + 1}. {article_title} .\n'
            # выводим в чат сообщение о запросе статьи, которую пользователь хотел бы прочитать
            # за выбранную дату
            python_course_bot.send_message(message.chat.id,
                                           f'{list_number + 1}. {article_title} .')

    # создаем экземпляр класса ReplyKeyboardMarkup
    # для обработки событий в чате
    markup = types.ReplyKeyboardMarkup(row_width=1)

    # создаем кол-во кнопок для выбора статьи для прочтения
    # равное кол-ву статей в списке за выбранную дату
    for article in article_choice_list:
        markup.add(types.KeyboardButton(article_choice_list.index(article) + 1))

    # запрашиваем выбор пользователя в чате на выведенный
    # список статей для прочтения
    article_choice = python_course_bot.send_message(message.chat.id,
                                    f'Какую статью за {data_for_read} Вы хотели бы прочитать? ', reply_markup=markup)

    # "ловим" выбор пользователя, вызываем функцию article_process_step
    # и передаем ей выбранную пользователем статью для прочтения
    python_course_bot.register_next_step_handler(article_choice, article_process_step)


def article_process_step(message):

    # формируем индекс (по дате публикации выбранной пользователем)
    # для вывода текста статьи по выбранной дате
    url_for_read = article_choice_list[int(message.text) - 1]

    # выводим в чат список ссылку и саму статью для прочтения
    python_course_bot.send_message(message.chat.id, 'Ссылка на статью на сайте: ')
    python_course_bot.send_message(message.chat.id, url_for_read)
    # python_course_bot.send_message(message.chat.id, 'Текст статьи: ')
    # python_course_bot.send_message(message.chat.id, text_data_dict[url_for_read]['text'])



# запускаем непрерывное процесс приема/отправки сообщений бота
python_course_bot.polling()


