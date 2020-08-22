import telebot
import pandas as pd
import datetime
from flask import Flask, request
import os
from help_funcs import give_text

TOKEN = "<YOUR_TOKEN>"
HEROKU_WEB_URL = "<YOUR_HEROKU_WEB_URL>"
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

df = pd.read_excel("schedule3.xlsx")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    send_message = f"Привет, {message.from_user.first_name}! Добро пожаловать!"
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(commands=["help"])
def send_help(message):
    send_message = f"Для получения расписания следуйте инструкции: \n1. Отправьте любое сообшение боту (не из списка специальных команд). \n2. Введите номер группы. \n3. Введите нужный день недели."
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(commands=["groups"])
def send_groups_list(message):
    send_message = sorted(set(df["группа"]))
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(commands=["week"])
def give_week(message):
    today = datetime.date.today()
    week = today.isocalendar()[1]
    send_message = "Сейчас идет {}-я учебная неделя".format(week)
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(commands=["today"])
def give_today(message):
    today = datetime.date.today()
    data = today.strftime("%d/%m/%Y")
    send_message = "Сегодня {}".format(data)
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(content_types=["text"])
def start_request(message):

    msg = bot.send_message(message.chat.id, "Введите номер группы.", parse_mode="html")
    bot.register_next_step_handler(msg, get_group) 
    
@bot.message_handler(content_types=["text"])
def get_group(message):

    global group
    group = message.text.strip().lower()

    if message.text.strip().lower() == "stop" or message.text.strip().lower() == "стоп":
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    elif group in set(df["группа"]):
        msg2 = bot.send_message(message.chat.id, "Введите нужный день недели.", parse_mode="html")
        bot.register_next_step_handler(msg2, get_day) 
    else:
        msg2 = bot.send_message(message.chat.id, "Такой группы нет!", parse_mode="html")
        bot.register_next_step_handler(msg2, get_group) 

        
@bot.message_handler(content_types=["text"])
def get_day(message):

    day_of_week = message.text.strip().lower()

    today = datetime.date.today()
    week = today.isocalendar()[1]

    day_dict = {0: "понедельник",  
                1: "вторник", 
                2: "среда", 
                3: "четверг", 
                4: "пятница", 
                5: "суббота", 
                6: "воскресенье"}
    day_list = list(day_dict.values())

    future_day_dict = {"вчера": -1,
                       "сегодня": 0,
                       "завтра": 1,
                       "послезавтра": 2,
                       "послепослезавтра": 3}
    future_day_list = list(future_day_dict.keys())

    if message.text.strip().lower() == "stop" or message.text.strip().lower() == "стоп":
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)

    elif day_of_week in future_day_list:

        today = datetime.date.today()
        today += datetime.timedelta(days=future_day_dict[day_of_week])
        day_of_week = today.weekday()
        day_of_week = day_dict[day_of_week]
        week = today.isocalendar()[1]

        final_message = df[(df["группа"] == group) & (df["день недели"] == day_of_week) & (df["неделя"] == week)].loc[:, ["время", "предмет"]]
        final_data = give_text(final_message)

        bot.send_message(message.chat.id, final_data)

    elif day_of_week in day_list:

        final_message = df[(df["группа"] == group) & (df["день недели"] == day_of_week) & (df["неделя"] == week)].loc[:, ["время", "предмет"]]
        final_data = give_text(final_message)

        bot.send_message(message.chat.id, final_data)

    elif day_of_week not in future_day_list and day_of_week not in day_list:
        msg3 = bot.send_message(message.chat.id, "Введите дату правильно!")
        bot.register_next_step_handler(msg3, get_day) 


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=HEROKU_WEB_URL + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))


bot.polling(none_stop=True)
