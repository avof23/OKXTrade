import json
import os
from dotenv import load_dotenv

import okx.Account as Account
import okx.MarketData as MarketData

load_dotenv()
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
PASSPHRASE = os.getenv("PASSPHRASE")

# flag='0' — реальные торги, flag='1' — демо-режим (песочница)
flag = '1'



# Модуль для работы с балансом и аккаунтом
account_api = Account.AccountAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)

# Модуль для чтения рыночных данных (стаканы, цены)
market_api = MarketData.MarketAPI(use_server_time=False, flag=flag)

# Баланс
result_balance = account_api.get_account_balance()
#print("Баланс:", result_balance)

# Цена тикера
#result_ticker = market_api.get_ticker(instType="SPOT", instId="BTC-USDT")
#print("Данные тикера:", result_ticker)

#read_balance = json.load(result_balance)
beautiful_json = json.dumps(result_balance, indent=4, ensure_ascii=False)
print(beautiful_json)