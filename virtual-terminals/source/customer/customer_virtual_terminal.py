import os
import sys
import json

from square.client import Client
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# Instantiate Square API Client. 
""" note: Must have SQUARE_ACCESS_TOKEN environment variable exported"""
client = Client(
    square_version='2023-08-16',
    access_token=os.environ['SQUARE_ACCESS_TOKEN'],
    environment='sandbox',
    max_retries=4
    )

"""
QT Customer Checkout Window
---------------------------
GUI with list of order items, total bill, and payment button.
"""
class CheckoutWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EzServe - Checkout")
        self.resize(450, 300)
        # define layout type
        checkout_layout = QGridLayout()

        # SQUARE Order API
        # Retrieve last order by location
        # Note: In production implementation, this would include device ID.
        self.o_id = get_last_order_by_location(self)
        order = client.orders.retrieve_order(order_id = self.o_id)

        # Define list widget for Order items
        checkout_items = QListWidget()

        #Define dummy Pay Button - would direct customer to payment processing in production ie have an nfc readers
        self.payment_btn = QPushButton("PAY")
        self.payment_btn.clicked.connect(self.payment_processing) # currently kills app processing execution on activation

        # define order total
        total = 0
        #For all items in the order retrieved, add them and selected metadata to list widget.
        for item in order.body["order"]["line_items"]:
                order_Item = QListWidgetItem(str(item["quantity"]) + " x " + item["variation_name"] + " " + item["name"] + " -   " + str(item["base_price_money"]["amount"]) + " " + item["base_price_money"]["currency"])
                checkout_items.addItem(order_Item)
                currency = str(item["base_price_money"]["currency"])
                total += int(item["base_price_money"]["amount"])

        # instantiate label and assign chckout totoal
        self.checkout_total = QLabel("TOTAL (" + currency + ") - " + str(total))
        self.checkout_total.setStyleSheet("font-weight: bold")


        # Add widgets to QT layout
        checkout_layout.addWidget(checkout_items, 0, 0)
        checkout_layout.addWidget(self.checkout_total, 1, 0)
        checkout_layout.addWidget(self.payment_btn, 2, 0)
        self.setLayout(checkout_layout)

    # Custom function using the Square terminal checkout API
    def get_terminal_checkout(self, c_id):
        result = client.terminal.get_terminal_checkout(checkout_id = c_id)

        if result.is_success():
            #print(result.body)
            order = result.body
        elif result.is_error():
            print(result.errors)

        return order['checkout']['note']

    # Kill's widget process onClick of 'PAY' button
    def payment_processing(self):
        sys.exit(app.exec_())

"""
QT Customer Main Virtual Terminal Window
----------------------------------------
GUI for active customer order, shows order status, and order items. 
Can be updated once EZ-Serve processes order through Square network.
FUTURE TO-DO: webhooks for live updates
Meant to emulate the screen on our square concept device.
In current state, it represents a virtual screen for our EZ-Serve hardware being the raspberry pi 4.
"""
class Terminal(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZServe - Order")
        self.resize(450, 300)
        # Create a top-level layout
        terminal_layout = QGridLayout()

        # SQUARE Order API
        # retrieve hard-coded order ID
        self.o_id = get_last_order_by_location(self)

        # Order List Widget and Status Label Widget
        self.order_items = QListWidget()
        self.order_status = QLabel()

        # Update order & Checkout button widgets
        self.update_order_btn = QPushButton("UPDATE ORDER")
        self.checkout_btn = QPushButton("CHECKOUT")
        # Checkout & Update Order Actions
        self.checkout_btn.clicked.connect(self.checkout_window)
        self.update_order_btn.clicked.connect(self.update_order)

        self.update_order()
        self.update_order_status()

        terminal_layout.addWidget(self.order_items, 1, 0)
        terminal_layout.addWidget(self.order_status, 0, 0)
        terminal_layout.addWidget(self.update_order_btn, 2, 0)
        terminal_layout.addWidget(self.checkout_btn, 3, 0)
        self.setLayout(terminal_layout)

    def checkout_window(self, checked):
        self.c = CheckoutWindow()
        self.c.show()

    def update_order(self):
        # SQUARE Retrieve Order API
        order = self.retrieve_order()
        #Update order by searching for all order items and updating list component
        self.order_items.clear()
        for item in order.body["order"]["line_items"]:
            order_Item = QListWidgetItem(str(item["quantity"]) + " x " + item["variation_name"] + " " + item["name"] + " -   " + str(item["base_price_money"]["amount"]) + " " + item["base_price_money"]["currency"])
            self.order_items.addItem(order_Item)
        self.order_items.update()

    def update_order_status(self):
        # SQUARE Retrieve Order API
        order = self.retrieve_order()
        status = str(order.body["order"]["state"])
        # display banner color based on order status
        # if status == "OPEN":
        #     self.order_status.setStyleSheet("background: green; font-weight: bold")
        # elif status == "PENDING":
        #     self.order_status.setStyleSheet("background: yellow; font-weight: bold")
        # elif status == "CLOSED":
        #     self.order_status.setStyleSheet("background: red; font-weight: bold")

        self.order_status = QLabel("ORDER STATUS: " + status, self)
        self.order_status.setStyleSheet("background: green; font-weight: bold")
        self.order_status.setAlignment(Qt.AlignCenter)

    # SQUARE FUNCTIONS
    def retrieve_order(self): 
        order = client.orders.retrieve_order(order_id = self.o_id)
        return order

def get_last_order_by_location(self):
    result = client.orders.search_orders(
        body = {
            "location_ids": [
                "LETE3KSW0H1RB"
                ]
            }
        )
    if result.is_success():
        pass
        #print(result.body)
    elif result.is_error():
        print(result.errors)

    return result.body["orders"][0]["id"]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Terminal()
    window.show()
    sys.exit(app.exec_())