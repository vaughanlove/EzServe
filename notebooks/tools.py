from langchain.tools.base import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import json
from typing import Optional, Type
from pydantic import BaseModel, Field, ConfigDict
from uuid import uuid4

from square.client import Client
from square.api.catalog_api import CatalogApi

from dotenv import load_dotenv
import os

from order import Order

ord = Order()

load_dotenv()
API_KEY = os.getenv("API_KEY")
LOCATION = os.getenv("LOCATION")


client = Client(
    square_version='2023-08-16',
    access_token=API_KEY,
    environment='sandbox')

# note everything in here will in theory be able to be called by a end user.

class GetOrderIdTool(BaseTool):
    name="get_order_id_tool"
    description="for getting the order id when a order has already been placed. Useful for checking current order and updating order when items are ordered."
    def _run(
          self, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Test values"""
        if ord.ONGOING:
            return ord.ORDER_ID
        else:
            return "ERROR: there is no current order id. Use create_new_order"



class GetBasicMenuTool(BaseTool):
    name="get_basic_menu_tool"
    description="helpful for listing the basic menu items when user requests. important** should not be used when ordering."
    args_schema: Type[None] = None
    def _run(
        self, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        #result = client.catalog.list_catalog(types = "ITEM" )
        result = ord.menu
        menu = []
        for object in result['objects']:
            menu.append(object['item_data']['name'])
        return menu
        return "ERROR: cannot retrieve menu."

class GetDetailedMenuTool(BaseTool):
    name="get_detailed_menu_tool"
    description="helpful for listing the entire menu when details like size or flavor of an item are asked about. important** should not be used when ordering."
    args_schema: Type[None] = None
    def _run(
        self, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        #result = client.catalog.list_catalog(types = "ITEM" )
        result = ord.menu
        menu = []
        for object in result['objects']:
            for variation in object['item_data']['variations']:
                menu.append(variation['item_variation_data']['name'] + ' ' + object['item_data']['name'])
        return menu
        return "ERROR: cannot retrieve menu."


class CreateOrderSchema(BaseModel):
    item_id: str = Field(description="The item ID of the item being ordered.")
    quantity: str = Field(description="**VERY IMPORTANT: must be a string. The quantity of food item requested.")


class CreateOrderTool(BaseTool):
    name="create_new_order"
    description="used for creating a new order. Do not hallucinate. Use GetItemIdTool to get the Id of a item."
    args_schema: Type[CreateOrderSchema] = CreateOrderSchema
    def _run(
        self, item_id: str, quantity: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:    
        result = client.orders.create_order(body = {  "order": { "location_id": LOCATION, "line_items": [{"catalog_object_id" : item_id, "item_type": "ITEM", "quantity": quantity}]},"idempotency_key": str(uuid4().hex)})
        if result.is_success():
            ord.ONGOING = True
            ord.ORDER_ID = result.body["order"]["id"]
            return result.body
        else:
          return 
        
class GetVerboseMenuTool(BaseTool):
    name="get_verbose_menu_tool"
    description="helpful for getting the menu items"
    def _run(
        self, args, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        #result = client.catalog.list_catalog(types = "ITEM" )
        result = ord.menu
        menu = {}
        for object in result['objects']:
            for variation in object['item_data']['variations']:
                menu[variation['item_variation_data']['name'] + ' ' + object['item_data']['name']] = {
                    'item_id' : variation['id'],
                    'price' : variation['item_variation_data']['price_money']['amount']                    
                }
            return menu

        return []

        
class FindItemIdSchema(BaseModel):
    name: str = Field(description="The name of a menu item. important** If provided, include adjectives like size, ie small, medium, or large. Menu items will usually have adjectives before them like 'small' or 'pumpkin', make sure to include those.")


class FindItemIdTool(BaseTool):
    name="find_item_id_tool"
    description="For finding the item IDs corresponding to the name of a menu item. Do not hallucinate."
    args_schema: Type[FindItemIdSchema] = FindItemIdSchema
    def _run(
        self, name, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        #result = client.catalog.list_catalog(types = "ITEM" )
        result = ord.menu
        for object in result['objects']:
            for variation in object['item_data']['variations']:
                temp_item = (variation['item_variation_data']['name'] + ' ' + object['item_data']['name']).lower()
                # TOdo some regex
                if (name.lower() == temp_item.replace(',', '')):
                    return variation['id']

        # todo: improve errors
        return "Error: cannot find item in menu."

# deprecated 
class GetEntireMenuTool(BaseTool):
    name="get_menu_tool"
    description="helpful for getting the menu items"
    def _run(
        self, args, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        #result = client.catalog.list_catalog(types = "ITEM" )
        result = ord.menu        
        menu = {}
        for object in result['objects']:
            for variation in object['item_data']['variations']:
                menu[object['item_data']['name']] = {
                    'type' : object['item_data']['name'],
                    'modifiers' : variation['item_variation_data']['name'].split(','),
                    'item_id' : variation['id'],
                    'price' : variation['item_variation_data']['price_money']['amount']                    
                }
            return menu
   
        return []
        
         
         


