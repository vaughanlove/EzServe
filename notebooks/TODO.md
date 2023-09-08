# TODO

1. Abstract the user order/menu to reduce api calls. - this is done on `dev` but square dev api has been out for 12hours. 

## Agent

Should write a custom agent so I can have control over the prompt input. It would be interesting to give users the chance to:
1. pick the language they would like to interact with the bot with. (chirp can support 25+ languages)
2. pick the personality they would like their server to have
   
#### Questions
1. Should the agent have memory?
- Could potentially enable prompt injections or the possibility of misordering or hallucinating IDs.
- I could artificially introduce memory through a tool to retrieve to the user's current order.

## Chirp
Development currently with prerecorded .wav files because can't figure out how to find laptop interal mic with PyAudio in WSL.
Works fine - need to sit down and figure out architecture.


