""" Module for langchain tools
"""
from langchain.tools import Tool

import json

from  source.agents.agentv2.database.client import DatabaseClient
from  source.agents.agentv2.order import Order

db = DatabaseClient()
square_order = Order()

def get_item_details(item_string: str) -> str:
    """When people are wondering about details of their dish"""
    text_json = {}
    try: 
        text_json = json.loads(item_string)
    except e:
        return "order_string was not valid JSON."
    
    print(text_json)
    
    if len(text_json) == 0:
        return "Nothing to order in order_string."
    else:
        vec_similarities = [] 
        for x in text_json:
            temp = x
            note = ""
            if isinstance(x, str):
                vec_similarities.append(db.query(x))

            elif "order_note" in temp.keys():
                if temp["order_note"] == None:
                    note = ""
                else:
                    note = temp["order_note"]
                vec_similarities.append(db.query(temp["item_name"]))

    if len(vec_similarities) == 0:
        return "there were no dishes similar to the one you requested."    
    return vec_similarities[0]['data']['Get']['Menu_item'][0]['description']

# used in OrderTool
def order(
        order_string: str,
    ) -> str:

    try: 
        text_json = json.loads(order_string)
    except e:
        return "order_string was not valid JSON."
    
    print(text_json)

    if len(text_json) == 0:
        return "Nothing to order in order_string."
    else:
        vec_similarities = [db.query(x["item_name"] + " " + (x["order_note"] if "order_note" in x.keys() else ""))['data']['Get']['Menu_item'] for x in text_json] 
    
    print(vec_similarities)
    if len(vec_similarities) == 0:
        return "Nothing you ordered on the menu is available."
    # since our prompt is made to store details about each item, the item_name in
    # the text_json dict can be verbose. From testing, the general item ordered is
    # correct 99% of the time, but perhaps when distance >= 1, we should add
    # human-in-the-loop to verify or clarify that certain item.
    # I don't think the other orders should fail, so add HITL after placing orders.

    succeeded_orders = []
    failed_orders = []

    for i in range(len(vec_similarities)):
        # TODO: if vector distance >= 1, reaffirm with the user what they ordered, and allow them to change.

        note = text_json[i]["order_note"] if "order_note" in text_json[i].keys() else ""
        
        if not square_order.order_ongoing:
            # TODO: add error handling
            success = square_order.create_order(
                vec_similarities[0][0]['item_id'],
                text_json[i]["quantity_ordered"],
                note
            )
            if not success:
                failed_orders.append(vec_similarities[i][0]["name"])
            else:
                succeeded_orders.append(vec_similarities[i][0]["name"])
        else:
            # really need to do graceful error handling, and keep track of what items were not ordered.
            success = square_order.add_item_to_order(
                vec_similarities[i][0]['item_id'],
                text_json[i]["quantity_ordered"],
                note
            )

            if not success:
                failed_orders.append(vec_similarities[i][0]["name"])
            else:
                succeeded_orders.append(vec_similarities[i][0]["name"])
            
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

DescriptionTool = Tool(
    name = "get_item_details",
    description = "This tool is for getting descriptions for an item for customers.",
    func=get_item_details,
)