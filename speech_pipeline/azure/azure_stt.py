# pip install azure-cognitiveservices-speech

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import azure.cognitiveservices.speech as speechsdk
from azure.azurecredentials import speech_key, service_region


def recognise_speech(filepath):
    # Creates an instance of a speech config with specified subscription key and service region.
    # Replace with your own subscription key and service region (e.g., "westus").
    # speech_key, service_region = "YourSubscriptionKey", "YourServiceRegion"
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    # audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True) # for microphone input
    audio_config = speechsdk.audio.AudioConfig(filename=filepath) # for file input

    # Creates a recognizer with the given settings
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # print("Say something...")

    # Note: Since recognize_once() returns only a single utterance, it is suitable only for single
    # shot recognition like command or query. 
    # Starts speech recognition, and returns after a single utterance is recognized. The end of a
    # single utterance is determined by listening for silence at the end or until a maximum of 15
    # seconds of audio is processed.  The task returns the recognition text as result. 
    # For long-running multi-utterance recognition, use start_continuous_recognition() instead.
    # Note: recognize_once_async operation to transcribe utterances of up to 30 seconds, or until silence is detected.
    result = speech_recognizer.recognize_once_async().get()

    # Checks result.
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(result.text))
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(result.no_match_details))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

    return result.text