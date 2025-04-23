<<<<<<< HEAD
import whisper
import os
from pydub import AudioSegment
import subprocess

# Liste des variantes de "Salambo" à détecter
SALAMBO_VARIANTS = ["salambo", "salimbo", "salam-bo", "salam beaux"]

def convert_mp4_to_mp3(input_file, output_file):
    temp_output_file = "temp_audio.mp3"
    command = f'ffmpeg -i "{input_file}" -q:a 0 -map a "{temp_output_file}" -y'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print("Erreur lors de l'exécution de ffmpeg :")
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, command)
    
    audio = AudioSegment.from_mp3(temp_output_file)
    audio.export(output_file, format="mp3")
    print(f"Audio conversion completed: {output_file}")
    os.remove(temp_output_file)

def transcribe_audio(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    print("Transcription terminée.")
    return result["segments"]

def find_salambo_segments(transcription_segments):
    salambo_times = []
    for seg in transcription_segments:
        text = seg['text']
        start_time = seg['start'] * 1000
        end_time = seg['end'] * 1000
        if any(variant in text.lower() for variant in SALAMBO_VARIANTS):
            salambo_times.append((start_time, end_time))
    return salambo_times

def generate_segments_and_verify(salambo_times, base_audio, output_folder="audio_segments"):
    last_end_time = 0
    segment_files = []
    model = whisper.load_model("base")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for idx, (start_time, end_time) in enumerate(salambo_times):
        segment_audio = base_audio[last_end_time:start_time]
        if len(segment_audio) > 0:
            audio_filename = os.path.join(output_folder, f"segment_{idx + 1}.mp3")
            segment_audio.export(audio_filename, format="mp3")
            segment_files.append(audio_filename)
            print(f"Segment sans 'Salambo' créé : {audio_filename}")
        
        # Vérification et ajustement du segment
        if verify_and_trim_segment(audio_filename, model):
            print(f"Vérification et ajustement effectués pour : {audio_filename}")

        last_end_time = end_time  # Met à jour pour le prochain segment

    # Segment après le dernier "Salambo"
    if last_end_time < len(base_audio):
        remaining_audio = base_audio[last_end_time:]
        audio_filename = os.path.join(output_folder, f"segment_{len(salambo_times) + 1}.mp3")
        remaining_audio.export(audio_filename, format="mp3")
        segment_files.append(audio_filename)
        print(f"Segment final sans 'Salambo' créé : {audio_filename}")

        if verify_and_trim_segment(audio_filename, model):
            print(f"Vérification et ajustement effectués pour : {audio_filename}")

    return segment_files

def verify_and_trim_segment(segment_path, model):
    """Transcrit le segment et supprime les occurrences de 'Salambo' si détecté."""
    segment_audio = AudioSegment.from_mp3(segment_path)
    result = model.transcribe(segment_path)
    
    salambo_intervals = []
    for seg in result["segments"]:
        text = seg['text']
        start_time = seg['start'] * 1000
        end_time = seg['end'] * 1000
        if any(variant in text.lower() for variant in SALAMBO_VARIANTS):
            salambo_intervals.append((start_time, end_time))

    # Suppression des intervalles contenant 'Salambo'
    if salambo_intervals:
        for start_time, end_time in salambo_intervals:
            segment_audio = segment_audio[:start_time] + segment_audio[end_time:]
        
        # Sauvegarde du segment après la suppression
        segment_audio.export(segment_path, format="mp3")
        print(f"'Salambo' supprimé de : {segment_path}")
        
    # Rogner les silences en début et fin après la suppression de 'Salambo'
    trimmed_segment = trim_silence_from_edges(segment_audio)
    trimmed_segment.export(segment_path, format="mp3")
    print(f"Silences rognés pour : {segment_path}")

    return True  # Modification effectuée

def trim_silence_from_edges(audio, silence_thresh=-35, padding=500):
    """Rogne les silences en début et fin d'un fichier audio avec une marge."""
    def detect_leading_silence(audio, silence_thresh=-35):
        trim_ms = 0
        while trim_ms < len(audio) and audio[trim_ms:trim_ms+10].dBFS < silence_thresh:
            trim_ms += 10
        return trim_ms

    start_trim = detect_leading_silence(audio, silence_thresh=silence_thresh)
    end_trim = detect_leading_silence(audio.reverse(), silence_thresh=silence_thresh)

    start_trim = max(0, start_trim - padding)
    end_trim = max(0, end_trim - padding)

    return audio[start_trim:len(audio) - end_trim]

# Chemins relatifs
mp4_path = "Untitled Video.mp4"
mp3_base_path = "votre_fichier_base.mp3"
output_folder = "audio_segments"

convert_mp4_to_mp3(mp4_path, mp3_base_path)
transcription_segments = transcribe_audio(mp3_base_path)
salambo_times = find_salambo_segments(transcription_segments)

base_audio = AudioSegment.from_mp3(mp3_base_path)
segment_files = generate_segments_and_verify(salambo_times, base_audio, output_folder)
=======
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
>>>>>>> da38d5a (Modification des variables config)
