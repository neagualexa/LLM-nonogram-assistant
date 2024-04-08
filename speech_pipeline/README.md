# Final Year Project - Verbal UI

This repository contains the `speech_pipeline` component for the verbal conversation with the AI assistant.

## Contents

The `speech_pipeline` folder contains the following:

1. `server.py` includes the flask server to run this component of the UI
2. `pipeline.py` caintains all the connections between all subcomponents of the verbal capabilities
3. `speech_to_text.py` converts the user's audio recorded in Unity into text
4. `text_to_speech.py` uses a natural voice dataset to generates an audio for the LLM's response

## How to Run

Follow the steps below to run the `speech_pipeline` project:

1. This is part of the AI Assistant repo, it will have to be run in parallel to the `app.py` from the main folder by running `run_assistant.bash`.
2. If you want to run it separately, then 
   1. Navigate to the `speech_pipeline` directory: `cd speech_pipeline`
   2. Install the required dependencies: `pip install -r requirements.txt` from main folder
   3. Run the main file: `python server.py`

