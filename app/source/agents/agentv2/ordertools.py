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
    # try to convert the JSON string into a List[dict].
    # if that fails, its usually just the name of an item.
    # TODO: move all this input checking into own function
    
    if item_string == None:
        return "Cannot find the item you requested."
     
    text_json = {}
    try: 
        text_json = json.loads(item_string)
    except:
        text_json = {"item_name" : item_string}

    if text_json == None:
        return "Cannot find the item you requested."    

    # make sure theres content.
    if len(text_json) == 0:
        return "Nothing to order in order_string."
    
    vec_similarities = [] 
    for x in text_json.values():
        temp = x
        if isinstance(x, str):
            vec_similarities.append(db.query(x))
        elif "item_name" in temp.keys():
            # append the similar items found in the database
            vec_similarities.append(db.query(temp["item_name"]))

    print(vec_similarities)

    # if there was nothing similar
    if len(vec_similarities) == 0 or vec_similarities == [[]]:
        return "there were no dishes similar to the ones you requested."  
    return vec_similarities[0][0]['description']

# used in OrderTool
def order(
        order_string: str,
    ) -> str:

    # try convert the input JSON string to a dict.
    try: 
        text_json = json.loads(order_string)
    except:
        return "order_string was not valid JSON."
    
    if text_json == None:
        return "Cannot find the item you requested."    

    # check for content
    if len(text_json) == 0:
        return "Nothing to order in order_string."
    else:
        vec_similarities = []
        for i in range(len(text_json)):
            note = ""
            if "order_note" in text_json[i].keys():
                if text_json[i]["order_note"] == None:
                    note = ""
                else: 
                    note = text_json[i]["order_note"]
            search_string = text_json[i]["item_name"] + " " + note
            print(search_string)
            augment_item = db.query(search_string)
            print(augment_item)
            if augment_item == []:
                failed_orders.append(search_string) 
            else:
                vec_similarities.append(augment_item)

    print(vec_similarities)    
    if len(vec_similarities) == 0 or vec_similarities == [[]]:
        return "Nothing you ordered is available on the menu."
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

        # sanity check. can probably remove 
        if vec_similarities[i] == []:
            continue
        elif not square_order.order_ongoing:
            # TODO: add error handling
            # please comment this
            success = square_order.create_order(
                vec_similarities[i][0]['item_id'],
                text_json[i]["quantity_ordered"],
                note
            )
            if not success:
                failed_orders.append(vec_similarities[i][0]["name"])
            else:
                succeeded_orders.append(vec_similarities[i][0]["name"])
        else:
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
        return f"""Your orders for {', '.join(succeeded_orders)}! Your total is now {square_order.get_order_total()}."""
    else:
        return f"""The orders for {', '.join(succeeded_orders)} succeeded, but the orders for {', '.join(failed_orders)} failed."""

# Below are all the tools.
OrderTool = Tool(
    name = "order_tool",
    description = "This tool is for creating new orders or adding items to existing orders.",
    return_direct=True, # dont want order tool to get called.
    func=order,
)

DescriptionTool = Tool(
    name = "get_item_details",
    description = "This tool is for getting descriptions for an item for customers.",
    return_direct=True, # dont want order tool to get called.
    func=get_item_details,
)
