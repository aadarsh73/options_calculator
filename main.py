from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import pyotp
import py_vollib.black.greeks.analytical
import py_vollib.black.implied_volatility
from datetime import datetime
from config import pin, user_id, totp_token

symbol = 'BANKNIFTY'
expiry = '2023-07-27'

def calculate_implied_volatility(row):
    global r, t, flag
    if flag=='c':
        return py_vollib.black.implied_volatility.implied_volatility(row['ce_ltp'], row['futures_price'], row['strike'], r, t, flag)
    elif flag=='p':
        return py_vollib.black.implied_volatility.implied_volatility(row['pe_ltp'], row['futures_price'], row['strike'], r, t, flag)
    
def calculate_black(row):
    global r, t, flag
    if flag=='c':
        return py_vollib.black.black(flag, row['futures_price'], row['strike'], t, r, row['sigma_ce'])
    elif flag=='p':
        return py_vollib.black.black(flag, row['futures_price'], row['strike'], t, r, row['sigma_pe'])

def calculate_delta(row):
    global r, t, flag
    if flag=='c':
        return py_vollib.black.greeks.analytical.delta(flag, row['futures_price'], row['strike'], t, r, row['sigma_ce'])
    elif flag=='p':
        return py_vollib.black.greeks.analytical.delta(flag, row['futures_price'], row['strike'], t, r, row['sigma_pe'])
    
def calculate_gamma(row):
    global r, t, flag
    if flag=='c':
        return py_vollib.black.greeks.analytical.gamma(flag, row['futures_price'], row['strike'], t, r, row['sigma_ce'])
    elif flag=='p':
        return py_vollib.black.greeks.analytical.gamma(flag, row['futures_price'], row['strike'], t, r, row['sigma_pe'])
    
def calculate_theta(row):
    global r, t, flag
    if flag=='c':
        return py_vollib.black.greeks.analytical.theta(flag, row['futures_price'], row['strike'], t, r, row['sigma_ce'])
    elif flag=='p':
        return py_vollib.black.greeks.analytical.theta(flag, row['futures_price'], row['strike'], t, r, row['sigma_pe'])
    
def calculate_vega(row):
    global r, t, flag
    if flag=='c':
        return py_vollib.black.greeks.analytical.vega(flag, row['futures_price'], row['strike'], t, r, row['sigma_ce'])
    elif flag=='p':
        return py_vollib.black.greeks.analytical.vega(flag, row['futures_price'], row['strike'], t, r, row['sigma_pe'])

expiry_time = datetime.strptime(expiry, '%Y-%m-%d')
options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

driver.maximize_window()
driver.get("https://login.5paisa.com/")

# Login to 5paisa
input_box = driver.find_element(By.XPATH, '//*[@id="loginUser"]')
input_box.send_keys(user_id)
print('input user id')
proceed_button = driver.find_element(By.XPATH, '//*[@id="btnGenerateOTP"]')
proceed_button.click()
print('generating totp')
totp = pyotp.TOTP(totp_token).now()
try:
    totp_input = driver.find_element(By.XPATH, '//*[@id="dvLoginTOTP1"]')
    totp_input.send_keys(totp)
    print('totp entered')
    
    verify_button = driver.find_element(By.XPATH, '//*[@id="btnVerifyTOTP"]')
    verify_button.click()
except:
    print('totp not required')
time.sleep(3)
print('entering pin')
pin_input = driver.find_element(By.CSS_SELECTOR, '#dvPin1')
pin_input.click()
pin_input.send_keys(pin)
print('submitting login details')
try:
    submit_button = driver.find_element(By.XPATH, '//*[@id="btnPINSubmit"]')
    submit_button.click()
except:
    driver.find_element(By.XPATH, '//*[@id="btnPINlinkingLimitYes"]').click()
    
try:
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="btnPINlinkingLimitYes"]').click()
except: 
    print('')
time.sleep(10)

print('logged in successfully')

dropdown = driver.find_element(By.XPATH, '//*[@id="dropdownMenuButton"]')
dropdown.click()


research_button = driver.find_element(By.XPATH, '//*[@id="mCSB_6_container"]/div[4]/h3/span')
research_button.click()

sensibull_button = driver.find_element(By.XPATH, '//*[@id="mCSB_6_container"]/div[4]/p/a[2]')
sensibull_button.click()
print('redirecting to sensibull')
time.sleep(5)
print('changing tabs')
chwd = driver.window_handles
for w in chwd:
    driver.switch_to.window(w)
time.sleep(10)
analyse_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[3]/div[1]/div/ul/li[2]/button')
analyse_button.click()
option_chain_button = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[3]/div[1]/div/ul/li[2]/div/div/ul[1]/li[1]/a')
option_chain_button.click()
print('loading option chain data')
time.sleep(3)

url = f'https://web.sensibull.com/option-chain?expiry={expiry}&tradingsymbol={symbol}'
driver.get(url)
time.sleep(3)
print('fetching data...')

while True:
    time.sleep(3)
    data = driver.find_elements(By.CSS_SELECTOR, '.rt-tr-group .rt-tr .rt-td')
    data = [x.text for x in data]
    # ce_oi_change = data[::8]
    # ce_oi = data[1::8]
    ce_ltp = data[2::8]
    strike = data[3::8]
    pe_ltp = data[5::8]
    # iv = data[4::8]
    # pe_oi_change = data[5::8]
    # pe_oi = data[6::8]
    
    print(len(ce_ltp), len(strike),len(pe_ltp))
    df = pd.DataFrame({
        'ce_ltp': ce_ltp,
        'strike': strike,
        'pe_ltp': pe_ltp,
    })
    
    contains_hyphen = df.apply(lambda x: x.str.contains('-'))
    rows_with_hyphen = contains_hyphen.any(axis=1)
    df = df[~rows_with_hyphen]
    
    df['ce_ltp'] = df['ce_ltp'].astype(float)
    df['strike'] = df['strike'].astype(float)
    df['pe_ltp'] = df['pe_ltp'].astype(float)
    df['futures_price'] = df['strike'] + df['ce_ltp'] - df['pe_ltp']
    print(df)
    today = datetime.today()
    expiry_days = (expiry_time - today).days
    expiry_years = expiry_days / 365  
    t = expiry_years
    flag =  'c'
    r = 0.00
    
    df['sigma_ce'] = df.apply(calculate_implied_volatility, axis=1)
    df['delta_ce'] = df.apply(calculate_delta, axis = 1)
    df['gamma_ce'] = df.apply(calculate_gamma, axis = 1)
    df['theta_ce'] = df.apply(calculate_theta, axis = 1)
    df['vega_ce'] = df.apply(calculate_vega, axis = 1)
    df['premia_ce'] = df.apply(calculate_black, axis=1)
    
    flag = 'p'
    
    df['sigma_pe'] = df.apply(calculate_implied_volatility, axis=1)
    df['delta_pe'] = df.apply(calculate_delta, axis = 1)
    df['gamma_pe'] = df.apply(calculate_gamma, axis = 1)
    df['theta_pe'] = df.apply(calculate_theta, axis = 1)
    df['vega_pe'] = df.apply(calculate_vega, axis = 1)
    df['premia_pe'] = df.apply(calculate_black, axis=1)
    
    df.to_csv('data.csv')
    print(df)






