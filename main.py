from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

import requests
import string
import time
import json
import os

REGION = 'en_US'
PATCH = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
CHAMPIONS_DATA = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{PATCH}/data/{REGION}/champion.json').json()['data']
CHAMPIONS_LIST = [champion_name for champion_name in CHAMPIONS_DATA.keys()]

# TODO: Create the following variable using a lambda
CHAMPIONS_DIFFICULTY = {
    champion: {'difficulty': CHAMPIONS_DATA[champion]['info']['difficulty']}
    for champion in CHAMPIONS_DATA.keys()
}


def scraper():
    base_url = 'https://www.leagueofgraphs.com/champions/'
    scrapped_data = dict()

    driver = webdriver.Chrome()
    driver.maximize_window()

    print(f'Scraping data, this should take around {round(len(CHAMPIONS_LIST) / 1.8)} seconds...')

    # Load the page
    driver.get(base_url + 'winrates-by-xp/diamond')

    # Dark theme
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CLASS_NAME, 'switch'))).click()
    WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div/div/div/table/tbody/tr[1]/th[2]'))).click()

    # Get the data
    WIN_RATE_BY_EXPERIENCE = [
        float(element.text[:-1]) 
        for index, element in enumerate(WebDriverWait(driver, 10).until(expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, 'progressBarTxt')))) 
        if index % 3 == 2
    ]

    for champion in zip(CHAMPIONS_LIST, WIN_RATE_BY_EXPERIENCE):
        # Load the page
        driver.get(base_url + 'stats/' + ''.join([c for c in champion[0].lower() if c in string.ascii_lowercase]) + '/diamond')

        # Retrieve some data
        popularity, win_rate, ban_rate, mains = (
            float(WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, f'graphDD{graph_index}'))).text[:-1])
            for graph_index in range(1, 5)
        )

        scrapped_data[champion[0]] = {
            'popularity': popularity,
            'win_rate': win_rate,
            'ban_rate': ban_rate,
            'mained_by': mains,
            'riot_difficulty': CHAMPIONS_DIFFICULTY[champion[0]]['difficulty'],
            'win_rate_by_experience': champion[1]
        }

        # This is not a distributed denial-of-service attack
        time.sleep(0.5)

    with open('save.json', 'w+') as f:
        f.write(json.dumps({**{'patch': PATCH, 'date': time.time()}, **scrapped_data}, indent=4))


if __name__ == '__main__':
    if os.path.exists('save.json'):
        with open('save.json', 'r') as f:
            data = json.loads(f.read())
            if data['patch'] == PATCH and data['date'] > time.time() - 86400:
                print(f"Data is up to date (patch {data['patch']})", f"\n{'- * ' * 7}-")
            else:
                scraper()
    else:
        scraper()
    
    with open('save.json', 'r') as f:
        data = json.loads(f.read())

    points = [
        round((data[champion]['popularity'] - data[champion]['mained_by'] + data[champion]['ban_rate'] - data[champion]['win_rate_by_experience'] / 2) * (data[champion]['win_rate'] / 3))
        for champion in data
        if champion not in ('patch', 'date')
    ]

    for champion in zip(points, CHAMPIONS_LIST):
        if champion[0] >= 750:
            print(champion[1] + ' needs a huge nerf')
        elif champion[0] >= 650:
            print(champion[1] + ' needs a big nerf')
        elif champion[0] >= 550:
            print(champion[1] + ' needs a small nerf')
        elif champion[0] <= -70:
            print(champion[1] + ' needs a huge buff')
        elif champion[0] <= -35:
            print(champion[1] + ' needs a big buff')
        elif champion[0] <= 0:
            print(champion[1] + ' needs a small buff')
        else:
            pass
