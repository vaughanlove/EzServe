"""Simple ChromaDB client that the Agent can easily query.
Initializes with menu information from square.
"""
from square.client import Client
import weaviate
from weaviate.embedded import EmbeddedOptions
import os
import re
from typing import List
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DatabaseClient(object):
    """ Class for connecting and querying the Chroma vector database.
    """

    def __init__(self):
        load_dotenv()
        logger.info("Initializing the chromadb client.")
        self.client = weaviate.Client(embedded_options=EmbeddedOptions())
        self.items = []
        self.ids = []
        self.metadatas = []
        self.__GetData()
        #self.__PopulateDatabase()

    def __GetData(self):
        square_client = Client(
            access_token=os.getenv("API_KEY"),
            environment='sandbox'
        )

        logger.info("CHROMADB: Fetching menu from square api.")
        result = square_client.catalog.list_catalog(
            types = "ITEM"
        )
        for obj in result.body["objects"]:
            for variation in obj["item_data"]["variations"]:
                temp_item = variation["item_variation_data"]["name"] + " " + obj["item_data"]["name"]
                clean_item = re.sub(r"[^a-zA-Z0-9\s]","", temp_item).lower()
                
                # if the item has a cost. In the event the square owner didn't set a price,
                # don't let a user get free items.
                if "price_money" in variation["item_variation_data"].keys():
                    #self.items.append(clean_item)
                    #self.metadatas.append({"price" : variation["item_variation_data"]["price_money"]["amount"]})
                    #self.ids.append(variation["id"])
                    data_obj = {
                        "name": clean_item,
                        "item_id": variation["id"],
                        "price": variation["item_variation_data"]["price_money"]["amount"]
                    }
                    self.client.data_object.create(data_obj, "menu_item")
                    
    def query(self, item: List[str]):
        res =  self.client.query.get("menu_item", ["name", "item_id", "price"]).with_bm25(query=item).with_limit(2).do()
        return res
