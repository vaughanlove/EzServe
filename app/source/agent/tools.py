""" Module for langchain tools
"""
from langchain.tools.base import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from typing import Optional, Type
from pydantic import BaseModel, Field

# import re

from source.agent.order import Order

square_order = Order()


class GetDetailedMenuTool(BaseTool):
    """Tool for retrieving the menu."""

    name = "get_detailed_menu_tool"
    description = "helpful for listing the entire menu when details like size or flavor \
        of an item are asked about. important** should not be used when ordering."
    args_schema: Type[None] = None

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Get from square api"""
        return square_order.menu


class FindItemIdSchema(BaseModel):
    name: str = Field(
        description="The name of a menu item. important** If provided, \
        include adjectives like size, ie small, medium, or large. \
        Menu items will usually have adjectives before them like 'small' or 'pumpkin', \
        make sure to include those."
    )

class OrderSchema(BaseModel):
    item_id: str = Field(
        description="The item ID of the item being ordered. Use find_item_id_tool to \
            find this variable"
    )
    quantity: str = Field(
        description="**VERY IMPORTANT: must be a string. The quantity of food item \
            requested."
    )


class OrderTool(BaseTool):
    """Tool for creating and updating orders."""

    name = "order_tool"
    description = "For creating new orders or adding items to existing orders. Use \
        after find_item_id_tool."
    args_schema: Type[OrderSchema] = OrderSchema

    def _run(
        self,
        item_id: str,
        quantity: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        if square_order.order_ongoing:
            return square_order.add_item_to_order(item_id, quantity)
        else:
            return square_order.create_order(item_id, quantity)


class MakeOrderCheckoutTool(BaseTool):
    """Tool for initiating a checkout on a square terminal."""
    name = "make_order_checkout"
    description = "for when the customer wants to checkout their order. \
        Important** ONLY call this when the customer is asking to check out."

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return square_order.start_checkout()


class FindItemIdTool(BaseTool):
    """Tool for finding the square id corresponding to the natural language input item"""
    name = "find_item_id_tool"
    description = "For finding the item IDs corresponding to the name of a menu item. \
        Do not hallucinate."
    args_schema: Type[FindItemIdSchema] = FindItemIdSchema

    def _run(
        self, name, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Check the menu for a similar match."""
        for obj in square_order.menu["objects"]:
            for variation in obj["item_data"]["variations"]:
                temp_item = (
                    (
                        variation["item_variation_data"]["name"]
                        + " "
                        + obj["item_data"]["name"]
                    )
                    .lower()
                    .replace(",", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                temp_name = (
                    name.lower()
                    .replace(",", "")
                    .replace("(", "")
                    .replace(")", "")
                    .split(" ")
                )
                same = True
                # TOdo replace with regex
                for ty in temp_item.split(" "):
                    same = same & (ty in temp_name)

                if same:
                    return variation["id"]

        # todo: improve errors
        return "Error: cannot find item in menu."


class GetOrderTool(BaseTool):
    """Tool for getting the order """
    name = "get_order_tool"
    description = "for retrieving the items in the customer's order."

    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Return the customer's current order"""
        return square_order.order_items
