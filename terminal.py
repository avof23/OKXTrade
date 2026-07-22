import os
from datetime import datetime
import time

from dotenv import load_dotenv

import okx.Account as Account
import okx.Funding as Funding
import okx.Trade as Trade
import okx.MarketData as MarketData


load_dotenv()
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
PASSPHRASE = os.getenv("PASSPHRASE")
flag = os.getenv("FLAG")
# flag='0' — реальные торги, flag='1' — демо-режим (песочница)


class OKXAPIError(Exception):
    pass


class OkxApiInterface:
    """Класс бизнес логики, Инициализация API интерфейса и
    обработка всех запросов на биржу"""
    def __init__(self):
        self.account_api = Account.AccountAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)
        self.funding_api = Funding.FundingAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)
        self.trade_api = Trade.TradeAPI(API_KEY, SECRET_KEY, PASSPHRASE, use_server_time=False, flag=flag)
        self.market_api = MarketData.MarketAPI(flag=flag)

        self.CACHE_TTL = 300
        self.price_cache = {}

    def get_ticker_price(self, ticker: str) -> float:
        """Получаем актуальные цены с биржи и сохраняем в локальный кэш"""
        if ticker == "USDT" or ticker == "USD":
            return 1.00

        if ticker in self.price_cache:
            cached_data = self.price_cache[ticker]
            if time.time() - cached_data["time"] < self.CACHE_TTL:
                return cached_data["price"]

        try:
            result = self.market_api.get_index_tickers(instId=f"{ticker}-USDT")
            if result.get("code") == "0" and result.get("data"):
                ticker_data = result.get("data", [])[0]
                last_price = float(ticker_data.get("idxPx", 0.00))
            else:
                last_price = 0.00
        except Exception:
            last_price = 0.00

        self.price_cache[ticker] = {
            "price": last_price,
            "time": time.time()
        }

        return last_price

    def get_balace_trade(self) -> list:
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
            "balanceUSDT": float(val.get("eq")) * self.get_ticker_price(val.get("ccy")), # "balanceUSDT": val.get("eqUsd", "0"),
        } for val in details]

    def get_balance_funding(self) -> list:
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
            "balanceUSDT": float(asset.get("bal")) * self.get_ticker_price(asset.get("ccy"))
        } for asset in data]

    def transfer_funds(self, currency: str, amount: str, direction: str = "to_trade"):
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

    def place_spot_order(self, inst_id: str, side: str, ord_type: str, amount_str: str, price_str=None, is_usdt=False):
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

    def get_orders(self) -> list:
        """Получить все активные ордера по SPOT торговле"""

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

    def cancel_spot_order(self, tik: str, order_id: str):
        """
        Отмера активного ордера на SPOT торговле
        :param tik: Тикер, например "BTC-USDT"
        :param order_id: ID ордера размещенного в терминале"
        """
        result_cancel = self.trade_api.cancel_order(instId=tik, ordId=order_id)

        if result_cancel.get("code") != "0":
            error_msg = result_cancel.get('msg', 'Unknown error')
            raise OKXAPIError(f"Error OKX: {error_msg}")
        return True
