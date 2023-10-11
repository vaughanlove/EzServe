"""For translating things to/from english.
We want to keep everything in the backend in one language so that we 
can always easily incorporate with any menu.
"""

from google.cloud.translate_v2 import client


def translate(text: str) -> object:
    """
    Instantiates GCloud translate client, determines input language and translates to english, returns results.
    """
    translate_client = client.Client()

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    result = translate_client.translate(text, target_language="EN")

    if result["translatedText"] is not None:
        print(f"EZ-Serve DETECTED LANGUAGE: {result['detectedSourceLanguage']}.")
        print(f"EZ-Serve TRANSLATED RESPONSE: {result['translatedText']}.")
        return result["detectedSourceLanguage"], result["translatedText"]
    else:
        return "en", """This is not a user input. The translation failsed
                and no output was found. **important** 
                now all you need to do is prompt the customer to try again."""
    
def translate_to_language(text: str, lang: str) -> object:
    """
    Translates to desired language.
    """
    translate_client = client.Client()

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    result = translate_client.translate(text, target_language=lang)


    if result["translatedText"] is not None:
        print(f"EZ-Serve TRANSLATED RESPONSE: {result['translatedText']}.")
        return result["translatedText"]
    else:
        return """This is not a user input. The translation failsed
                and no output was found. **important** 
                now all you need to do is prompt the customer to try again."""
