# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import azure.cognitiveservices.speech as speechsdk
from azure.azurecredentials import speech_key, service_region

def vocalise_text(text, output_file_path=None):
    # Creates an instance of a speech config with specified subscription key and service region.
    # Replace with your own subscription key and service region (e.g., "westus").
    # speech_key, service_region = "YourSubscriptionKey", "YourServiceRegion"
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    # Set the voice name, refer to https://aka.ms/speech/voices/neural for full list.
    speech_config.speech_synthesis_voice_name = "en-GB-OliviaNeural" #(GB) SoniaNeural OliviaNeural

    # Creates a speech synthesizer using the default speaker as audio output.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    # Receives a text from console input.
    # print("Type some text that you want to speak...")
    # text = input()
    # text = "Hello, I am a text-to-speech service. I turn text into spoken words."

    # Synthesizes the received text to speech.
    # The synthesized speech is expected to be heard on the speaker with this line executed.
    result = speech_synthesizer.speak_text_async(text).get()

    # Checks result.
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized to speaker for text [{}]".format(text))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
        print("Did you update the subscription info?")
    
    if output_file_path:
        with open(output_file_path, "wb") as audio_file:
            audio_data = result.audio_data
            audio_file.write(audio_data)