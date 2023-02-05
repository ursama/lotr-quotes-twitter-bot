from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementNotVisibleException
from dotenv import load_dotenv
import random
import os
import time
import requests

# Loads environmental variables and checks if they were imported correctly
load_dotenv()

CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')
TWITTER_EMAIL = os.getenv('TWITTER_EMAIL')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
# Access token to The One API
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
# A path to my UserData directory
USER_DATA = os.getenv('USER_DATA')
if not CHROME_DRIVER_PATH or not TWITTER_EMAIL or not TWITTER_PASSWORD or not ACCESS_TOKEN or not USER_DATA or \
        type(CHROME_DRIVER_PATH) != str or type(TWITTER_EMAIL) != str or type(TWITTER_PASSWORD) != str or \
        type(ACCESS_TOKEN) != str or type(USER_DATA) != str:
    print('error loading env variables')

# Loads cookies, so I don't need to log in repetitively
options = Options()
options.add_argument(USER_DATA)
options.page_load_strategy = 'normal'


class QuotesBot:
    def __init__(self):
        service = Service(CHROME_DRIVER_PATH)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.headers = {
            "Authorization": "Bearer " + ACCESS_TOKEN
        }
        self.quote = ""

    def get_quote(self):
        # Gets the quote
        response = requests.get(url="https://the-one-api.dev/v2/quote", headers=self.headers)
        response.raise_for_status()
        quotes = response.json()["docs"]

        # Checks if length of the quote is not too short but also suitable for a twitter post
        # If it's not right, it searches another one
        not_found = True
        while not_found:
            quote_dict = quotes[random.randint(1, len(quotes))]
            if 15 < len(quote_dict['dialog']) < 240:
                not_found = False
                # Searches a character that said the line and searches another quote, if it comes from a minor character
                response = requests.get(url=f"https://the-one-api.dev/v2/character/{quote_dict['character']}",
                                        headers=self.headers)
                response.raise_for_status()
                character = response.json()['docs'][0]['name']
                if character == "MINOR_CHARACTER":
                    not_found = True

        self.quote = f"{quote_dict['dialog']} ~ {character}"

    def tweet_quote(self):
        self.driver.get('https://twitter.com/?lang=en')
        time.sleep(2)

        # Gets a new quote
        self.get_quote()

        # Posts a tweet
        self.driver.find_element(By.XPATH, '//*[@id="react-root"]/div/div/div[2]/header/div/div/div/div[1]/div[3]/a/'
                                 'div').click()
        time.sleep(2)
        textbox = self.driver.find_element(By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/'
                                           'div/div/div[3]/div[2]/div[1]/div/div/div/div/div[2]/div[1]/div/div/div/div/'
                                           'div/div[2]/div/div/div/div/label/div[1]/div/div/div/div/div/div[2]/div')
        textbox.send_keys(self.quote)
        self.driver.find_element(By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div/div'
                                 '[3]/div[2]/div[1]/div/div/div/div/div[2]/div[3]/div/div/div[2]/div[4]').click()
        self.driver.close()


def main():
    # Sometimes there are some pop-ups on the main page and I couldn't find their xpath cause I can't get the pop-up
    # appear now, when I need it :) So I just repeat the whole process with faith that it won't happen again
    tweeted = False
    while not tweeted:
        try:
            bot = QuotesBot()
            bot.tweet_quote()
            tweeted = True
        except ElementNotVisibleException:
            pass


if __name__ == '__main__':
    main()
