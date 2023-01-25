import telebot
import sqlite3
import replicate
import os

TOKEN = '5873640811:AAFvljGqovEOIEu3LDBHHyMRXQi5mPm6GLw'

con = sqlite3.connect("user.db", check_same_thread=False)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS user (id integer unique, token text)")

con.commit()

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
  bot.send_message(message.chat.id,'''Добро пожаловать! 
Я - ваш личный бот-художник, готовый создать для вас уникальное изображение по вашему запросу. 
Чтобы начать, просто напишите мне что-нибудь, и я с радостью воплощу вашу идею в живописную картину!''')

@bot.message_handler(content_types=['text'])
def s(message):
    res = cur.execute(f"SELECT token, id FROM user WHERE id={message.chat.id}")
    g = res.fetchone()
    if (g is None):
        bot.send_message(message.chat.id, '''Вам нужно зарегистрироваться на данном сайте 
(https://replicate.com/account), 
скопировать токен и вставить его сюда:''')
        photo = open('img.jpg', 'rb')
        bot.send_photo(message.chat.id, photo)
        bot.register_next_step_handler(message, set_token)
    else:
        if ('/change' in message.text):
            change_token(message)
        elif ('/info' in message.text):
            info_token(message, g[0])
        else:
            os.environ["REPLICATE_API_TOKEN"] = g[0]
            create_img(message)

def create_img(message):
    try:
        bot.send_message(message.chat.id, 'Создаю картинку. Подождите...')
        model = replicate.models.get("stability-ai/stable-diffusion")
        version = model.versions.get("f178fa7a1ae43a9a9af01b833b9d2ecf97b1bcb0acfd2dc5dd04895e042863f1")
        inputs = {
            'prompt': message.text,
            'width': 512,
            'height': 512,
            'prompt_strength': 0.8,
            'num_outputs': 1,
            'num_inference_steps': 50,
            'guidance_scale': 7.5,
            'scheduler': "DPMSolverMultistep",
        }
        output = version.predict(**inputs)
        bot.send_photo(message.chat.id, output[0])
    except Exception as err:
        bot.send_message(message.chat.id, 'Неправильный токен. Чтобы его поменять введите /change {токен}')
        print(err)
def change_token(message):
    commands = message.text.split()

    if (commands[0] == '/change' and len(commands) > 1):
        res = cur.execute(f'UPDATE "user" SET token = "{commands[1]}" WHERE id = {message.chat.id}')
        con.commit()
        bot.send_message(message.chat.id, f'Вы поменяли свой токен на: {commands[1]}')
    elif (commands[0] == '/change'):
        bot.send_message(message.chat.id, 'Чтобы изменить токен введите: /change [токен]')
    else:
        pass

def info_token(message, token):
    bot.send_message(message.chat.id, f'Ваш текущий токен: {token}')

def set_token(message):
    cur.execute(f'INSERT INTO user VALUES ({message.chat.id}, "{message.text}")')
    con.commit()
    bot.send_message(message.chat.id, f'''Вы добавили в свой профиль данный токен: {message.text}
Чтобы изменить его, пропишите /change [токен]''')

bot.polling(non_stop=True)
