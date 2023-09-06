from langchain.tools.base import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import json
from typing import Optional, Type

from square.client import Client
from square.api.catalog_api import CatalogApi

from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

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


class GetMenuTool(BaseTool):
    name="get_menu_tool"
    description="helpful for getting the menu items"
    def _run(
        self, args, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get from square api"""
        result = client.catalog.list_catalog(types = "ITEM" )
        if result.is_success():
            menu = []
            for object in result.body['objects']:
                for variation in object['item_data']['variations']:
                    menu.append({
                        'type' : object['item_data']['name'],
                        'modifiers' : variation['item_variation_data']['name'].split(','),
                        'item_id' : variation['id'],
                        'price' : variation['item_variation_data']['price_money']['amount']                    
                    })
                return menu
        elif result.is_error():
          # todo error handling.
          pass
        return []


class GetItemId(BaseTool):
    name="get_item_id"
    description="helpful for retrieving a specific item's id for ordering"
    def _run(
        self, item_name: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        menu = GetMenuTool()
        return menu[item_name]['variations']
        
         
         


