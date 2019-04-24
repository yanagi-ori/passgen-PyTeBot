import logging
import random

import telegram
from telegram.ext import RegexHandler, MessageHandler, Filters, CommandHandler, Updater
from xkcdpass import xkcd_password as xp

import config
import locale

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(bot, update):
    global chat_id
    chat_id = update.message.chat_id
    dp.remove_handler(not_started)
    markup = telegram.ReplyKeyboardMarkup(locale.start_keyboard)
    bot.send_message(chat_id=update.message.chat_id,
                     text=locale.welcome_message,
                     reply_markup=markup)

    dp.add_handler(RegexHandler("^(Generate Weak password)$", easy_pwd))
    dp.add_handler(RegexHandler("^(Generate Normal password)$", normal_pwd))
    dp.add_handler(RegexHandler("^(Generate Strong password)$", strong_pwd))
    dp.add_handler(RegexHandler("^(Generate Stronger password)$", stronger_pwd))
    dp.add_handler(RegexHandler("^(Generate Insane password)$", insane_pwd))
    dp.add_handler(RegexHandler("^(Send Feedback)$", feedback_handler))


def easy_pwd(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generate_weak_pwd())


def normal_pwd(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generate_normal_pwd())


def strong_pwd(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generate_strong_pwd())


def stronger_pwd(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generate_stronger_pwd())


def insane_pwd(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=generate_insane_pwd())


def throw_random():
    return random.randint(0, 1)


def generate_weak_pwd():
    # 2 words, no separators between words
    return xp.generate_xkcdpassword(wordlist=wordlist, numwords=2, delimiter="")


def generate_normal_pwd():
    # 3 words, no separators between words, second word is CAPITALIZED
    words = xp.generate_xkcdpassword(wordlist=wordlist, numwords=3, delimiter=" ").split()
    return "{0}{1}{2}".format(words[0], str.upper(words[1]), words[2])


def generate_strong_pwd():
    # 3 words, random CAPITALIZATION, random number as separator between words
    words = xp.generate_xkcdpassword(wordlist=wordlist, numwords=3, delimiter=" ").split()
    return "{word0}{randnum0}{word1}{randnum1}{word2}".format(word0=str.upper(words[0]) if throw_random() else words[0],
                                                              word1=str.upper(words[1]) if throw_random() else words[1],
                                                              word2=str.upper(words[2]) if throw_random() else words[2],
                                                              randnum0=random.randint(0, 9),
                                                              randnum1=random.randint(0, 9))


def generate_stronger_pwd():
    # Same as "strong", but using 4 words
    words = xp.generate_xkcdpassword(wordlist=wordlist, numwords=4, delimiter=" ").split()
    return "{word0}{randnum0}{word1}{randnum1}{word2}{randnum2}{word3}" \
        .format(word0=str.upper(words[0]) if throw_random() else words[0],
                word1=str.upper(words[1]) if throw_random() else words[1],
                word2=str.upper(words[2]) if throw_random() else words[2],
                word3=str.upper(words[3]) if throw_random() else words[3],
                randnum0=random.randint(0, 9),
                randnum1=random.randint(0, 9),
                randnum2=random.randint(0, 9))


def generate_insane_pwd():
    # 4 words, second one CAPITALIZED, separators, prefixes and suffixes
    words = xp.generate_xkcdpassword(wordlist=wordlist, numwords=4, delimiter=" ").split()
    return "{randsymbol}{randsymbol}{word0}{separator}{word1}{separator}{word2}{randsymbol}{randsymbol}" \
        .format(randsymbol=random.choice("!$%^&*-_+=:|~?/.;0123456789"),
                word0=words[0],
                word1=str.upper(words[1]),
                word2=words[2],
                separator=random.choice(".$*;_=:|~?!%-+"))


def cancel_button(bot, update):
    try:
        dp.remove_handler(text_handler)
    except NameError:
        pass
    bot.send_message(update.message.chat_id,
                     text=locale.cancel,
                     reply_markup=telegram.ReplyKeyboardMarkup(locale.start_keyboard))


def feedback_handler(bot, update):
    """Catch user feedback"""
    global text_handler
    dp.add_handler(RegexHandler("^(Cancel)$", cancel_button))
    markup = telegram.ReplyKeyboardMarkup([[locale.cancel]])
    bot.send_message(update.message.chat_id,
                     text=locale.ask_feedback,
                     reply_markup=markup)
    text_handler = MessageHandler(Filters.text, send_feedback,
                                  pass_user_data=True)
    dp.add_handler(text_handler)


def send_feedback(bot, update, user_data):
    """Send feedback to admins"""
    markup = telegram.ReplyKeyboardMarkup(locale.start_keyboard)
    bot.send_message(chat_id=update.message.chat_id,
                     text=locale.done, reply_markup=markup)
    for guy in config.admins:
        bot.send_message(guy, str(update.message.from_user.username) +
                         locale.fb_mes + update.message.text)
    dp.remove_handler(text_handler)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def dummy(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=locale.not_started)


def debug(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=locale.debug)
    config.admins.add(update.message.chat_id)
    print(config.admins)


def cancel_debug(bot, update):
    try:
        config.admins.remove(update.message.chat_id)
        bot.send_message(update.message.chat_id, 'success')
    except KeyError:
        pass


def main():
    """Run bot."""
    global dp, not_started

    updater = Updater(config.token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("__debug", debug))
    dp.add_handler(CommandHandler("__cancel_debug", cancel_debug))
    not_started = MessageHandler(Filters.text, dummy)
    dp.add_handler(not_started)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    global wordlist
    wordlist = xp.generate_wordlist(wordfile=config.words_file, min_length=4, max_length=10, valid_chars="[a-z]")
    main()
