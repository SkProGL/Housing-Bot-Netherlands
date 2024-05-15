import shutil
import time
from datetime import datetime
from random import randrange

import schedule
from pyngrok import ngrok

from BotCommander import BotCommander
from DatabaseControl import DatabaseControl
from Monitoring import Monitoring

NGROK_TOKEN = 'NGROK_TOKEN_KEY'
port = 3000


class EventSchedule:

    # compares monitored and database data
    def compare_data(self, data, dictionary, id=''):
        changes = ''
        for i in range(len(data)):
            count = int(data[i]['count'])
            name = data[i]['name']
            url = data[i]['url']
            if count != dictionary[name][0]:
                # print(f"[schedule] {name} {count} compared to {db_price[i]}")
                if count < dictionary[name][0] and data[i]['url'] == dictionary[name][1] or count < 0:
                    # print(f'[schedule] {name} number of housings decreased without adding new listings')
                    continue
                changes += f"{name} (total of {count})\n"
                changes += f"link: {url}\n\n" if len(url) > 0 else '\n'
                DatabaseControl('housing.db').update('current_data', {'price' + id: count, 'url' + id: url},
                                                     f'website_name = "{name}"')
        return changes

    def monitor(self):
        now = datetime.now()
        hours = now.strftime('%H')
        minutes = now.strftime('%M')
        # monitor less in the nighttime
        if int(hours) in [1, 3, 5, 7] or int(hours) in [2, 4, 6, 8] and int(minutes) == 30:
            return

        delay = randrange(90)
        time.sleep(delay)
        print("[schedule] monitoring, time delay " + str(delay) + ", " + str(time.strftime('%H:%M:%S')))

        monitor = Monitoring()

        prices = [None, 500, 1000]

        # loop through 3 states of filter ids, and update table
        print('========================================')
        for i in range(3):
            print(i)
            price_filter = monitor.filter(prices[i])
            id = '_' + str(i) if i > 0 else ""

            merged_columns = DatabaseControl('housing.db').select_columns(f'website_name, price{id}, url{id}',
                                                                          'current_data')
            temp_dictionary = {}
            for j in merged_columns:
                temp_dictionary[j[0]] = [j[1], j[2]]

            changes = self.compare_data(price_filter, temp_dictionary, id)
            # if changes occurred
            if len(changes) > 0:
                # loop through chat ids
                for j in DatabaseControl('user.db').select_column('chat_id', 'online_user'):
                    filter_id = DatabaseControl('user.db').select('online_user', f'chat_id = {j}', 'filter_id')[0][0]
                    state = DatabaseControl('user.db').select('online_user', f'chat_id = {j}', 'notifications')[0][0]
                    if filter_id == i and state == 1:
                        BotCommander().send_message(j, f'Filter: max price {prices[i]} EUR\n\n{changes}')
            time.sleep(randrange(20))

        for i in DatabaseControl('housing.db').select('current_data'):
            print(i)

    def backup_data(self):
        shutil.copyfile('user.db', "backup/user_" + str(datetime.now().strftime('%d%m%y')) + ".db")
        pass

    def update_webhook(self):
        print("[schedule] update webhook " + str(time.strftime('%H:%M:%S')))

        for i in ngrok.get_tunnels():
            print(f'[schedule] closing tunnel: {i.public_url}')
            ngrok.disconnect(i.public_url)

        with open('webhook.txt', 'w+')as f:
            tunnel = ngrok.connect(port)
            ngrok.set_auth_token(NGROK_TOKEN)
            BotCommander().set_webhook(str(tunnel.public_url) + '/webhook')
            f.write(str(tunnel.public_url))

    def run_schedule(self):
        print('[schedule] starting...')
        schedule.every().hours.at(":25").do(self.monitor)
        schedule.every().hours.at(":55").do(self.monitor)
        # schedule.every(2).hours.at(":45").do(self.update_webhook)
        schedule.every().day.at("23:50").do(self.backup_data)

        while True:
            schedule.run_pending()
            time.sleep(1)
