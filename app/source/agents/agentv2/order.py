"""Order module for managing order details and interacting with the square api.

TODO:
    Add exceptions
    Improve error handling
"""

from dotenv import load_dotenv
import os
from uuid import uuid4
from square.client import Client
import json


class Order(object):
    """Contains all methods and information for managing a square order.

    Attributes:
        order_ongoing (bool): True if there has been an order created, False otherwise.
        order_total_cost (int): Total cost in cents of the order.
        order_version (int): Used for updating the order, to ensure sequential ordering.
        order_items (:obj:`list` of :obj:`str`): List of item names in the order.
        _order_id (str): The order ID corresponding to the order in square's db.
    """

    order_ongoing = False
    order_total_cost = 0
    order_version = 1
    order_items = []
    _order_id = None

    def __init__(self):
        """
        Initialize the Order class. Sets up the Square Client and fetches the menu.
        """
        self.__setup_client()
        self.__init_menu()

    def get_order_total(self):
        """
        Returns the total cost of the order.
        """
        return self.order_total_cost

    def get_order_items(self):
        """Returns the items in the order."""
        return self.order_items

    def add_item_to_order(self, item_id: str, quantity: str, note: str) -> bool:
        """Adds an item to the order.

        Todo:
            add type checking for item - make a Item type.

        Args:
            item_id (str): The item_id of the item.
            quantity (str): The amount of item to add.
            note (str): notes for that specific item order.
        """

        # https://developer.squareup.com/explorer/square/orders-api/update-order
        body = {
            "order": {
                "location_id": self._location_id,
                "line_items": [
                    {
                        "catalog_object_id": item_id,
                        "item_type": "ITEM",
                        "quantity": quantity,
                        "note": note,
                    }
                ],
                "version": self.order_version,
            },
            "idempotency_key": str(uuid4().hex),
        }
        result = self._square_client.orders.update_order(self._order_id, body)
        if result.is_success():
            item = result.body["order"]["line_items"][self.order_version]["name"]
            self.order_items.append(item)
            self.order_total_cost += int(
                result.body["order"]["line_items"][self.order_version][
                    "base_price_money"
                ]["amount"]
            )
            self.order_version = self.order_version + 1
            return True
        else:
            return False

    def create_order(self, item_id: str, quantity: str, note: str) -> bool:
        """Create a new order.

        Args:
            item_id (str): The id from square corresponding to the ordered item.
            quantity (str): The number of item ordered.
            note (str): notes for that specific item order.
        """
        assert isinstance(quantity, str)
        body = {
            "order": {
                "location_id": self._location_id,
                "line_items": [
                    {
                        "catalog_object_id": item_id,
                        "item_type": "ITEM",
                        "quantity": quantity,
                        "note": note,
                    }
                ],
            },
            "idempotency_key": str(uuid4().hex),
        }
        result = self._square_client.orders.create_order(body)
        if result.is_success():
            item = result.body["order"]["line_items"][0]["name"]
            self.order_ongoing = True
            self.order_items.append(item)
            self.order_total_cost += int(
                result.body["order"]["line_items"][0]["base_price_money"]["amount"]
            )
            self._order_id = result.body["order"]["id"]
            return True
        else:
            return False

    def start_checkout(self):
        """Start a checkout on a square terminal."""
        body = {
            "idempotency_key": str(uuid4().hex),
            "checkout": {
                "amount_money": {"amount": self.order_total_cost, "currency": "USD"},
                "order_id": self._order_id,
                "payment_options": {
                    "autocomplete": True,
                    "accept_partial_authorization": False,
                },
                "device_options": {
                    "device_id": self._square_device_id,
                    "skip_receipt_screen": True,
                    "collect_signature": True,
                    "show_itemized_cart": True,
                },
                "payment_type": "CARD_PRESENT",
                "customer_id": "",
            },
        }
        result = self._square_client.terminal.create_terminal_checkout(body)
        if result.is_success():
            self._order_id = ""
            self.order_ongoing = False
            self.order_total_cost = 0
            self.order_items = []
            self._checkout_id = result.body["checkout"]["id"]
            return True
        else:
            return False

    def cancel_checkout(self):
        assert self._checkout_id != "", "Missing Checkout ID"
        result = self._square_client.terminal.cancel_terminal_checkout(
            checkout_id=self._checkout_id
        )
        if result.is_success():
            self.checkout_id = ""
            return "Checkout successfully cancelled. Feel free to continue ordering."
        else:
            return "Checkout could not be cancelled"

    def __setup_client(self):
        """Load in environment variables and initialize the square client."""
        load_dotenv()
        self._square_api_key = os.getenv("API_KEY")  #: Square API key
        self._location_id = os.getenv("LOCATION")  #: Square Location ID
        self._square_device_id = os.getenv("DEVICE")  #: Square Device ID
        self._square_client = Client(
            square_version="2023-08-16",
            access_token=self._square_api_key,
            environment="production",
        )

    def __init_menu(self):
        """ Fetch the menu from the square api.

        Returns:
            List of the names of menu items.
        """
        result = self._square_client.catalog.list_catalog(types="ITEM")
        if result.is_success():
            self.menu = result.body
        else:
            return "ERROR: could not retrieve menu."
