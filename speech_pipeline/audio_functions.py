#import pyaudio
# import wave
import pygame
from pydub import AudioSegment

#def record_audio(file_name, duration=5, sample_rate=16000, channels=2, chunk_size=1024):
#    p = pyaudio.PyAudio()
#
#    stream = p.open(format=pyaudio.paInt16,
#                    channels=channels,
#                    rate=sample_rate,
#                    input=True,
#                    frames_per_buffer=chunk_size)
#
#    print("Recording...")
#
#   frames = []
#    for i in range(0, int(sample_rate / chunk_size * duration)):
#        data = stream.read(chunk_size)
#        frames.append(data)
#
#    print("Recording complete.")
#
#    stream.stop_stream()
#    stream.close()
#    p.terminate()
#
#    # Save the audio to a WAV file
#    wf = wave.open(file_name, 'wb')
#    wf.setnchannels(channels)
#    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
#    wf.setframerate(sample_rate)
#    wf.writeframes(b''.join(frames))
#    wf.close()

def convert_to_standard_wav(filename):
    sound = AudioSegment.from_file(filename)
    sound.export(filename, format="wav")
    
def play_audio(file_name):
    pygame.init()
    pygame.mixer.init()

    pygame.mixer.music.load(file_name)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.quit()
    pygame.quit()