import datetime
import json
import requests


class BotCommander:
    BOT_TOKEN = "TELEGRAM_BOT_API_KEY"
    BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/'

    TEST_NOTIFICATIONS = "Testing notifications!\n" \
                         "(Message below doesn't show any real data, it depicts the approximate message you will " \
                         "receive)"

    TEST_EXAMPLE = """Filter notifications
huurzone (total of 2)

kamernet (total of 7)
link: https://kamernet.nl/ ...

pararius (total of 7)
link: https://www.pararius.nl/ ...

roomnl (total of 30)
link: https://www.room.nl/en/ ...

studentwoningen (total of 5)
link: https://www.studentenwoningweb.nl/ ..."""

    def get_current_date(self):
        # 20/08/23 15:56:06
        return datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')

    def send_message(self, chat_id, text):
        print(f"[bot_commander] send message, \nchatID: {chat_id} \ntext: ---{text}---")
        response = requests.post(self.BASE_URL + 'sendMessage',
                                 data={'chat_id': chat_id, 'text': text})
        return response.json()

    def send_message_markup(self, chat_id, text, reply_markup):
        print(f"[bot_commander] send message markup, chatID: {chat_id} text: {text}")
        response = requests.post(self.BASE_URL + 'sendMessage',
                                 data={'chat_id': chat_id, 'text': text, 'reply_markup': json.dumps(reply_markup)})
        return response.json()

    def edit_message(self, chat_id, message_id, text, reply_markup=json.dumps({'inline_keyboard': []})):
        print(f"[bot_commander] edit message, chatID: {chat_id}")
        edit_data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'reply_markup': reply_markup
        }
        return requests.post(self.BASE_URL + 'editMessageText', data=edit_data)

    def get_update(self):
        print("[bot_commander] get update")
        response = requests.post(self.BASE_URL + 'getUpdates')
        return response.json()

    def set_webhook(self, webhook_url, drop_pending_updates=True):
        print(f"[bot_commander] set webhook, url: {webhook_url}")

        response = requests.post(self.BASE_URL + "setWebhook",
                                 data={'url': webhook_url, 'drop_pending_updates': drop_pending_updates})

        if response.status_code != 200:
            print(f"[bot_commander] webhook failed, status code: {response.status_code}")
            print(f"[bot_commander] response text: {response.text}")

    def set_commands(self):
        commands = [
            {'command': 'start', 'description': 'Open main menu / Sign up for notifications'},
            {'command': 'help', 'description': 'Open main menu / Sign up for notifications'}
        ]
        response = requests.post(self.BASE_URL + "setMyCommands", json={'commands': json.dumps(commands)})
        return response.status_code

    def remove_webhook(self):
        print("[bot_commander] deleting webhook")
        response = requests.post(self.BASE_URL + 'deleteWebhook')
        return response.json()

    def welcome_message(self, chat_id):
        welcome_text = """
Hi,
I'm Orwell The Finder (version 0.1)
a Telegram Bot searching for housing updates in Amsterdam 🇳🇱!

🕰 Explanation: 
    Whenever a change occurs on the website, I will notify you within 30 minutes on which website changes occurred, so you don't have to monitor sites yourself!

📜 How to start:
    By default, I will notify you about changes on every website (full list below) with price range set to "Any" (including all price segments).

🔬 Websites I (currently) check:
    Huurwoningen
    Huurzone
    Kamernet
    Pararius
    Room (student housing)
    Spotahome
    Studentenwoningweb (student housing)
    Uniplaces


If you wish to change my settings, below you will find "Filters"

If you are stuck to find settings, just type /help or /start and this message will appear

"""
        response = requests.post(self.BASE_URL + 'sendMessage',
                                 data={'chat_id': chat_id, 'text': welcome_text,
                                       'reply_markup': json.dumps({'inline_keyboard': [
                                           [{'text': 'Filter price', 'callback_data': 'option_filter'},
                                            {'text': 'Test notifications', 'callback_data': 'option_test'}
                                            ],
                                           [
                                               {'text': 'Mute notifications', 'callback_data': 'option_notifications'},
                                               {'text': 'Support project',
                                                'url': 'https://www.buymeacoffee.com/allegedlyrigid',
                                                'callback_data': 'option_support'},
                                           ]
                                       ]})})
        return response.json()
