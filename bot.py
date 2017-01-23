import logging
from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

import json
from pymongo import MongoClient
from pymongo import ReturnDocument
from datetime import datetime
from credentials import TOKEN, APP_URL
from os import environ # path

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


FACULTIES = ("SCHOOL OF BUSINESS", "SCIENCE", "ENGINEERING", "SCHOOL OF COMPUTING", "JOINT MULTI-DISCIPLINARY PROGRAMMES", "LAW", "SCHOOL OF DESIGN AND ENVIRONMENT", "ARTS & SOCIAL SCIENCES")
ROUNDS = ("Round 1A", "Round 1B", "Round 1C", "Round 2A", "Round 2B", "Round 3A", "Round 3B")

#non-bot functions
def getRounds(moduleCode, chat_id, record):
    userFaculty = record["faculty"]
    userStudentType = record["studentType"]
    availRounds = []

    currentRound = 0
    for currRound in summaries:
        for module in currRound:
            if module["moduleCode"] == moduleCode: #match module code
                groups = module["info"]

                for group in groups:
                    groupFac = group["faculty"]
                    groupType = group["studentType"]

                    if groupType == "New Students [P]":
                        if userStudentType == "senior" or userFaculty != groupFac:
                            break
                    elif groupType == "Returning Students [P]":
                        if userStudentType == "freshie" or userFaculty != groupFac:
                            break
                    elif groupType == "Reserved for [G] in later round":
                        break
                    elif groupType == "Returning Students and New Students [P]":
                        if userFaculty != groupFac:
                            break
                    elif groupType == "NUS Students [G]":
                        if userFaculty == groupFac:
                            break
                    elif groupType == "NUS Students [P]":
                        if userFaculty != groupFac:
                            break
                    elif groupType == "NUS Students [P, G]":
                        pass
                    elif groupType == "Returning Students [P] and NUS Students [G]":
                        if userFaculty == groupFac and userStudentType == "freshie":
                            break

                    addMod = {}
                    addMod["round"] = ROUNDS[currentRound]
                    addMod["lowestBid"] = group["lowestBid"]
                    addMod["succBid"] = group["succBid"]
                    addMod["highestBid"] = group["highestBid"]
                    availRounds.append(addMod)
                break
        currentRound += 1

    return availRounds

# send a reminder to the user when the CORS bidding period is open
def sendReminder():
    currentTime = datetime.utcnow() #get current time

#bot functions

#sends a welcome message to the user
#also initialises the customised ReplyKeyboard
def start(bot, update):
    chat_id = update.message.chat_id
    text = "Of course we'll make your life easier ;)" + "\n\n"
    text += "1) Choose your faculty and year" + "\n"
    text += "2) Find out when to bid for a module, and its bidding history instantly" + "\n"
    bot.sendMessage(chat_id=chat_id, text=text)
    setup(bot, update)

def setreminder(bot, update):
    chat_id = update.message.chat_id
    data = {}
    data["chat_id"] = chat_id
    text = "Reminders set. I'll nudge you when the CORS bidding period starts.\n"
    bot.sendMessage(chat_id=chat_id, text=text)
    remindID = db.remindID
    remindID.insert_one(data)

def removereminder(bot, update):
    chat_id = update.message.chat_id
    data = {}
    data["chat_id"] = chat_id
    text = "Removed from reminder list.\n"
    bot.sendMessage(chat_id=chat_id, text=text)
    remindID = db.remindID
    remindID.delete_one({'chat_id' : chat_id})

def setup(bot, update):
    chat_id = update.message.chat_id

    keyboard = []
    for faculty in FACULTIES:
        keyboard.append([InlineKeyboardButton(faculty, callback_data=faculty)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Now, choose your faculty:"
    bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)

def button(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    records = {}
    records["chat_id"] = chat_id
    userID = db.userID
    userID.insert_one(records)

    if query.data in FACULTIES:
        records["faculty"] = query.data
        result = userID.update_one({'chat_id' : chat_id}, {'$set' : {'faculty' : query.data}}, upsert=True)
        keyboard = []
        keyboard.append([InlineKeyboardButton("Freshie", callback_data="freshie")])
        keyboard.append([InlineKeyboardButton("Senior", callback_data="senior")])

        text = "Are you a freshie or senior?"
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.editMessageText(chat_id=chat_id, text=text, message_id=message_id, reply_markup=reply_markup)
        
    else:
        records["studentType"] = query.data
        result = userID.update_one({'chat_id' : chat_id}, {'$set' : {'studentType' : query.data}}, upsert=True)
        text = "You're all set! Use /info [module code] to get more info about a module"
        bot.editMessageText(chat_id=chat_id, text=text, message_id=message_id)


def info(bot, update):
    chat_id = update.message.chat_id
    moduleCode = update.message.text.replace("/info ", "").upper()
    userID = db.userID
    record = userID.find_one({"chat_id" : chat_id})
    text = ""
    if record:
        availRounds = getRounds(moduleCode, chat_id, record)
        if availRounds:
            text = text + "*" + moduleCode + "*" + "\n"
            for aRound in availRounds:
                text = text + aRound["round"] + "\n"
                text = text + "Lowest Bid: " + aRound["lowestBid"] + "\n"
                text = text + "Successful Bid: " + aRound["succBid"] + "\n"
                text = text + "Highest Bid: " + aRound["highestBid"] + "\n\n"
        else:
            text += "Unavailable for bidding in any round (Ask Ms Toh or visit CORS website)"

    else:
        text += "Please use the /setup command first"

    bot.sendMessage(chat_id=chat_id, text=text, parse_mode="Markdown")


def help(bot, update):
    chat_id = update.message.chat_id
    text = "*Disclaimer: This is a hackathon prototype.*\n\n"
    text = text + "Please report any bugs to shaohui@u.nus.edu"

    bot.sendMessage(chat_id=chat_id, text=text, parse_mode="Markdown")

def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))

def main():

    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # initialise bot
    global bot
    bot = Bot(token=TOKEN)

    # setup webhook
    PORT = int(environ.get('PORT', '5000'))
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.setWebhook(APP_URL + TOKEN)

    client = MongoClient('mongodb://ofcorsbot:ofcorsbot@ds145405.mlab.com:45405/ofcors')
    # getting database
    global db
    db = client.ofcors
    
    global round1A
    global round1B
    global round2A
    global round2B
    global round3A
    global round3B

    global round1ASum
    global round1BSum
    global round2ASum
    global round2BSum
    global round3ASum
    global round3BSum

    # global rounds
    # rounds = []
    global summaries
    summaries = []

    #import summaries
    with open('round1ASumm.json', 'r') as json_data:
        data = json.load(json_data)
    round1A = data["round1Asumm"]
    summaries.append(round1A)

    with open('round1BSumm.json', 'r') as json_data:
        data = json.load(json_data)
    round1B = data["round1Bsumm"]
    summaries.append(round1B)

    with open('round1CSumm.json', 'r') as json_data:
        data = json.load(json_data)
    round1C = data["round1Csumm"]
    summaries.append(round1C)

    with open('round2ASumm.json', 'r') as json_data:
        data = json.load(json_data)
    round2A = data["round2Asumm"]    
    summaries.append(round2A)


    with open('round2BSumm.json', 'r') as json_data:
        data = json.load(json_data)
    round2B = data["round2Bsumm"]  
    summaries.append(round2B)


    with open('round3ASumm.json', 'r') as json_data:
        data = json.load(json_data)
    round3A = data["round3Asumm"]
    summaries.append(round3A)


    with open('round3BSumm.json', 'r') as json_data:
        data = json.load(json_data)
    round3B = data["round3Bsumm"]
    summaries.append(round3B)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler("setup", setup))
    updater.dispatcher.add_handler(CommandHandler("info", info))
    updater.dispatcher.add_handler(CommandHandler("setreminder", setreminder))
    updater.dispatcher.add_handler(CommandHandler("removereminder", removereminder))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_error_handler(error)

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()

if __name__ == "__main__":
    main()
