""" Module for langchain tools
"""
from langchain.tools import Tool

import json

from  source.agents.agentv2.database.client import DatabaseClient
from  source.agents.agentv2.order import Order

db = DatabaseClient()
square_order = Order()

def validate_and_search(input_str: str):
    text_json = {}
    try: 
        text_json = json.loads(input_str)
    except:
        text_json = {"item_name" : input_str}

    if text_json == None:
        return "Cannot find the item you requested."    

    # make sure theres content.
    if len(text_json) == 0:
        return "Nothing to order in order_string."
    
    vec_sim = [] 
    for x in text_json.values():
        temp = x
        if isinstance(x, str):
            vec_sim.append(db.query(x))
        elif "item_name" in temp.keys():
            # append the similar items found in the database
            vec_sim.append(db.query(temp["item_name"]))
    return vec_sim

def get_item_details(item_string: str) -> str:
    """When people are wondering about details of their dish"""
    # try to convert the JSON string into a List[dict].
    # if that fails, its usually just the name of an item.
        
    if item_string == None:
        return "Did not get any input from the user. Prompt the user to try again."
    
    vector_similarities = validate_and_search(item_string)

    # if there was nothing similar
    if len(vector_similarities) == 0 or vector_similarities == [[]]:
        return "there were no dishes similar to the ones you requested."
    else:
        return vector_similarities[0][0]['description']

# used in OrderTool
def order(
        order_string: str,
    ) -> str:
    """ order tool called to place and update orders.
    
    the order_string dict can be verbose. From testing, the general item ordered is
    correct 99% of the time, but potentially when distance >= 1, we should add
    human-in-the-loop to verify or clarify that certain item.
    I don't think the other orders should fail, so add HITL after placing orders. 
    """

    # try convert the input JSON string to a dict.
    try: 
        text_json = json.loads(order_string)
    except:
        return "order_string was not valid JSON."
    
    if text_json == None or order_string == None or len(text_json) == 0:
        return "Did not get any input from the user. Prompt the user to try again."
    
    # vec_similarities will hold the results of a vector search for each item requested in order_string
    vec_similarities = []
    failed_orders = []
    succeeded_orders = []

    for i in range(len(text_json)):
        # empty note by default
        note = ""
        # LLM hopefully correctly formatted and created a "order_note" field.
        if "order_note" in text_json[i].keys():
            # Occasionally the LLM likes to create the "order_note" field 
            # with a value of `null`, json.loads() converts null to NoneType
            # we dont want this b/c converting NoneType to str throws errors.
            if text_json[i]["order_note"] != None:
                note = text_json[i]["order_note"]
        
        # this is the string we are going to query the vecDB with.
        search_string = text_json[i]["item_name"] + " " + note
        query_results = db.query(search_string)

        print(query_results)
        
        # If the query can't find the item, add that input to the failed_orders.
        # otherwise, place the order.
        if query_results == []:
            failed_orders.append(search_string) 
        else:
            if not square_order.order_ongoing:
                success = square_order.create_order(
                    query_results[0]['item_id'], # the [0] index is bc we want the most similar vector.
                    text_json[i]["quantity_ordered"],
                    note
                )
            else:
                success = square_order.add_item_to_order(
                    query_results[0]['item_id'],
                    text_json[i]["quantity_ordered"],
                    note
                )
            if not success:
                failed_orders.append(query_results[0]["name"])
            else:
                succeeded_orders.append(query_results[0]["name"])   

    # nice output to user        
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
