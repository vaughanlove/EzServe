from google.cloud.translate_v2 import client as translate

class Translator(object):
    def translate(self, text: str) -> object:

        translate_client = translate.Client()

        if isinstance(text, bytes):
            text = text.decode("utf-8")

        #google cloud translation api call
        result = translate_client.translate(text, target_language="EN")

        return result["translatedText"]