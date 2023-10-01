""" Module for langchain tools
"""
from langchain.tools import Tool

import json

from  source.agents.agentv2.database.client import ChromaClient
from  source.agents.agentv2.order import Order

db = ChromaClient()
square_order = Order()

def get_item_details(item_string: str) -> str:
    """When people are wondering about details of their dish"""
    pass

# used in OrderTool
def order(
        order_string: str,
    ) -> str:
    if isinstance(order_string, dict):
        pass
    else:
        text_json = json.loads(order_string)
        # here I need to assert that text_json actually contains data.
        query_data = []
        for x in text_json:
            note = x["order_note"] if "order_note" in x.keys() else ""
            query_data.append(x["item_name"] + " " + note)

        # find similar vectors to the item_name + modifiers
        vec_similarities = db.query(query_data, 2)

        # since our prompt is made to store details about each item, the item_name in
        # the text_json dict can be verbose. From testing, the general item ordered is
        # correct 99% of the time, but perhaps when distance >= 1, we should add
        # human-in-the-loop to verify or clarify that certain item.
        # I don't think the other orders should fail, so add HITL after placing orders.

        succeeded_orders = []
        failed_orders = []

        for i in range(len(query_data)):
            # TODO: if vector distance >= 1, reaffirm with the user what they ordered, and allow them to change.

            note = text_json[i]["order_note"] if "order_note" in text_json[i].keys() else ""

            if not square_order.order_ongoing:
                # TODO: add error handling
                success = square_order.create_order(
                    vec_similarities["ids"][0][0],
                    text_json[i]["quantity_ordered"],
                    note
                )
                if not success:
                    failed_orders.append(vec_similarities["documents"][i][0])
                else:
                    succeeded_orders.append(vec_similarities["documents"][i][0])
            else:
                # really need to do graceful error handling, and keep track of what items were not ordered.
                success = square_order.add_item_to_order(
                    vec_similarities["ids"][i][0],
                    text_json[i]["quantity_ordered"],
                    note
                )

                if not success:
                    failed_orders.append(vec_similarities["documents"][i][0])
                else:
                    succeeded_orders.append(vec_similarities["documents"][i][0])
                
        if len(failed_orders) == 0:
            return f"Your orders for {succeeded_orders}! Your total is now {square_order.get_order_total()}."
        else:
            return f"""The orders for {succeeded_orders} succeeded, but the orders for {failed_orders} failed."""

# Below are all the tools.
OrderTool = Tool(
    name = "order_tool",
    description = "This tool is for creating new orders or adding items to existing orders.",
    func=order,
)