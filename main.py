import json
import threading
import time

from flask import Flask, request
from pyngrok import ngrok

from BotCommander import BotCommander
from DatabaseControl import DatabaseControl
from EventSchedule import EventSchedule
from Monitoring import Monitoring

app = Flask(__name__)
bot = BotCommander()


# last_active_users = []

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()

    if 'callback_query' in update:
        callback_query = update['callback_query']
        print('[server] options response expected')
        # print(json.dumps(callback_query, indent=4))
        callback_response(callback_query)
    else:
        # last_active_users.append({'chat_id': update['message']['chat']['id'], 'timestamp': update['message']['date']})
        print('[server] message response expected')
        # print(json.dumps(update, indent=4))

        message_response(update)
    return "Webhook received successfully", 200


def message_response(update):
    try:
        user = DatabaseControl('user.db')

        chat_id = update['message']['chat']['id']
        chat = update['message']['chat']
        text = update['message']['text']
        if text in ('/start', '/help'):
            print('[server] register User')
            print(update)
            if update['message']['from']['is_bot'] == True:
                return
            if user.exists('online_user', f"chat_id = {chat_id}") is False:
                user.insert('online_user', {'chat_id': chat_id,
                                            'first_name': chat['first_name'],
                                            'last_name': chat['last_name'],
                                            'register_date': bot.get_current_date(),
                                            'status': 'default',
                                            'filter_id': 1,
                                            'notifications': 1,
                                            })
                bot.send_message(chat_id, "You have successfully registered for notifications!")
                time.sleep(2)

            bot.welcome_message(chat_id)
        if text in '/online':
            user_count = DatabaseControl('user.db').count_rows('online_user', 'chat_id')
            if user_count:
                bot.send_message(chat_id, "Current number of users: " + str(user_count))
            else:
                bot.send_message(chat_id, "Current number of users: not applicable")
        elif 'entities' not in update['message']:
            bot.send_message(chat_id, "Please click or type: /help or /start to open bot menu!")


    except Exception as e:
        print('[server] message response error ' + str(e))


def callback_response(callback_query):
    try:
        message_id = callback_query['message']['message_id']
        chat_id = callback_query['message']['chat']['id']
        if callback_query['data'] == "option_filter":
            bot.edit_message(chat_id, message_id, 'Please select max price: ', json.dumps({'inline_keyboard': [
                [{'text': '<500', 'callback_data': 'filter_1'}, {'text': '<1000', 'callback_data': 'filter_2'},
                 {'text': 'Any', 'callback_data': 'filter_0'}, ]]}))
        elif callback_query['data'] == "option_test":
            bot.edit_message(chat_id,
                             message_id,
                             bot.TEST_NOTIFICATIONS)
            time.sleep(2)
            bot.send_message(chat_id, bot.TEST_EXAMPLE)
        elif callback_query['data'] == "option_notifications":
            notifications = \
                DatabaseControl('user.db').select('online_user', f'chat_id = {chat_id}', 'notifications')[0][0]
            state = 1 if int(notifications) == 0 else 0
            DatabaseControl('user.db').update('online_user', {'notifications': state}, f'chat_id = {chat_id}')
            state = 'off' if state == 0 else 'on'
            time.sleep(2)
            bot.edit_message(chat_id,
                             message_id,
                             f"Notifications turned {state}!")
        if 'filter_' in callback_query['data']:
            category = int(callback_query['data'].replace('filter_', ''))
            if 3 > category >= 0:
                DatabaseControl('user.db').update('online_user', {'filter_id': category}, f'chat_id = {chat_id}')
                bot.edit_message(chat_id, message_id, "Filters were successfully applied!")
    except Exception as e:
        print('[server] callback response error ' + str(e))


def setup_flask(token, port, run_once=False):
    try:
        tunnel = ngrok.connect(port)
        ngrok.set_auth_token(token)
        bot.set_webhook(str(tunnel.public_url) + '/webhook')
        with open('webhook.txt', 'w+')as f:
            f.write(tunnel.public_url)
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print('[flask] setup exception ' + str(e))
        if run_once:
            return
        print('[flask] restarting ngrok server...')
        setup_flask(token, port, True)


def setup_housing_database(clean=False):
    print('[server] housing database setup')
    housing = DatabaseControl('housing.db')
    housing.create_table('current_data', housing.accommodation_default_table)

    # remove all data within table
    if clean:
        housing.delete_table('current_data')
        housing.create_table('current_data', housing.accommodation_default_table)

        for i in Monitoring().websites:
            housing.insert('current_data', {'website_name': i, 'price': 0, 'price_1': 0, 'price_2': 0})


def setup_user_database(clean=False):
    print('[server] user database setup')
    temp = DatabaseControl('user.db')
    temp.create_table('online_user', temp.user_default_table)

    # remove all data within table
    if clean:
        temp.delete_table('online_user')
        temp.create_table('online_user', temp.user_default_table)


def run_tests():
    try:
        # setup_housing_database(True)
        # setup_user_database(True)

        print(f"[test] total number of users: {DatabaseControl('user.db').count_rows('online_user', 'chat_id')}")


        housing = DatabaseControl('housing.db')
        for i in Monitoring().websites:
            if housing.exists('current_data', f'website_name = "{i}"') is False:
                housing.insert('current_data', {'website_name': i, 'price': 0, 'price_1': 0, 'price_2': 0})
                print('[test] website added to database ' + i)
        print(housing.select('current_data'))
        for i in Monitoring().filter():
            print(i)
        return True
    except Exception as e:
        print('[test] testing error ' + str(e))
        return False


if __name__ == "__main__":
    print("[server] " + str(time.strftime('%H:%M:%S')) + " starting...")
    print(Monitoring().filter(500))
    NGROK_TOKEN = 'NGROK_TOKEN_KEY'
    if run_tests():
        print('[test] tests passed succesfully, loading server')
        time.sleep(5)
        thread1 = threading.Thread(target=setup_flask, args=[NGROK_TOKEN, 3000])
        thread2 = threading.Thread(target=EventSchedule().run_schedule)
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
