from langchain.tools.base import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import json
from typing import Optional, Type
    
class GetLocationIdTool(BaseTool):
    name="get_location_id_tool"
    description="helpful for retrieving the location ID."
    def _run(
          self, run_manager: Optional[CallbackManagerForToolRun] = None
      ) -> str:
          """Right now this is hard coded."""
          return "LETE3KSW0H1RB"

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
    description="helpful for getting all the menu items with prices"
    def _run(
          self, run_manager: Optional[CallbackManagerForToolRun] = None
      ) -> str:
          """Test values"""
          return {"coffee": 4, "tea": 2, "danish": 3}


