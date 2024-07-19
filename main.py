import selenium
import pandas as pd
import numpy as np
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PrettyColorPrinter import add_printer
from arbitrage import check_arbitrage

add_printer(1)

try:
    # abrindo site
    driver = Driver(uc=True)
    driver.get(
        'https://www.flashscore.com.br/'
    )

    # clique no botao de cookies
    cookies_accept = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
    )
    cookies_accept.click()

    more = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button._accordion_1gb8n_4 span'))
    )
    list_more = [m for m in more]

    for m in list_more:
        if 'exibir jogos' in m.text:
            m.click()

    # partida
    matches = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.eventRowLink'))
    )

    original_window = driver.current_window_handle

    for match in matches:
        driver.execute_script("arguments[0].click();", match)
        all_windows = driver.window_handles
        for window in all_windows:
            if window != original_window:
                driver.switch_to.window(window)
                break
        
        header_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button._tab_myv7u_4'))
        )
        header = [btn for btn in header_btn]
        header[1].click()

        df_arbitrage = pd.DataFrame()

        try:
            odds = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.oddsCell__odd span'))
            )
            list_odds = [float(odd.text) for odd in odds]

            bet_names = driver.find_elements(By.CSS_SELECTOR, 'img.prematchLogo')
            list_bet_name = [bet.get_attribute('title') for bet in bet_names]

            team_names = driver.find_elements(By.CSS_SELECTOR, 'a.participant__participantName')
            list_team_name = [team.text for team in team_names]

            if len(list_team_name) >= 2 and len(list_odds) >= len(list_bet_name) * 3:
                df_arbitrage['team_name_1'] = [list_team_name[0]]
                df_arbitrage['team_name_2'] = [list_team_name[1]]

            overall_counter = 0
            for bet in list_bet_name:
                for odd_counter in range(1, 4):
                    column_name = f'{bet}_odd_{odd_counter}'
                    if column_name not in df_arbitrage:
                        df_arbitrage[column_name] = [list_odds[overall_counter]]
                    else:
                        df_arbitrage.at[0, column_name] = list_odds[overall_counter]
                    overall_counter += 1

            print(df_arbitrage)

            check_arbitrage(df_arbitrage, list_bet_name)

        except Exception as e:
            print(f'Ocorreu um erro ao raspar as odds: {e}')

        driver.close()
        driver.switch_to.window(original_window)

except Exception as exception:
    print('Ocorreu algum erro durante a requisição de dados\n\nMais informações:\n', exception)
    driver.quit()