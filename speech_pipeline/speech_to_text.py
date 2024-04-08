###### SPEECH to TEXT with Google SPEECH API
import speech_recognition as sr

def transcribe_audio(audio_file):
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Load audio file
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

    try:
        # Recognize the speech using Google Web Speech API
        # Set show_all=True to include all alternatives
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        print("Google Web Speech API could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Web Speech API; {e}")


###### SPEECH to TEXT with HUGGINGFACE MODELS

# from transformers import WhisperProcessor, WhisperForConditionalGeneration
# import librosa

# # load model and processor
# processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
# model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny")
# model.config.forced_decoder_ids = None                                                          # automatically task=transcribe for english
# # forced_decoder_ids = processor.get_decoder_prompt_ids(language="french", task="transcribe")   # if transcribe different language

# def speech_to_text(file_path, translate=False, duration=5, sample_rate=16000):
#     # Load the audio file
#     # waveform, sample_rate = torchaudio.load(file_path)
#     print("Loading audio file from ", file_path)
#     waveform, sample_rate = librosa.load(file_path, sr=None, mono=True)

#     # Preprocess the audio file
#     input_features = processor(waveform, sampling_rate=sample_rate, return_tensors="pt").input_features

#     # Generate the token IDs
#     predicted_ids = model.generate(input_features)
    
#     if translate:
#         forced_decoder_ids = processor.get_decoder_prompt_ids(language="french", task="translate")
#         predicted_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids)

#     # Decode the token IDs to text
#     transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)

#     return transcription
    
    
