import os
import sys
from decimal import Decimal, ROUND_DOWN

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

from QDesign.main_iface import Ui_MainWindow
from terminal import OkxApiInterface, OKXAPIError

format_balance = Decimal("0.00001")

class OKXTradeMainWindow(QtWidgets.QMainWindow):
    """Класс основной формы приложения"""

    def __init__(self):
        super(OKXTradeMainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.api = OkxApiInterface()

        # Btn Configuration
        self.ui.btn_getbal.clicked.connect(self.get_ballance)
        self.ui.btn_getord.clicked.connect(self.get_orders)
        self.ui.btn_buy.clicked.connect(self.send_buy)
        self.ui.btn_sell.clicked.connect(self.send_sell)
        self.ui.btn_exit.clicked.connect(QtWidgets.QApplication.instance().quit)

    def get_ballance(self):
        self.table_main = self.ui.tableWidget_main
        self.table_main.clear()

        self.table_main.setColumnCount(3)
        self.table_main.setColumnWidth(1, 200)
        self.table_main.setColumnWidth(2, 200)
        self.table_main.setHorizontalHeaderLabels(["Ticker", "Balance", "Balance in USD"])

        try:
            if self.ui.rb_main.isChecked():
                data = self.api.get_balance_funding()
            elif self.ui.rb_trade.isChecked():
                data = self.api.get_balace_trade()

        except OKXAPIError as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage(str(e))

        except Exception as e:
            self.ui.statusbar.setStyleSheet("color: red;")
            self.ui.statusbar.showMessage(f"System error: {str(e)}")

        self.ui.statusbar.setStyleSheet("color: green;")
        self.ui.statusbar.showMessage(f"Successful get balance")
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
        pass

    def send_buy(self):
        pass

    def send_sell(self):
        pass

def create_application():
    """Запуск модуля основного приложения"""
    app = QApplication(sys.argv)
    main_window = OKXTradeMainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    create_application()
