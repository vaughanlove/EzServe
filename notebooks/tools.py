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

load_dotenv()
API_KEY = os.getenv("API_KEY")
LOCATION = os.getenv("LOCATION")


client = Client(
    square_version='2023-08-16',
    access_token=API_KEY,
    environment='sandbox')

# note everything in here will in theory be able to be called by a end user.

class GetLocationNameTool(BaseTool):
    name="get_location_name_tool"
    description="helpful for getting the name of the resturaunt"
    def _run(
          self, location_id: str, run_manager: Optional[CallbackManagerForToolRun] = None
      ) -> str:
          """Test values"""
          return "Hungry Harry's Dumplings"

class GetBasicMenuTool(BaseTool):
    name="get_basic_menu_tool"
    description="helpful for listing the menu items when user requests. Not an exhaustive list and should not be used when ordering."
    args_schema: Type[None] = None
    def _run(
        self, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        result = client.catalog.list_catalog(types = "ITEM" )
        if result.is_success():
            menu = []
            for object in result.body['objects']:
                menu.append(
                    {object['item_data']['name'] : object['item_data']['category_id']},                
                )
            return menu
        elif result.is_error():
          # todo error handling.
          pass
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
          return client.orders.create_order(body = {  "order": { "location_id": LOCATION, "line_items": [{"catalog_object_id" : item_id, "item_type": "ITEM", "quantity": quantity}]},"idempotency_key": str(uuid4().hex)})
        
class GetVerboseMenuTool(BaseTool):
    name="get_verbose_menu_tool"
    description="helpful for getting the menu items"
    def _run(
        self, args, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        result = client.catalog.list_catalog(types = "ITEM" )
        if result.is_success():
            menu = {}
            for object in result.body['objects']:
                for variation in object['item_data']['variations']:
                    menu[variation['item_variation_data']['name'] + ' ' + object['item_data']['name']] = {
                        'item_id' : variation['id'],
                        'price' : variation['item_variation_data']['price_money']['amount']                    
                    }
                return menu
        elif result.is_error():
          # todo error handling.
          pass
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
        result = client.catalog.list_catalog(types = "ITEM" )
        for object in result.body['objects']:
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
        result = client.catalog.list_catalog(types = "ITEM" )
        if result.is_success():
            menu = {}
            for object in result.body['objects']:
                for variation in object['item_data']['variations']:
                    menu[object['item_data']['name']] = {
                        'type' : object['item_data']['name'],
                        'modifiers' : variation['item_variation_data']['name'].split(','),
                        'item_id' : variation['id'],
                        'price' : variation['item_variation_data']['price_money']['amount']                    
                    }
                return menu
        elif result.is_error():
          # todo error handling.
          pass
        return []
        
         
         


