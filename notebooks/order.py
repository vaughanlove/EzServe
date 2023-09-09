from dotenv import load_dotenv
import os
from uuid import uuid4

from square.client import Client
from square.api.catalog_api import CatalogApi

# dummy values for testing
DEVICE_ID_CHECKOUT_SUCCESS="9fa747a2-25ff-48ee-b078-04381f7c828f"
DEVICE_ID_CHECKOUT_SUCCESS_TIP="22cd266c-6246-4c06-9983-67f0c26346b0"
DEVICE_ID_CHECKOUT_SUCCESS_GC="4mp4e78c-88ed-4d55-a269-8008dfe14e9"
DEVICE_ID_CHECKOUT_FAILURE_BUYER_CANCEL="841100b9-ee60-4537-9bcf-e30b2ba5e215"

class Order:
    ORDER_ID = ''
    ONGOING = False
    # add to total after each item.
    TOTAL = 0
    order_items = []

    # should I make this private and only expose order methods?
    client = None
    
    API_KEY = ''
    LOCATION = ''
    VERSION = 1

    
    def __init__(self):
        self.__setupClient()
        self.__initMenu()

    def __setupClient(self):
        load_dotenv()
        self.API_KEY = os.getenv("API_KEY")
        self.LOCATION = os.getenv("LOCATION")
        self.client = Client( square_version='2023-08-16', access_token=self.API_KEY, environment='sandbox')

    def getTotal(self):
        return self.TOTAL
    
    def getItems(self):
        return self.order_items

    # todo: add type checking for item - make a Item type (with cost of each item and running).
    def updateOrder(self, item_id, quantity):
        # checking parameters
        assert type(quantity) == str, "Quantity parameter should be a string."
        body = { 
            "order": { 
                "location_id": self.LOCATION, 
                "line_items": [
                    {
                        "catalog_object_id" : item_id,
                        "item_type": "ITEM", 
                        "quantity": quantity
                    }
                ],
                "version": 1
            },
            "idempotency_key": str(uuid4().hex)
        }
        result = self.client.orders.update_order(ord.ORDER_ID, body)
        if result.is_success():
            self.VERSION += 1
            self.order_items.append(result.body["order"]["line_items"][0]["name"])
            self.TOTAL += result.body["order"]["line_items"][0]["base_price_money"]["amount"]
            return result.body
        else:
            return result.error

    def createOrder(self, item_id, quantity):
        # checking parameters
        assert type(quantity) == str, "Quantity parameter should be a string."
        body = {  
            "order": { 
                "location_id": self.LOCATION,
                "line_items": [
                    {
                        "catalog_object_id" : item_id,
                        "item_type": "ITEM",
                        "quantity": quantity
                    }
                ]
            },
            "idempotency_key": str(uuid4().hex)
        }
        result = self.client.orders.create_order(body)
        if result.is_success():
            self.ORDER_ID = result.body["order"]["id"]
            self.ONGOING = True
            self.order_items.append(result.body["order"]["line_items"][0]["name"])
            self.TOTAL += result.body["order"]["line_items"][0]["base_price_money"]["amount"]
            return result.body
        else:
            return "ERROR: square create_order call threw an error."


    def startCheckout(self):
        order = self.client.orders.retrieve_order(order_id = self.ORDER_ID)
        if order.is_error():
            return "Error: order retrieval failed."
            
        body = {
            "idempotency_key": str(uuid4().hex),
            "checkout": {
                "amount_money": {
                    "amount": self.TOTAL,
                    "currency": "USD"
                  },
                "order_id": self.ORDER_ID,
                "payment_options": {
                    "autocomplete": True,
                    "accept_partial_authorization": False
                },
                "device_options": {
                    "device_id": DEVICE_ID_CHECKOUT_SUCCESS,
                    "skip_receipt_screen": True,
                    "collect_signature": True,
                    "show_itemized_cart": True
                },
                "payment_type": "CARD_PRESENT",
                "customer_id": ""
            }
        }
        result = self.client.terminal.create_terminal_checkout(body)
        if result.is_success():
            self.ORDER_ID = ''
            self.ONGOING = False
            self.TOTAL = 0
            self.order_items = []
            return "Checkout was successful, have a good day!"
        else:
            return "ERROR: square create_order call threw an error."

    # todo add a getOrderTotal() for use with checkout.
    # def calculate
    
    # private
    def __initMenu(self):
        result = self.client.catalog.list_catalog(types = "ITEM" )
        if result.is_success():
            self.menu = result.body
        else:
            # desperately need to improve error handling.
            return "ERROR: could not retrieve menu."