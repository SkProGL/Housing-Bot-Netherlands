import inspect
import json

import requests
from bs4 import BeautifulSoup


class Monitoring:
    headers = {'User-Agent': 'Mozilla/5.0', "content-type": "application/json; charset=UTF-8"}

    HUURWONINGEN_URL = "https://www.huurwoningen.nl/in/amsterdam/"
    HUURZONE_URL = "https://www.huurzone.nl/huurwoningen/amsterdam?page=1&sort_by=price_asc&autocomplete_identifier=Y2l0eS9hbXN0ZXJkYW0"
    KAMERNET_URL = "https://kamernet.nl/en/for-rent/rooms-amsterdam"
    PARARIUS_URL = "https://www.pararius.nl/huurwoningen/amsterdam/"
    ROOM_URL = "https://roomapi.hexia.io/api/v1/actueel-aanbod?limit=100&locale=nl_NL&page=0&sort=-publicationDate"
    SPOTAHOME_URL = "https://www.spotahome.com/s/amsterdam--netherlands?"
    STUDENTENWONING_URL = "https://www.studentenwoningweb.nl/webapi/zoeken/find/"
    UNIPLACES_URL = "https://www.uniplaces.com/accommodation/amsterdam"

    websites = ['huurwoningen', 'huurzone', 'kamernet', 'pararius', 'roomnl', 'spotahome', 'studentwoningen',
                'uniplaces']

    def url_parameters(self, **kwargs):
        result = ""
        for arg in kwargs.items():
            result += f"&{arg[0]}={arg[1]}"
            if arg[1] == None:
                return ""
        return result

    def make_request(self, url, data, load_json=True, method=''):
        try:
            data = json.dumps(data).encode("utf-8")
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            else:
                response = requests.post(url, data=data, headers=self.headers)

            return response.json() if load_json else response.text
        except Exception as e:
            print("[monitoring] make_request error " + str(e))
            return None

    def bs_selector(self, response, count, url=None):
        try:
            selector = BeautifulSoup(response, "html.parser")
            count = selector.select_one(count).text
            url = selector.select_one(url) if url is not None else ""
            if url:
                url = url.get('href')
            return [count, url]
        except Exception as e:
            print('[monitoring]', inspect.stack()[1].function)
            print('[monitoring] beautifulsoup selector error ' + str(e))
            return [0, '']

    def count_huurwoningen(self, price=None):
        try:
            params = f'?price=0-{price}' if price else ""
            response = self.make_request(self.HUURWONINGEN_URL + params, "", False, 'GET')
            [count, url] = self.bs_selector(response, '.search-list-header__count',
                                            '.listing-search-item__link--title')
            return {'name': 'huurwoningen', 'count': count, 'url': 'https://www.huurwoningen.nl' + str(url)}
        except Exception as e:
            print("[monitoring] huurwoningen error " + str(e))
            return {'name': 'huurwoningen', 'count': -9, 'url': ''}

    def count_huurzone(self, params=None):
        try:
            params = params if params else ""
            response = self.make_request(self.HUURZONE_URL + params, "", False, 'GET')
            [count, url] = self.bs_selector(response, "span.text-huur-primary")
            return {'name': 'huurzone', 'count': str(count).replace('woningen', '').strip(), 'url': ''}
        except Exception as e:
            print("[monitoring] huurzone error " + str(e))
            return {'name': 'huurzone', 'count': -9, 'url': ''}

    def count_kamernet(self, price_id=None):
        try:
            price_id = price_id / 100 if price_id else -1
            # RentalPriceId, -1 (any), 5 (max 500), 10 (max 1000)
            data = {"Variant": "", "PageNumber": "1", "DontFecthEarlyBird": "False", "SearchResults.SearchView": "Tile",
                    "SearchResults.ResultType": "Search", "IsNoResultsPage": "False", "SortId": "1", "StreetName": "",
                    "StreetSlug": "", "LocationText": "Amsterdam", "RadiusId": "1", "RentalPriceId": price_id,
                    "SurfaceId": "2", "AvailableFromDate": "", "AvailableFromDate_submit": "",
                    "SuitableForNumberOfPersonsId[]": "-", "CandidateAge[]": "-", "RoommateMaxNumberId[]": "-"}

            response = self.make_request(self.KAMERNET_URL, data, False)
            [count, url] = self.bs_selector(response, '[for="search_results"]', 'a[href].tile-title.truncate')
            # print(url.text) url title
            return {'name': 'kamernet', 'count': count.replace('living places for rent in Amsterdam', '').strip(),
                    'url': str(url)}
        except Exception as e:
            print("[monitoring] kamernet error " + str(e))
            return {'name': 'kamernet', 'count': -9, 'url': ''}

    def count_pararius(self, params=None):
        try:
            params = f'0-{params}' if params else ""
            response = self.make_request(self.PARARIUS_URL + params, "", False)
            [count, url] = self.bs_selector(response, '.search-list-header__count', '.listing-search-item__title a')
            return {'name': 'pararius', 'count': count, 'url': f'https://www.pararius.nl{url}'}
        except Exception as e:
            print("[monitoring] pararius error " + str(e))
            return {'name': 'pararius', 'count': -9, 'url': ''}

    def count_roomnl(self, price=None):
        try:
            if price:
                price = [{"regio.id": {"$eq": "3"}}, {"$or": [{"$and": [
                    {"reactionData.aangepasteNettoHuurprijs": {"$gte": 0}},
                    {"reactionData.aangepasteNettoHuurprijs": {"$lte": price}}]}, {"$or": [
                    {"$and": [{"totaleHuurVan": {"$gte": 0}}, {"totaleHuurVan": {"$lte": price}}]},
                    {"$and": [{"totaleHuurTot": {"$gte": 0}}, {"totaleHuurTot": {"$lte": price}}]}]}]}]
            else:
                price = [{"regio.id": {"$eq": "3"}}]
            data = {"filters": {"$and": [{"$and": price}]}, "hidden-filters": {
                "$and": [{"dwellingType.categorie": {"$eq": "woning"}}, {"isExtraAanbod": {"$eq": ""}},
                         {"isWoningruil": {"$eq": ""}}, {"$and": [{"$or": [{"street": {"$like": ""}},
                                                                           {"houseNumber": {"$like": ""}},
                                                                           {"houseNumberAddition": {"$like": ""}}]}, {
                                                                      "$or": [{"street": {"$like": ""}},
                                                                              {"houseNumber": {"$like": ""}}, {
                                                                                  "houseNumberAddition": {
                                                                                      "$like": ""}}]}]},
                         {"rentBuy": {"$eq": "Huur"}}]}}
            response = self.make_request(self.ROOM_URL, data)
            count = str(len(response['data']))
            url = f"https://www.room.nl/en/offerings/to-rent/details/{response['data'][0]['urlKey']}"
            return {'name': 'roomnl', 'count': count, 'url': url}
        except Exception as e:
            print("[monitoring] room error " + str(e))
            return {'name': 'roomnl', 'count': -9, 'url': ''}

    def count_spotahome(self, price=None):
        try:
            price = '-' + str(price) if price else ""
            site = f'{self.SPOTAHOME_URL}budget=0{price}&sortBy=recentlyListed'

            response = self.make_request(site, "", False, 'GET')
            [count, url] = self.bs_selector(response, '[data-test="search-title"] strong', '.l-list__item a')
            url = 'https://www.spotahome.com' + url if int(count) is not 0 else ""
            return {'name': 'spotahome', 'count': count, 'url': url}
        except Exception as e:
            print("[monitoring] spotahome error " + str(e))
            return {'name': 'spotahome', 'count': -9, 'url': ''}

    def count_studentwoningen(self, price=None):
        try:
            price = f"~huurprijs[300,{price}]" if price else ''
            data = {"url": f"model[Regulier aanbod]~plaatsenwijken[Amsterdam]{price}~sort[publicatie_einddatum,ASC]",
                    "command": "sort[publicatie_einddatum,DESC]",
                    "hideunits": "hideunits[]"}

            response = self.make_request(self.STUDENTENWONING_URL, data)
            url = "https://www.studentenwoningweb.nl" + str(response['Resultaten'][0]['PreviewUrl'])
            return {'name': 'studentwoningen', 'count': str(response["TotalSearchResults"]), 'url': url}
        except Exception as e:
            print("[monitoring] studentenwoning error " + str(e))
            return {'name': 'studentwoningen', 'count': -9, 'url': ''}

    def count_uniplaces(self, price=None):
        try:
            params = (f'?budget-max={price * 100}&' if price else "?") + "order=recency"
            response = self.make_request(self.UNIPLACES_URL + params, "", False)
            [count, url] = self.bs_selector(response, 'h1', 'a')
            count = count[:str(count).index(' ')]
            return {'name': 'uniplaces', 'count': count, 'url': url}
        except Exception as e:
            print("[monitoring] uniplaces error " + str(e))
            return {'name': 'uniplaces', 'count': -9, 'url': ''}

    def filter(self, price=None):
        if price:
            print(f"[filter] {price}")
        else:
            print(f"[filter] any")
        huurwoningen = self.count_huurwoningen(price)
        huurzone = self.count_huurzone(self.url_parameters(price_to=price))
        kamernet = self.count_kamernet(price)
        pararius = self.count_pararius(price)
        spotahome = self.count_spotahome(price)
        uniplaces = self.count_uniplaces(price)
        if price == 500:
            roomnl = self.count_roomnl(price)
            studentwoningen = self.count_studentwoningen(price)
        else:
            roomnl = self.count_roomnl(price)  # user menu does not imply filter of 1000
            studentwoningen = self.count_studentwoningen(price)  # user menu does not imply filter of 1000

        return [huurwoningen, huurzone, kamernet, pararius, roomnl, spotahome, studentwoningen, uniplaces]
