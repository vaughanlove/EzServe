import os
import sys
import json
import random
import re

from square.client import Client

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

client = Client(
    square_version='2023-08-16',
    access_token=os.environ['SQUARE_ACCESS_TOKEN'],
    environment='sandbox',
    max_retries=4
    )

class OrderTerminal(QWidget):
    def __init__(self, order_id):
        super().__init__()
        self.o_id = order_id
        self.setWindowTitle("Vendor A - Order " + self.o_id) # pass order ID to title
        self.resize(600, 300)
        # Create a top-level layout
        individual_order_layout = QGridLayout()

        self.order = self.retrieve_order()

        self.order_id = QLabel("ID: " + self.o_id)
        self.order_id.setStyleSheet("font-weight: bold")

        self.order_location = QLabel("LOCATION: " + self.order.body["order"]["location_id"])

        self.order_items = QListWidget()
        self.get_order_items()

        self.order_state = QLabel("STATE: " + self.order.body["order"]["state"])
        self.order_state.setStyleSheet("font-weight: bold")

        self.order_list_label = QLabel("ORDER ITEMS")
        self.order_list_label.setStyleSheet("font-weight: bold")


        self.order_tax_money = QLabel("TOTAL TAX: " + str(self.order.body["order"]["total_tax_money"]["amount"]) + " " + self.order.body["order"]["total_tax_money"]["currency"])
        self.order_discount_money = QLabel("TOTAL DISCOUNTS: " + str(self.order.body["order"]["total_discount_money"]["amount"]) + " " + self.order.body["order"]["total_discount_money"]["currency"])
        self.order_tip_money = QLabel("TOTAL TIP: " + str(self.order.body["order"]["total_tip_money"]["amount"]) + " " + self.order.body["order"]["total_tip_money"]["currency"])
        self.order_service_charge_money = QLabel("SERVICE CHARGE: " + str(self.order.body["order"]["total_service_charge_money"]["amount"]) + " " + self.order.body["order"]["total_service_charge_money"]["currency"])
        self.order_total_money = QLabel("TOTAL: " + str(self.order.body["order"]["total_money"]["amount"]) + " " + self.order.body["order"]["total_money"]["currency"])
        self.order_total_money.setStyleSheet("font-weight: bold")

        self.order_start = QLabel("START TIME: " + self.order.body["order"]["created_at"])
        self.order_last_update = QLabel("LAST UPDATE: " + self.order.body["order"]["updated_at"])
        self.order_source_name = QLabel("source - " + self.order.body["order"]["source"]["name"])

        individual_order_layout.addWidget(self.order_id, 0, 0)
        individual_order_layout.addWidget(self.order_location, 0, 1)
        individual_order_layout.addWidget(self.order_state, 1, 0)
        individual_order_layout.addWidget(self.order_start, 1, 1)
        individual_order_layout.addWidget(self.order_list_label, 2, 0)
        individual_order_layout.addWidget(self.order_items, 3, 0)
        individual_order_layout.addWidget(self.order_total_money, 3, 1)
        individual_order_layout.addWidget(self.order_last_update, 2, 1)
        individual_order_layout.addWidget(self.order_discount_money, 4, 0)
        individual_order_layout.addWidget(self.order_tip_money, 5, 0)
        individual_order_layout.addWidget(self.order_tax_money, 4, 1)
        individual_order_layout.addWidget(self.order_service_charge_money, 5, 1)
        individual_order_layout.addWidget(self.order_source_name, 6, 0)
        self.setLayout(individual_order_layout)
    
    # SQUARE FUNCTIONS
    def retrieve_order(self): 
        order = client.orders.retrieve_order(order_id = self.o_id)
        return order

    def get_order_items(self):
        # SQUARE Retrieve Order API
        order = self.retrieve_order()
        for item in order.body["order"]["line_items"]:
            order_Item = QListWidgetItem(str(item["quantity"]) + " x " + item["name"] + " -   " + str(item["base_price_money"]["amount"]) + " " + item["base_price_money"]["currency"])
            self.order_items.addItem(order_Item)
        self.order_items.update()


class VendorTerminal(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EzServe - Vendor A Terminal")
        self.resize(600, 300)
        # Create a top-level layout
        terminal_layout = QGridLayout()

        self.vendor_orders = QListWidget()

        location_orders = self.get_orders_for_location()

        for order in location_orders.body["orders"]:
            table_order = QListWidgetItem("Order [" + order["id"] + "]: Table " + str(random.randrange(1,100)) + " with " + str(random.randrange(1,12)) + " Patrons - " + order["state"]) 
            self.vendor_orders.addItem(table_order)

        self.vendor_orders.itemSelectionChanged.connect(self.individual_order_terminal)

        terminal_layout.addWidget(self.vendor_orders, 1, 0)

        self.setLayout(terminal_layout)
    
    def get_orders_for_location(self):
        result = client.orders.search_orders(
            body = {
                "location_ids": [
                    "LETE3KSW0H1RB"
                ]
            }
        )
        # if result.is_success():
        #     print(result.body)
        # elif result.is_error():
        #     print(result.errors)

        return result

    def individual_order_terminal(self):
        selected_order = self.vendor_orders.currentItem()
        pattern = r'\[(.*?)\]'
        match = re.search(pattern, selected_order.text())
        if match:
            order_id = match.group(1)
            self.o = OrderTerminal(order_id)
            self.o.show()
        else:
            print("No match.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VendorTerminal()
    window.show()
    sys.exit(app.exec_())