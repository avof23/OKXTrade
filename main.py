import json
import os
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN

import okx.Account as Account
import okx.MarketData as MarketData

load_dotenv()
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
PASSPHRASE = os.getenv("PASSPHRASE")

# flag='0' — реальные торги, flag='1' — демо-режим (песочница)
flag = '1'
format_balance = Decimal("0.00001")

def start_api():
    print("Welcome to simple trading script")
    account_api = Account.AccountAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)
    return account_api


def show_json(datajson):
    """Показать полный dump json данных"""

    beautiful_json = json.dumps(datajson, indent=4, ensure_ascii=False)
    print(beautiful_json)


def get_balace_trade(api):
    """Получить баланс по trading аккаунту"""
    result_balance = api.get_account_balance()
    return [{"ticker": val["ccy"], "balance": val["eq"]} for val in result_balance["data"][0]["details"]]


def show_balance_trade(short_balance):
    for item in short_balance:
        print(f'{item["ticker"]} = {Decimal(item["balance"]).quantize(format_balance, rounding=ROUND_DOWN)}')

def get_price_ticker(api, ticker: str) -> str:
    result_ticker = api.get_ticker(instType="SPOT", instId=ticker)
    return result_ticker

# Модуль для чтения рыночных данных (стаканы, цены)
#market_api = MarketData.MarketAPI(use_server_time=False, flag=flag)


if __name__ == "__main__":
    api = start_api()
    balance = get_balace_trade(api)
    show_balance_trade(balance)
    #show_json(balance)
