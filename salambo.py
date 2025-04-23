import subprocess
from pydub import AudioSegment, silence
import os
import time

class config:
    # Chemin vers la vidéo
    video_path = "Untitled Video.mp4"

def extract_audio(video_path, audio_path="audio_temp.wav"):
    print("Extraction de l'audio en cours...")
    start_time = time.time()
    
    # Appel à ffmpeg en ligne de commande
    subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path, '-y'], check=True)
    
    end_time = time.time()
    print(f"Extraction de l'audio terminée en {end_time - start_time:.2f} secondes.")
    return audio_path

def split_on_silence(audio_path, silence_len=2000, silence_thresh=-50, padding=500):
    print("Découpage en segments sur les silences...")
    start_time = time.time()
    
    # Charger l'audio
    audio = AudioSegment.from_wav(audio_path)
    
    # Découper aux silences
    segments = silence.split_on_silence(audio,
                                        min_silence_len=silence_len,
                                        silence_thresh=silence_thresh,
                                        keep_silence=padding)
    
    end_time = time.time()
    print(f"Découpage terminé en {end_time - start_time:.2f} secondes. Nombre de segments : {len(segments)}.")
    return segments

def export_segments(segments, output_folder="segments"):
    print("Exportation des segments audio...")
    os.makedirs(output_folder, exist_ok=True)
    
    for i, segment in enumerate(segments):
        segment.export(f"{output_folder}/segment_{i+1}.wav", format="wav")
        print(f"Segment {i+1} exporté.")
    
    print("Exportation terminée.")

def process_video(video_path):
    audio_path = extract_audio(video_path)
    segments = split_on_silence(audio_path)
    export_segments(segments)
    print("Processus complet terminé.")


process_video(config.video_path)
