import json
import os
import sys

from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN

import okx.Account as Account
import okx.Funding as Funding
import okx.Trade as Trade
import okx.MarketData as MarketData


load_dotenv()
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
PASSPHRASE = os.getenv("PASSPHRASE")

# flag='0' — реальные торги, flag='1' — демо-режим (песочница)
flag = '1'
format_balance = Decimal("0.00001")


class OKXAPIError(Exception):
    pass

class OkxApiInterface():
    def __init__(self):
        self.account_api = Account.AccountAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)
        self.funding_api = Funding.FundingAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)
        self.trade_api = Trade.TradeAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)

    # def start_api(self):
    #     account_api = Account.AccountAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)
    #     return account_api

    def show_json(self, datajson):
        """Показать полный dump json данных"""
        beautiful_json = json.dumps(datajson, indent=4, ensure_ascii=False)
        print(beautiful_json)

    def get_balace_trade(self):
        """Получить баланс по trading аккаунту"""
        result_trading_balance = self.account_api.get_account_balance()

        if result_trading_balance.get("code") != "0":
            error_msg = result_trading_balance.get('msg', 'Unknown error')
            raise OKXAPIError(f"Error OKX: {error_msg}")

        data = result_trading_balance.get("data")
        if not data:
            return []

        details = data[0].get("details", [])

        return [{
            "ticker": val.get("ccy", "Unknown"),
            "balance": val.get("eq", "0"),
            "balanceUSD": val.get("eqUsd", "0"),
        } for val in details]

    def get_balance_funding(self):
        """Получить баланс по основному аккаунту"""
        result_funding_balance = self.funding_api.get_balances()

        if result_funding_balance.get("code") != "0":
            error_msg = result_funding_balance.get('msg', 'Unknown error')
            raise OKXAPIError(f"Error OKX: {error_msg}")

        data = result_funding_balance.get("data")
        if not data:
            return []

        return [{
            "ticker": asset.get("ccy"),
            "balance": asset.get("bal"),
            "availBal": asset.get("availBal")
        } for asset in data]

    def show_balance_trade(self, short_balance):
        for item in short_balance:
            print(f'{item["ticker"]} = {Decimal(item["balance"]).quantize(format_balance, rounding=ROUND_DOWN)}')

    def get_price_ticker(self, ticker: str) -> str:
        result_ticker = self.account_api.get_ticker(instType="SPOT", instId=ticker)
        return result_ticker

    # Модуль для чтения рыночных данных (стаканы, цены)
    # market_api = MarketData.MarketAPI(use_server_time=False, flag=flag)