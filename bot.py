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
    send_message = f"Привет, {message.from_user.first_name}! Добро пожаловать! Для получения инструкции нажмите /help"
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(commands=["help"])
def send_help(message):
    send_message = f"Инструкция: \n1. Отправьте любое сообшение боту \n2. Введите название группы \n3. Введите нужный день текущей недели \n \n<b>Специальные команды</b> \nСписок доступных групп:  /groups \nТекущая дата:  /today \n"
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(commands=["groups"])
def send_groups_list(message):
    send_message = "<b>Список доступных групп бота: </b>" + "\n" + "\n" + "\n".join(sorted(set(df["группа"])))
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(commands=["today"])
def give_today(message):
    today = datetime.date.today()
    week = today.isocalendar()[1]-35
    data = today.strftime("%d.%m.%Y")
    day_dict = {1: "понедельник",  
                2: "вторник", 
                3: "среда", 
                4: "четверг", 
                5: "пятница", 
                6: "суббота", 
                7: "воскресенье"}
    day_list = list(day_dict.values())
    day_dt = today.isocalendar()[2]
    day_of_weeek = day_dict[day_dt]    
    send_message = "Сегодня {}".format(day_of_weeek) + ", " + "{}".format(data) + ", "+ "{}-я учебная неделя".format(week)
    bot.send_message(message.chat.id, send_message, parse_mode="html")


@bot.message_handler(content_types=["text"])
def start_request(message):
    msg = bot.send_message(message.chat.id, "Введите название группы", parse_mode="html")
    bot.register_next_step_handler(msg, get_group) 

    
@bot.message_handler(content_types=["text"])
def get_group(message):

    global group
    group = message.text.strip().lower()

    if message.text.strip().lower() == "/stop" or message.text.strip().lower() == "стоп":
        msg2 = bot.send_message(message.chat.id, "Чат сброшен. \nСписок доступных групп: /groups", parse_mode="html")
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)           
                
    elif group in set(df["группа"]):
        msg2 = bot.send_message(message.chat.id, "Введите нужный день недели \nДля ввода точной даты нажмите /date", parse_mode="html")
        bot.register_next_step_handler(msg2, get_day) 
    else:
        msg2 = bot.send_message(message.chat.id, "Такой группы нет! \nДля сброса чата нажмите /stop", parse_mode="html")
        bot.register_next_step_handler(msg2, get_group) 

        
@bot.message_handler(content_types=["text"])
def get_day(message):

    day_of_week = message.text.strip().lower()

    today = datetime.date.today()
    week = today.isocalendar()[1]-35

    day_dict = {0: "понедельник",  
                1: "вторник", 
                2: "среда", 
                3: "четверг", 
                4: "пятница", 
                5: "суббота", 
                6: "воскресенье"}
    day_list = list(day_dict.values())

    future_day_dict = {"сегодня": 0,
                       "завтра": 1,
                       "послезавтра": 2}
    future_day_list = list(future_day_dict.keys())

    if message.text.strip().lower() == "/stop" or message.text.strip().lower() == "стоп":
        msg3 = bot.send_message(message.chat.id, "Чат сброшен. \nДля получения инструкции нажмите /help \n", parse_mode="html")        
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)

    elif day_of_week in future_day_list:

        today = datetime.date.today()
        today += datetime.timedelta(days=future_day_dict[day_of_week])
        week = today.isocalendar()[1]-35
        if today.isocalendar()[2] > 6:
            today = today - 7
            week = week + 1
        day_of_week = today.weekday()
        day_of_week = day_dict[day_of_week]
        final_message = df[(df["группа"] == group) & (df["день недели"] == day_of_week) & (df["неделя"] == week)].loc[:, ["время", "предмет"]]
        final_data = give_text(final_message)

        bot.send_message(message.chat.id, final_data)

    elif day_of_week in day_list:
        week = today.isocalendar()[1]-35
        data = today.strftime("%d.%m.%Y")
        final_message = df[(df["группа"] == group) & (df["день недели"] == day_of_week) & (df["неделя"] == week)].loc[:, ["время", "предмет"]]
        final_data = give_text(final_message)

        bot.send_message(message.chat.id, final_data)

    elif message.text.strip().lower() == "/date":
        msg3 = bot.send_message(message.chat.id, "Введите дату в формате дд.мм.гг (01.09.20)")
        bot.register_next_step_handler(msg3, get_date)
        
    elif day_of_week not in future_day_list and day_of_week not in day_list and message.text.strip().lower() != "/date":
        msg3 = bot.send_message(message.chat.id, "Введите день недели корректно! \nДля сброса чата нажмите /stop ")
        bot.register_next_step_handler(msg3, get_day) 


@bot.message_handler(content_types=["text"])
def get_date(message):

    day_dict = {1: "понедельник",  
                2: "вторник", 
                3: "среда", 
                4: "четверг", 
                5: "пятница", 
                6: "суббота", 
                7: "воскресенье"}
    
    day_list = list(day_dict.values())
    if message.text.strip().lower() == "/stop" or message.text.strip().lower() == "стоп":
        msg4 = bot.send_message(message.chat.id, "Чат сброшен. \nДля получения инструкции нажмите /help \n", parse_mode="html")        
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)

    elif message.text.strip().lower() != "/stop" or message.text.strip().lower() != "стоп":
        date_time_str = message.text.strip().lower()
        try:
            date_time_obj = datetime.datetime.strptime(date_time_str, '%d.%m.%y')
        except ValueError:
            msg4 = bot.send_message(message.chat.id, "Введите дату корректно! \nДоступный промежуток: 01.09.20-31.12.20 \nДля сброса чата нажмите /stop ")
            bot.register_next_step_handler(msg4, get_date) 
            return date_time_str          
        week_dt = date_time_obj.isocalendar()[1]-35
        day_dt = date_time_obj.isocalendar()[2]
        day_of_weeek = day_dict[day_dt]
        final_message = df[(df["группа"] == group) & (df["день недели"] == day_of_weeek) & (df["неделя"] == week_dt)].loc[:, ["время", "предмет"]]
        final_data = give_text(final_message)

        bot.send_message(message.chat.id, final_data)
        bot.send_message(message.chat.id, "Нажмите /start", parse_mode="html")


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
