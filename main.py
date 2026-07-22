import sys
from decimal import Decimal, ROUND_DOWN

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QMessageBox, QPushButton
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression

from QDesign.main_iface import Ui_MainWindow
from QDesign.tranfer_iface import Ui_Dialog
from terminal import OkxApiInterface, OKXAPIError

format_balance = Decimal("0.00001")


class OKXTransferForm(QtWidgets.QDialog):
    """Класс окна формы для трансфера между счетами"""
    def __init__(self, api_client):
        super(OKXTransferForm, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.api = api_client
        self.result_message = ""

        regex = QRegularExpression(r"^[0-9]+([.,][0-9]{1,8})?$")
        validator = QRegularExpressionValidator(regex)
        self.ui.editline_amount.setValidator(validator)
        self.ui.btn_OK.clicked.connect(self.send_transfer)
        self.ui.btn_cancel.clicked.connect(self.reject)

    def send_transfer(self):
        """Проверка и отправка трансфера в метод бизнес логики"""
        try:
            self.ui.btn_OK.setEnabled(False)
            currency = self.ui.editline_currency.text().strip()
            amount_str = self.ui.editline_amount.text().strip().replace(',', '.')
            if not amount_str:
                QMessageBox.warning(self, "Warning", "Enter amount value")
                self.ui.btn_OK.setEnabled(True)
                return

            try:
                amount_float = float(amount_str)
                if amount_float <= 0:
                    QMessageBox.warning(self, "Warning", "Amount most be > 0")
                    self.ui.btn_OK.setEnabled(True)
                    return

            except ValueError:
                QMessageBox.critical(self, "Error", "Unexpected simbols. Enter digits only.")
                self.ui.btn_OK.setEnabled(True)
                return

            if self.ui.rb_TM.isChecked():
                directions = "to_funding"
            else:
                directions = "to_trade"

            tx_id = self.api.transfer_funds(currency=currency, amount=amount_str, direction=directions)
            self.result_message = f"Transfer successful! ID: {tx_id}"
            self.accept()
        except OKXAPIError as e:
            self.ui.btn_OK.setEnabled(True)
            QMessageBox.critical(self, "Error", str(e))


class OKXTradeMainWindow(QtWidgets.QMainWindow):
    """Класс основной формы приложения, связь с бизнес логикой"""

    def __init__(self):
        super(OKXTradeMainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.okx_client_api = OkxApiInterface()

        # Btn Configuration
        self.ui.btn_getbal.clicked.connect(self.get_ballance)
        self.ui.btn_getord.clicked.connect(self.get_orders)
        self.ui.btn_transfer.clicked.connect(self.open_transfer)
        self.ui.btn_buy.clicked.connect(lambda: self.send_order("buy"))
        self.ui.btn_sell.clicked.connect(lambda: self.send_order("sell"))
        self.ui.btn_exit.clicked.connect(QtWidgets.QApplication.instance().quit)

        # LineEdit configuration
        regex = QRegularExpression(r"^[0-9]+([.,][0-9]{1,8})?$")
        validator = QRegularExpressionValidator(regex)
        self.ui.editline_price.setValidator(validator)
        self.ui.editline_amount_usdt.setValidator(validator)
        self.ui.editline_amount_crypto.setValidator(validator)

        self.table_main = self.ui.tableWidget_main

        # Header
        self.ui.label_head.setText("Simple Trading Application for OKX Market")

    def get_ballance(self):
        """Получение баланса с выводом в таблицу"""
        self.table_main.clear()

        self.table_main.setColumnCount(3)
        self.table_main.setColumnWidth(1, 200)
        self.table_main.setColumnWidth(2, 200)
        self.table_main.setHorizontalHeaderLabels(["Ticker", "Balance", "Balance in USD"])

        try:
            if self.ui.rb_main.isChecked():
                data = self.okx_client_api.get_balance_funding()
            elif self.ui.rb_trade.isChecked():
                data = self.okx_client_api.get_balace_trade()
            else:
                data = []

        except OKXAPIError as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage(str(e))
            return

        except Exception as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage(f"System error: {str(e)}")
            return

        self.ui.statusbar.setStyleSheet("color: green;")
        self.ui.statusbar.showMessage(f"Successful get balance", 5000)
        self.table_main.setRowCount(len(data))

        for row, record in enumerate(data):
            for col, value in enumerate(record.values()):
                if value is None:
                    formatted_value = ""
                elif col == 2 or col == 3:
                    formatted_value = str(Decimal(value).quantize(format_balance, rounding=ROUND_DOWN))
                else:
                    formatted_value = str(value)
                self.table_main.setItem(row, col, QTableWidgetItem(formatted_value))

    def get_orders(self):
        """Получение всех активных ордеров с выводом в таблицу"""
        self.table_main.clear()

        self.table_main.setColumnCount(9)
        self.table_main.setColumnWidth(0, 100)
        self.table_main.setColumnWidth(1, 150)
        self.table_main.setColumnWidth(2, 30)
        self.table_main.setColumnWidth(3, 100)
        self.table_main.setColumnWidth(4, 100)
        self.table_main.setColumnWidth(5, 100)
        self.table_main.setColumnWidth(6, 50)
        self.table_main.setColumnWidth(7, 50)
        self.table_main.setColumnWidth(8, 50)
        self.table_main.setHorizontalHeaderLabels(["Ticker", "Date-Time", "Type",
                                                   "Price", "Amount", "Total_USDT",
                                                   "Status", "ID", "Actions"])

        try:
            data = self.okx_client_api.get_orders()

        except OKXAPIError as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage(str(e))
            return

        except Exception as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage(f"System error: {str(e)}")
            return

        self.ui.statusbar.setStyleSheet("color: green;")
        self.ui.statusbar.showMessage(f"Successful get orders", 5000)
        self.table_main.setRowCount(len(data))

        for row, record in enumerate(data):
            for col, value in enumerate(record.values()):
                if value is None:
                    formatted_value = ""
                elif col == 3 or col == 4:
                    formatted_value = str(Decimal(value).quantize(format_balance, rounding=ROUND_DOWN))
                else:
                    formatted_value = str(value)
                self.table_main.setItem(row, col, QTableWidgetItem(formatted_value))

            cancel_btn = QPushButton("del")
            cancel_btn.setStyleSheet("color: red; font-weight: bold;")
            ordid = self.table_main.item(row, 7).text()
            ordticker = self.table_main.item(row, 0).text()
            cancel_btn.clicked.connect(lambda checked, t=ordticker, oid=ordid: self.on_cancel_clicked(t, oid))
            self.table_main.setCellWidget(row, 8, cancel_btn)

    def send_order(self, side: str):
        """Размещение нового ордера в SPOPT торговле"""
        ticker = self.ui.editline_ticker.text().strip()
        if not ticker:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage("Error, Enter ticker (for example, BTC-USDT)")
            return

        ord_type = "limit" if self.ui.rb_limit.isChecked() else "market"

        price_str = None
        if ord_type == "limit":
            price_str = self.ui.editline_price.text().strip().replace(',', '.')
            if not price_str or float(price_str) <= 0:
                self.ui.statusbar.setStyleSheet("color: red;")
                self.ui.statusbar.showMessage("Error, A limit order requires a correct price.")
                return

        amount_crypto = self.ui.editline_amount_crypto.text().strip().replace(',', '.')
        amount_usdt = self.ui.editline_amount_usdt.text().strip().replace(',', '.')

        if amount_crypto and amount_usdt:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage("Error, Fill in only one field: either the amount of cryptocurrency or USDT.")
            return
        if not amount_crypto and not amount_usdt:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage("Error, Please specify the order size.")
            return

        is_usdt = bool(amount_usdt)
        target_amount = amount_usdt if is_usdt else amount_crypto

        try:
            if float(target_amount) <= 0:
                self.ui.statusbar.setStyleSheet("color: red;")
                self.ui.statusbar.showMessage("Error The volume must be greater than zero.")
                return

            self.ui.btn_buy.setEnabled(False)
            self.ui.btn_sell.setEnabled(False)

            order_id = self.okx_client_api.place_spot_order(
                inst_id=ticker,
                side=side,
                ord_type=ord_type,
                amount_str=target_amount,
                price_str=price_str,
                is_usdt=is_usdt
            )

            self.ui.statusbar.setStyleSheet("color: green;")
            self.ui.statusbar.showMessage(f"Successful, The order was successfully placed! ID: {order_id}")
            self.ui.editline_ticker.setText("")
            self.ui.editline_price.setText("")
            self.ui.editline_amount_usdt.setText("")
            self.ui.editline_amount_crypto.setText("")

        except ValueError:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage("Error, The “Amount” and “Price” fields must contain only numbers.")
        except OKXAPIError as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage("API Error", str(e))
        except Exception as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage("System error", str(e))
        finally:
            self.ui.btn_buy.setEnabled(True)
            self.ui.btn_sell.setEnabled(True)

    def open_transfer(self):
        """Метод открывает окно трансферов"""
        transfer_form = OKXTransferForm(self.okx_client_api)
        if transfer_form.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            status_result = transfer_form.result_message
            self.ui.statusbar.setStyleSheet("color: blue;")
            self.ui.statusbar.showMessage(status_result, 5000)

    def on_cancel_clicked(self, ticker: str, order_id: str):
        """Обработчик нажатия на кнопку удаления ордера"""

        reply = QMessageBox.question(self,
                                     "Confirmation",
                                     f"Are you shure cancel this order {order_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success = self.okx_client_api.cancel_spot_order(ticker, order_id)

            if success:
                self.remove_row_by_order_id(order_id)
            else:
                self.ui.statusbar.setStyleSheet("color: red;")
                self.ui.statusbar.showMessage("Error, The order could not be canceled on the exchange.")

    def remove_row_by_order_id(self, order_id: str):
        """Безопасный поиск и удаление строки по ID ордера"""
        for row in range(self.table_main.rowCount()):
            item = self.table_main.item(row, 7)
            if item and item.text() == order_id:
                self.table_main.removeRow(row)
                break


def create_application():
    """Запуск модуля основного приложения"""
    app = QApplication(sys.argv)
    main_window = OKXTradeMainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    create_application()
