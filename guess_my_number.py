"""
Guess-My-Number Game for Telegram Bot: 100% Python
Created 2021 by Nugroho Fredivianus
Just for fun, do what you please with this one! :)
"""

# !pip install python-telegram-bot
from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import MessageHandler, Filters, Updater
from datetime import datetime
from os.path import isfile
from random import randrange

# Save your token at this file, flat text no end-of-line
try:
    with open("bot_token.txt", "r") as f:
        token = f.read()
except:
    print("ERROR:\nPlease put the token for your Telegram bot to a file named bot_token.txt")
    exit()

bot = Bot(token)

scorefile = "score.csv"
header = "date;name;trial;score"
highscores = []
scores = []
userdata = {}


def reply(uid, teks):
    mode = userdata[uid]["mode"]
    buttons = userdata[uid]["buttons"] if mode == "play" else [["Chat", "Play", "Scores"]]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True) if mode != "ask_name" else ReplyKeyboardRemove()
    bot.send_message(uid, parse_mode="HTML", text=teks, reply_markup=markup)


def reset(uid, _mode="chat"):
    global userdata
    min_value = randrange(80) + 1
    userdata[uid] = {}
    userdata[uid]["mode"] = _mode
    userdata[uid]["trials"] = 5
    userdata[uid]["min_value"] = min_value
    userdata[uid]["key"] = min_value + randrange(20)
    userdata[uid]["last_score"] = 0
    userdata[uid]["buttons"] = [[str(a + n * 5 + min_value) for a in range(5)] for n in range(4)]


def print_highscores(uid):
    reply(uid, "\n".join(["<b>" + header.title() + "</b>"] + highscores).replace(";", "｜"))


def add_to_highscores(uid, name, trial, score):
    global scores, highscores
    if len(name) == 0:
        name = "user"

    highscores.append("{};{};{};{}".format(datetime.now().strftime("%d-%m-%Y"), name, 5 - trial, score))
    highscores.sort(key=lambda x: -int(x.split(";")[-1]))
    highscores = highscores[:10]
    scores = [int(h.split(";")[-1]) for h in highscores]

    with open(scorefile, "w") as _f:
        _f.write("\n".join([header] + highscores))
    print_highscores(uid)
    # Want to reset highscore? Delete scorefile and restart bot


def respond(_data, update):
    global userdata, scores, highscores
    message = _data.message
    uid = str(message.chat.id)  # user id

    ori_text = message.text
    if len(ori_text) > 1 and ori_text.startswith("/"):
        ori_text = ori_text[1:]
    text = ori_text.lower()

    if uid not in userdata:
        reset(uid)

    if text == "scores":
        reset(uid)
        print_highscores(uid)

    elif text == "chat":
        reset(uid)
        reply(uid, "<i>Type anything, I'll throw it back(wards).</i>")

    elif text == "play":
        reset(uid, "play")
        reply(uid, "Guess a number in [{}, {}]!".format(userdata[uid]["min_value"], userdata[uid]["min_value"] + 19))

    elif userdata[uid]["mode"] == "play":
        if text.isdigit():
            userdata[uid]["trials"] -= 1
            user_guess = int(text)

            if user_guess != userdata[uid]["key"]:
                buttons = userdata[uid]["buttons"]
                eliminate = range(userdata[uid]["min_value"], user_guess + 1) \
                    if user_guess < userdata[uid]["key"] else range(user_guess, userdata[uid]["min_value"] + 20)
                for e in eliminate:
                    if str(e) in buttons[(e - userdata[uid]["min_value"]) // 5]:
                        buttons[(e - userdata[uid]["min_value"]) // 5].remove(str(e))
                userdata[uid]["buttons"] = buttons

                reply(uid, "Too {}!".format("small" if user_guess < userdata[uid]["key"] else "big"))

                if userdata[uid]["trials"] <= 0:
                    user_key = userdata[uid]["key"]
                    reset(uid)
                    reply(uid, "The answer is {}\nHit <b>Play</b> to retry".format(user_key))

            else:
                reply(uid, "Correct!")
                score = 20 * userdata[uid]["trials"] + 20
                if len(scores) < 10 or score > scores[-1]:
                    userdata[uid]["mode"] = "ask_name"
                    userdata[uid]["last_score"] = score
                    reply(uid, "Enter your name (max. 15 chars) for highscore")
                else:
                    reset(uid)
                    reply(uid, "Your score: {}\nHit <b>Play</b> to play again".format(score))

        else:
            reply(uid, "Should be a number")

    elif userdata[uid]["mode"] == "ask_name":
        add_to_highscores(uid, ori_text[:15], userdata[uid]["trials"], userdata[uid]["last_score"])
        reset(uid)
        reply(uid, "Hit <b>Play</b> to play again")

    else:
        reply(uid, ori_text[::-1])

    return "ok"


if __name__ == '__main__':
    updater = Updater(bot=bot)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text, respond))
    print("@" + bot.username + " is ready.")

    if isfile(scorefile):
        with open(scorefile, "r") as f:
            highscores = f.readlines()[1:]
        highscores = [h.replace("\n", "") for h in highscores]
        scores = [int(h.split(";")[-1]) for h in highscores]
        scores.sort(reverse=True)

    else:
        with open(scorefile, "w") as f:
            f.write(header)

    updater.start_polling()
    updater.idle()
