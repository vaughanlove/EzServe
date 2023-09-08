from dotenv import load_dotenv
import os

from square.client import Client
from square.api.catalog_api import CatalogApi

class Order:
    ORDER_ID = ''
    ONGOING = False

    client = None
    
    API_KEY = ''
    LOCATION = ''
    VERSION = 1

    order_items = []
    
    def __init__(self):
        self.__setupClient()
        self.__initMenu()

    def __setupClient(self):
        self.API_KEY = os.getenv("API_KEY")
        self.LOCATION = os.getenv("LOCATION")
        self.client = Client( square_version='2023-08-16', access_token=self.API_KEY, environment='sandbox')

    # todo: add type checking for item - make a Item type.
    def addItem(self, item):
        self.order_items.append(item)
        
    # private
    def __initMenu(self):
        result = self.client.catalog.list_catalog(types = "ITEM" )
        if result.is_success():
            self.menu = result.body
        else:
            # desperately need to improve error handling.
            return "ERROR: could not retrieve menu."