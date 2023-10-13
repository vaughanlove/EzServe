"""Simple ChromaDB client that the Agent can easily query.
Initializes with menu information from square.
"""
from square.client import Client
import chromadb
import os
import re
import json
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
        self.client = chromadb.Client()
        self.items = []
        self.ids = []
        self.metadatas = []
        self.__GetData()
        self.__PopulateDatabase()

    def __GetData(self):
        client = Client(
            access_token=os.getenv("API_KEY"),
            environment='sandbox'
        )

        logger.info("CHROMADB: Fetching menu from square api.")
        result = client.catalog.list_catalog(
            types = "ITEM"
        )
        for obj in result.body["objects"]:
            for variation in obj["item_data"]["variations"]:
                temp_item = variation["item_variation_data"]["name"] + " " + obj["item_data"]["name"]
                clean_item = re.sub(r"[^a-zA-Z0-9\s]","", temp_item).lower()
                
                # if the item has a cost. In the event the square owner didn't set a price,
                # don't let a user get free items.
                if "price_money" in variation["item_variation_data"].keys():
                    self.items.append(clean_item)
                    self.metadatas.append({"price" : variation["item_variation_data"]["price_money"]["amount"]})
                    self.ids.append(variation["id"])

    def __PopulateDatabase(self):
        logger.info("CHROMADB: Populating database.")
        self.collection = self.client.create_collection(name="menu")
        self.collection.add(
            documents=self.items,
            metadatas=self.metadatas,
            ids=self.ids
        )
    
    def query(self, items: List[str]):
        res = self.collection.query(query_texts=items, n_results=2)
        #print("\nChromaDB response: " + json.dumps(res))
        
        # everything is configured to work with weaviate embedded on linux, so just adapting the chromadb response to 
        # what weaviate would respond.

        response = []
        try: 
            response.append({
                'name' : res["documents"][0][0],
                'price' : res["metadatas"][0][0]["price"],
                'description' : "no description",
                '_additional' : {'score' : res["distances"][0][0]},
                'item_id' : res["ids"][0][0] 
                })
        except:
            print("there was an error with chromadb.")
    
        return response