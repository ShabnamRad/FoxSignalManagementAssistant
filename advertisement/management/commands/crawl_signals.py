import json
import os
import time
from datetime import datetime

import bs4
import requests
from django.core.management import BaseCommand
from selenium import webdriver

from advertisement.models import Signal, Expert, Symbol


class Command(BaseCommand):
    help = 'crawls the signals from 100tahlil.com and inserts them into the database'

    def handle(self, *args, **options):
        # It run the chromedriver on OS X
        # On Windows or linux change it to chromedriver.exe or chromedriver_linux respectively
        os.chdir(os.path.dirname(__file__))
        self.browser = webdriver.Chrome('./chromedriver_mac')
        self.browser.get('https://100tahlil.com/BrokerInfo/Stock-Market-Analysts/sadtahlilAlgo$19$0$3$0$1')

        time.sleep(3)

        plus_button = self.browser.find_element_by_xpath('//a[@data-id="8"][@data-type="sadtahlilAlgo"]')

        user_data = []
        for i in range(40):
            plus_button.click()
            time.sleep(2)
        soup = bs4.BeautifulSoup(self.browser.page_source, features="html.parser")
        for div in soup.select("div.col-lg-3.col-md-3.col-sm-6.padding-10"):
            user_data.append([div.select_one('span.size-14.bold').getText(),
                                   div.select_one('a.hvr-color-theme').get('href').split('/')[-1]])
        print('Crawled the user data')

        for data in user_data:
            self.get_insert_predictions(data[0], data[1])

    def get_insert_predictions(self, user_name, user_id):
        url = 'https://100tahlil.com/Account/AnalyzerEstimateHistory?f=all&bid=%s&isPortfo=false&isclosed=true' % user_id

        predictions_list = json.loads(requests.get(url).text)

        for item in predictions_list:
            url2 = 'https://100tahlil.com/Estimate/EstimateDetailModal/' + str(item['Id'])
            self.browser.get(url2)
            expected_return = self.browser.find_element_by_xpath('//tr[@data-dt-column="1"]/td[2]').text
            expected_risk = self.browser.find_element_by_xpath('//tr[@data-dt-column="2"]/td[2]').text

            expert, _ = Expert.objects.get_or_create(display_name=user_name)
            symbol, _ = Symbol.objects.get_or_create(name=item['CompanyName'])
            Signal.objects.create(title='', is_succeeded=item['Successed'], profit=item['ProfitPercentage'],
                                  start_date=datetime.fromtimestamp(int(item['EstimateDate'][6:-5])),
                                  close_date=datetime.fromtimestamp(int(item['ClosingDate'][6:-5])),
                                  expected_return=float(expected_return[1:]), expected_risk=float(expected_risk[1:]),
                                  expert=expert, symbol=symbol)

        print('Done for Expert:', user_name)