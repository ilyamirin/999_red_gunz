import db_connector as dbc
import excel_files_handler as excel

import logging
import os
import requests

# logs

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(levelname)s : %(asctime)s : %(name)s : %(message)s')
stream_formatter = logging.Formatter('%(levelname)s : %(name)s : %(message)s')

file_handler = logging.FileHandler('logs/bot_logs.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_formatter)
stream_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Load additional data
from app_data import load_files

global REGIONS
global DEPUTIES_PARTIES
global DEPUTIES_REGIONS

REGIONS = load_files.REGIONS

# telegram library methods

import telegram
from telegram.ext import Updater
from telegram.ext import Filters
from telegram.ext import CallbackContext
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardRemove
from telegram.ext import BaseFilter
from telegram.utils.request import Request

global BOT
global TOKEN
VOTE = 1  # for vote conversation handler
REGION = 1  # for start conversation handler
EXCEL_FILE, DOCX_FILE, PDF_FILE, VOTES_FILE, BILL_ACCEPT = range(5)  # for add_bill conversation handler

with open('config.txt', 'r') as file:
    host = file.readline().strip()
    port = file.readline().strip()
    web_hook_link = file.readline().strip()
    admin_id = file.readline().strip()
    TOKEN = file.readline().strip()

BOT = telegram.Bot(token=TOKEN, request = Request(con_pool_size=10))
updater = Updater(bot=BOT, use_context=True)
dispatcher = updater.dispatcher


# Custom filter

class VoteFilter(BaseFilter):
    def filter(self, message):
        if '/cancel' in message.text:
            return False
        else:
            if message.text:
                return True


except_cancel_filter = VoteFilter()


# Validation data functions

def validate_answer(answer: str, options: list):
    answer = answer.strip()
    check_answer = answer.lower()
    options = [option.lower() for option in options]
    if check_answer in options:
        return answer
    else:
        return None


def processed_answer(answer: dict):
    answers = {
        '1': 1,
        '2': -1,
        '3': 0,
    }
    return answers[answer]


# Additional functions for sending data

def send_file(chat_id: str, file_path: str):
    file_check = os.path.exists(file_path)
    if file_check:
        file_properties = BOT.send_document(chat_id, open(file_path, 'rb'))
        logger.info(f'Asked by {chat_id} file {file_path} was sent')
        return file_properties
    else:
        logger.warning(f'Asked by {chat_id} file {file_path} not found')
        return None


# FILE UPLOAD handlers

def check_file_format(update, file_name, file_format):
    if not file_name.endswith(file_format):
        update.message.reply_text(
            "Неверный тип файла!"
        )
        return False
    else:
        return True


def upload_files(context, file_type):
    try:
        file = context.user_data[file_type].get_file()
        b_file = bytes(file.download_as_bytearray())
        if file_type == 'docx_file':
            with open(f"notes/{context.user_data['bill_id']}.docx", 'wb') as f:
                f.write(b_file)
                return True
        if file_type == 'pdf_file':
            with open(f"pdf_docs/{context.user_data['bill_id']}.pdf", 'wb') as f:
                f.write(b_file)
                return True
        if file_type == 'vote_file':
            with open(f"vote_results/{context.user_data['bill_id']}.xlsx", 'wb') as f:
                f.write(b_file)
                return True
    except Exception as e:
        logger.exception(e)
        return False


def add_excel_file(update: Updater, context: CallbackContext):
    try:
        file = update.message.document
        file_name = file['file_name']
        if not check_file_format(update, file_name, '.xlsx'):
            return ConversationHandler.END
        logger.info(f"Got file {file_name}")

        file = file.get_file().download_as_bytearray()
        file = bytes(file)

        is_bill, bill_data, e = excel.add_bill_excel(file)
        if e:
            logger.exception(e)
            update.message.reply_text(
                e.args[0]
            )
            return ConversationHandler.END
        logger.info(f"uploading bill {bill_data['bill_id']}")
        if not is_bill:
            context.user_data["bill_id"] = bill_data['bill_id']
            context.user_data["is_note"] = bill_data['is_note']
            context.user_data["is_pdf"] = bill_data["is_pdf"]
            context.user_data["is_secret"] = bill_data["is_secret"]
            context.user_data["bill_data"] = bill_data

            if context.user_data['is_note']:
                update.message.reply_text(
                    'Отправьте пояснительную записку .docx '
                )
                return DOCX_FILE
            elif context.user_data['is_pdf']:
                update.message.reply_text(
                    'Отправьте пакет документов .pdf'
                )
                return PDF_FILE
            else:
                update.message.reply_text(
                    'Нет пояснительной записки, нет перечня документов',
                )
                return ConversationHandler.END

        else:
            raise Exception("Error while adding bill with excel")
    except Exception as e:
        update.message.reply_text(
            'Увы, произошла ошибка :('
        )
        logger.exception(e)
        return ConversationHandler.END


def add_docx_file(update: Updater, context: CallbackContext):
    try:
        file = update.message.document
        file_name = file['file_name']
        if not check_file_format(update, file_name, '.docx'):
            return ConversationHandler.END
        logger.info(f"Got file {file_name}")

        # Файл не загружается сразу, а после того как все диалоги закончатся
        context.user_data['docx_file'] = file

        if context.user_data["is_pdf"]:
            update.message.reply_text(
                'Отправьте пакет документов .pdf'
            )
            return PDF_FILE
        elif not context.user_data["is_secret"]:
            update.message.reply_text(
                "Отправьте результаты голосования депутатов .xlsx",
            )
            return VOTES_FILE
        else:
            # ЗАРГУЗКА ФАЙЛОВ ЕСЛИ ПДФ ФАЙЛОВ НЕТ
            update.message.reply_text(
                "Подтвердите добавление законопроекта(/cancel - нет, остальное - да) :",
            )
            return BILL_ACCEPT

    except Exception as e:
        update.message.reply_text(
            'Увы, произошла ошибка :('
        )
        logger.exception(e)
        return ConversationHandler.END


def add_pdf_file(update: Updater, context: CallbackContext):
    try:
        file = update.message.document
        file_name = file['file_name']
        if not check_file_format(update, file_name, '.pdf'):
            return ConversationHandler.END
        logger.info(f"Got file {file_name}")

        context.user_data['pdf_file'] = file

        if not context.user_data['is_secret']:
            update.message.reply_text(
                "Отправьте результаты голосования депутатов .xlsx",
            )
            return VOTES_FILE
        else:
            update.message.reply_text(
                "Подтвердите добавление законопроекта(/cancel - нет, остальное - да) :",
            )
        return BILL_ACCEPT

    except Exception as e:
        update.message.reply_text(
            'Увы, произошла ошибка :('
        )
        logger.exception(e)
        return ConversationHandler.END


def add_vote_results(update: Updater, context: CallbackContext):
    try:
        file = update.message.document
        file_name = file['file_name']
        if not check_file_format(update, file_name, '.xlsx'):
            return ConversationHandler.END
        logger.info(f"Got file {file_name}")

        context.user_data['vote_file'] = file

        update.message.reply_text(
            "Подтвердите добавление законопроекта(/cancel - нет, остальное - да) :",
        )
        return BILL_ACCEPT

    except Exception as e:
        update.message.reply_text(
            'Увы, произошла ошибка :('
        )
        logger.exception(e)
        return ConversationHandler.END


def accept_bill(update: Updater, context: CallbackContext):
    try:
        if context.user_data['is_note']:
            _ = upload_files(context, 'docx_file')
        if context.user_data['is_pdf']:
            _ = upload_files(context, 'pdf_file')
        if not context.user_data['is_secret']:
            _ = upload_files(context, 'vote_file')
        result = dbc.add_bill(context.user_data["bill_data"])
        if not result:
            raise Exception("Ошибка записи законопроекта в БД.")

        update.message.reply_text(
            "Законопроект успешно добавлен!"
        )

        logger.info(f"{context.user_data['bill_id']} - bill added.")
        return ConversationHandler.END
    except Exception as e:
        update.message.reply_text(
            'Увы, произошла ошибка :('
        )
        logger.exception(e)
        return ConversationHandler.END

# command handlers


def start(update: Updater, context: CallbackContext):
    # Добавить в базу данных
    try:
        chat_id = update.effective_chat.id
        first_name = update.effective_chat.first_name
        user_exist = dbc.check_user(chat_id)
        if user_exist:
            logger.info(f"ALREADY EXISTED User {chat_id} started command start")
            context.bot.send_message(chat_id=chat_id, text="Вы уже пользователь!")
        else:
            context.user_data['user_id'] = chat_id
            context.user_data['first_name'] = first_name
            context.user_data['chat_id'] = chat_id
            context.user_data['region'] = None

            dbc.add_user(context.user_data)
            logger.info(f"NEW User {chat_id} started command start")
            update.message.reply_text(
                '''Введите свой регион из списка regions.txt (необязательно).
Или команду /cancel чтобы закончить регистрацию \n
                ''',
                reply_markup=ReplyKeyboardRemove(),
            )
            # file with regions
            send_file(chat_id, 'app_data/regions.txt')
            return REGION
    except:
        logger.exception(f"ERROR while start : chat_id {chat_id}")
        updater.message.reply_text(
            "Увы, произошла ошибка :(",
        )


def get_bill(update: Updater, context: CallbackContext):
    # Проверка на то, что пользователь существует в базе, если нет то сообщение написать start
    logger.info(f"User {update.effective_chat.id} started command get_bill")
    try:
        # Проверка что пользователь есть в базе данных и законопроект есть в базе
        chat_id = update.effective_chat.id
        user_exist = dbc.check_user(chat_id)

        if user_exist:
            # проверка на то, что в базе данных есть такой запрос
            # = 1: обработать как номер законопроекта
            # = 0: выдать новый законопроект
            assert len(context.args) == 1 or len(context.args) == 0

            #get user region
            context.user_data['user_region'] = dbc.get_user_region(chat_id)

            # getting the right bill
            if len(context.args) == 1:
                bill = dbc.get_bill_by_id(chat_id, context.args[0])
                logger.info(f"user message {context.args[0]}")
            else:
                bill = dbc.get_new_bill_by_id(chat_id)
                if not bill:
                    update.message.reply_text(
                        'Вы ответили на все законопроекты :)',
                    )
                    return ConversationHandler.END
                logger.info(f"user got {bill.bill_id} to vote")

            if bill:
                context.user_data['chat_id'] = chat_id
                context.user_data['bill_title'] = bill.title
                context.user_data['bill_id'] = bill.bill_id
                context.user_data['is_secret'] = bill.is_secret
                context.user_data['bill_result'] = {
                    'vote_for': bill.vote_for,
                    'vote_against': bill.vote_against,
                    'not_voted': bill.not_voted,
                    'abstained': bill.abstained,
                }

                # send bill info
                # try block to stop sending over and over again when an answer is wrong
                try:
                    _ = context.user_data['is_sent']
                    logger.info('files already sent')
                except:
                    # send files and bill title
                    logger.info('sending files')
                    context.user_data['is_sent'] = True

                    update.message.reply_text(
                        context.user_data['bill_title'],
                    )

                    pdf_path, note_path = dbc.get_files_paths(context.user_data['bill_id'])
                    if pdf_path:
                        send_file(chat_id, pdf_path)
                    if note_path:
                        send_file(chat_id, note_path)

                update.message.reply_text(
                    'Введите свой голос:\n 1 - За\n 2 - Против\n 3 - Воздержаться\n /cancel - остановить голосование',
                    reply_markup=ReplyKeyboardRemove(),
                )
                return VOTE

            else:
                update.message.reply_text(
                    'Законопроекта с таким номером нет, либо вы уже проголосовали по данному законопроекту:(',
                )
                return ConversationHandler.END

        else:
            logger.info(f"User command get_bill by {update.effective_chat.id} not completed. No such user")
            update.message.reply_text(
                'Перед тем, как получить законопроект запустите команду /start',
            )
    except Exception as e:
        logger.exception(e)
        logger.warning(f"User command get_bill by {update.effective_chat.id} ERROR arguments: {context.args}")
        update.message.reply_text(
            'Увы, произошла ошибка :(',
        )


def add_bill(update: Updater, context: CallbackContext):
    chat_id = update.effective_chat.id
    logger.warning(f"user {chat_id} add_bill")
    if chat_id != int(admin_id):
        # end conversation cause its for admin only
        help_message(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text(
            'Передайте .xlsx файл с законопроектом'
        )
        return EXCEL_FILE


def vote_handler(update: Updater, context: CallbackContext):
    answer = validate_answer(update.message.text, ['1', '2', '3', '/cancel'])
    if answer:
        logger.info(f'user send answer - {answer}')
        # need to update DB on answer
        answer = processed_answer(answer)
        answer_data = {
            'bill_id': context.user_data['bill_id'],
            'user_id': context.user_data['chat_id'],
            'user_vote': answer,
        }

        _ = dbc.add_answer(answer_data)
        #
        logger.info(f'Answer added chat_id - {context.user_data["chat_id"]}, bill_id - {context.user_data["bill_id"]}')
        update.message.reply_text('Ваш голос успешно записан!')

        update.message.reply_text(
            '''Результаты голования:
За - {vote_for}
Против - {vote_against}
Воздержались - {abstained}
Не голосовали - {not_voted}'''.format(**context.user_data["bill_result"])
        )
        if not context.user_data['is_secret'] and context.user_data['user_region']:
            try:
                dep_data = excel.get_deps_data(context.user_data['bill_id'],context.user_data['user_region'])
                dep_data = '\n'.join(dep_data)
                update.message.reply_text(
                    'Результаты голосования депутатов из вашего региона:\n' + dep_data
                )
            except Exception as e:
                logger.exception(e)
        context.user_data.pop('is_sent')
        return ConversationHandler.END
    else:
        update.message.reply_text('Укажите корректный ответ!')
        logger.info('User send incorrect answer')
        return VOTE


def region_handler(update: Updater, context: CallbackContext):
    region = validate_answer(update.message.text, REGIONS)
    try:
        if region:
            dbc.user_region_update(context.user_data['user_id'], region)
            update.message.reply_text(
                "Вы успешно зарегистрировались!",
            )
            logger.info('User added own region')
            return ConversationHandler.END
        else:
            update.message.reply_text(
                'Укажите корректный ответ!'
            )
            logger.info('User send incorrect answer')
            return REGION
    except Exception as e:
        logger.exception(e)
        update.message.reply_text(
            "Увы, произошла ошибка :("
        )
        return ConversationHandler.END


def end_start_handler(update: Updater, context: CallbackContext):
    update.message.reply_text(
        "Вы успешно зарегистрировались!",
    )
    logger.info('END_START_handler')
    return ConversationHandler.END


def cancel_handler(update: Updater, context: CallbackContext):
    update.message.reply_text('Отмена голосования')
    # clean data about sent files
    if context.user_data['is_sent']:
        context.user_data.pop('is_sent')
    logger.info('CANCEL_handler')
    return ConversationHandler.END


def add_bill_cancel(update: Updater, context: CallbackContext):
    update.message.reply_text(
        'Отмена добавления законопроeкта',
    )
    return ConversationHandler.END


def help_message(update: Updater, context: CallbackContext):
    message = '''
    Для работы с ботом воспользуйтесь одной из команд:
    /start - добавление пользователя в базу данных
    /get_bill - начать голосование за законопроект
    '''
    logger.info(f"User {update.effective_chat.id} send a message {update.effective_message.text}")
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


# conversation handlers
start_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start, pass_user_data=True),
    ],
    states={
        REGION: {
            MessageHandler(except_cancel_filter, region_handler, pass_user_data=True),
        },
    },
    fallbacks=[
        CommandHandler('cancel', end_start_handler, pass_user_data=True)
    ]
)

vote_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('get_bill', get_bill, pass_user_data=True),
    ],
    states={
        VOTE: [
            MessageHandler(except_cancel_filter, vote_handler, pass_user_data=True)
        ],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_handler, pass_user_data=True),
    ],
)

add_bill_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('add_bill', add_bill, pass_user_data=True),
    ],
    states={
        EXCEL_FILE: [
            MessageHandler(Filters.document, add_excel_file, pass_user_data=True)
        ],
        DOCX_FILE: [
            MessageHandler(Filters.document, add_docx_file, pass_user_data=True)
        ],
        PDF_FILE: [
            MessageHandler(Filters.document, add_pdf_file, pass_user_data=True)
        ],
        VOTES_FILE: [
            MessageHandler(Filters.document, add_vote_results, pass_user_data = True)
        ],
        BILL_ACCEPT: [
            MessageHandler(except_cancel_filter, accept_bill, pass_user_data=True)
        ]
    },
    fallbacks=[
        MessageHandler(Filters.all, add_bill_cancel, pass_user_data=True)
    ]
)

# command handlers
# start - добавление пользователя в базу данных
# get_bill - начать голосование за законопроект. Принимает один параметр - id законопроекта

start_handler = CommandHandler('start', start)
get_bill_handler = CommandHandler('get_bill', get_bill)
add_bill_handler = CommandHandler('add_bill', add_bill)
# message handlers

missed_message_handler = MessageHandler(Filters.all, help_message)

# dispatcher

dispatcher.add_handler(start_conv_handler)
dispatcher.add_handler(vote_conv_handler)
dispatcher.add_handler(add_bill_conv_handler)

dispatcher.add_handler(add_bill_handler)
dispatcher.add_handler(get_bill_handler)
dispatcher.add_handler(start_handler)

dispatcher.add_handler(missed_message_handler)


def set_webhook(link):
    result = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={link}")
    return result


# bot start with webhook
if __name__ == '__main__':

    is_set = set_webhook(web_hook_link)
    if is_set.ok:
        updater.start_webhook(listen=host,
                              port=int(port))
        updater.idle()
