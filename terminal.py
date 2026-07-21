import os
from datetime import datetime
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

    def get_balace_trade(self):
        """
        Получить баланс по trading аккаунту
        """
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
        """
        Получить баланс по основному аккаунту
        """
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

    def transfer_funds(self, currency, amount, direction="to_trade"):
        """
        Переводит средства между Основным и Торговым счетами.

        :param currency: Тикер монеты, например "USDT"
        :param amount: Сумма перевода в виде строки, например "10.5"
        :param direction: Направление. "to_trade" (на торговый) или "to_funding" (на основной)
        """
        # Определяем коды счетов в зависимости от направления
        if direction == "to_trade":
            account_from = "6"  # С Основного
            account_to = "18"  # На Торговый
        elif direction == "to_funding":
            account_from = "18"  # С Торгового
            account_to = "6"  # На Основной
        else:
            raise ValueError("Unknown transfer directions")

        response = self.funding_api.funds_transfer(
            ccy=currency,
            amt=str(amount),
            from_=account_from,
            to=account_to
        )

        if response.get("code") != "0":
            error_msg = response.get('msg', 'Unknown transfer error')
            raise OKXAPIError(f"Error transfer OKX: {error_msg}")

        data = response.get("data", [])
        if data:
            trans_id = data[0].get("transId")
            return trans_id

        return None

    def get_price_ticker(self, ticker: str) -> str:
        result_ticker = self.account_api.get_ticker(instType="SPOT", instId=ticker)
        return result_ticker

    def place_spot_order(self, inst_id, side, ord_type, amount_str, price_str=None, is_usdt=False):
        """
        Отправляет SPOT ордер.
        :param inst_id: Тикер, например "BTC-USDT"
        :param side: Направление: "buy" или "sell"
        :param ord_type: Тип ордера: "market" или "limit"
        :param amount_str: Количество или сумма (строка)
        :param price_str: Цена ордера (только для лимитных)
        :param is_usdt: True, если amount_str указан в USDT, False если в крипте
        """
        params = {
            "instId": inst_id.upper(),
            "tdMode": "cash",  # cash = SPOT торговля
            "side": side,
            "ordType": ord_type,
            "sz": amount_str
        }

        if ord_type == "limit":
            if not price_str:
                raise OKXAPIError("For a limit order, you must specify a price.")

            if is_usdt:
                calculated_size = float(amount_str) / float(price_str)
                params["sz"] = str(calculated_size)

            params["px"] = price_str

        elif ord_type == "market":
            params["tgtCcy"] = "quote_ccy" if is_usdt else "base_ccy"

        response = self.trade_api.place_order(**params)

        if response.get("code") != "0":
            error_msg = response.get("msg", "Unknown error")
            raise OKXAPIError(f"Order Error: {error_msg}")

        data = response.get("data", [])
        if data:
            return data[0].get("ordId")

        return None

    def get_orders(self):
        """
        Получить все активные ордера
        """
        result_orders_list = self.trade_api.get_order_list(instType="SPOT", ordType="limit,market")

        if result_orders_list.get("code") != "0":
            error_msg = result_orders_list.get('msg', 'Unknown error')
            raise OKXAPIError(f"Error OKX: {error_msg}")

        data = result_orders_list.get("data")
        if not data:
            return []

        parsed_orders = []

        for order in data:
            c_time_ms = int(order.get("cTime", 0))
            date_str = datetime.fromtimestamp(c_time_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S") if c_time_ms > 0 else ""
            price = float(order.get("px", 0)) if order.get("px") else 0.0
            amount = float(order.get("sz", 0)) if order.get("sz") else 0.0
            total_usdt = price * amount

            parsed_orders.append({
                "ticker": order.get("instId", "Unknown"),
                "date": date_str,
                "type": order.get("side"),
                "price": price,
                "amount": amount,
                "total_usdt": total_usdt,
                "status": order.get("state", ""),
                "ID": order.get("ordId"),
            })

            return parsed_orders

    # Модуль для чтения рыночных данных (стаканы, цены)
    # market_api = MarketData.MarketAPI(use_server_time=False, flag=flag)