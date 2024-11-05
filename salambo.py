import whisper
import os
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import subprocess

# Liste des variantes de "Salambo" à détecter
SALAMBO_VARIANTS = ["salambo", "salimbo", "salam-bo"]

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
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier MP3 spécifié n'a pas été trouvé : {file_path}")
    
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    print("Transcription terminée.")
    return result["segments"]

def find_salambo_segments(transcription_segments, output_folder):
    salambo_times = []
    transcription_file = os.path.join(output_folder, "transcription.txt")
    with open(transcription_file, "w") as f:
        f.write("Transcription complète des segments:\n\n")
        
        for seg in transcription_segments:
            text = seg['text']
            start_time = seg['start'] * 1000  # Convertir en ms
            end_time = seg['end'] * 1000
            
            # Enregistrer chaque segment dans le fichier de transcription
            f.write(f"[{seg['start']} - {seg['end']}] {text}\n")
            
            # Identifier les occurrences de "Salambo" et variantes
            if any(variant in text.lower() for variant in SALAMBO_VARIANTS):
                salambo_times.append((start_time, end_time))
                
    print(f"Transcription enregistrée dans {transcription_file}")
    return salambo_times

def generate_audio_segments_excluding_salambo(salambo_times, base_audio, output_folder="audio_by_keyword"):
    total_segment_duration = 0
    last_end_time = 0  # Dernier point de fin pour découper les segments
    keyword_count = 1
    segment_files = []  # Stocker les chemins des segments générés pour la seconde passe

    # Parcours des intervalles sans "Salambo"
    for (start_time, end_time) in salambo_times:
        cut_start_time = max(last_end_time, start_time - 800)
        segment_audio = base_audio[last_end_time:cut_start_time]
        segment_duration = len(segment_audio)
        total_segment_duration += segment_duration

        # Ajouter des pauses et exporter le segment
        pause = AudioSegment.silent(duration=500)
        final_audio = pause + segment_audio + pause
        audio_filename = os.path.join(output_folder, f"segment_{keyword_count}.mp3")
        final_audio.export(audio_filename, format="mp3")
        segment_files.append(audio_filename)  # Stocker le fichier segment pour la seconde passe
        print(f"Audio file created for segment {keyword_count}: {audio_filename}")
        keyword_count += 1

        last_end_time = end_time + 800

    # Ajouter l'audio restant après la dernière occurrence de "Salambo"
    if last_end_time < len(base_audio):
        remaining_audio = base_audio[last_end_time:]
        pause = AudioSegment.silent(duration=500)
        final_audio = pause + remaining_audio + pause
        audio_filename = os.path.join(output_folder, f"segment_{keyword_count}.mp3")
        final_audio.export(audio_filename, format="mp3")
        segment_files.append(audio_filename)
        total_segment_duration += len(remaining_audio)
        print(f"Final audio segment created: {audio_filename}")

    total_audio_duration = len(base_audio)
    print("\n--- Résumé des Durées ---")
    print(f"Durée totale de l'audio source : {total_audio_duration / 1000} secondes")
    print(f"Durée totale des segments générés : {total_segment_duration / 1000} secondes")

    return segment_files  # Retourner les fichiers segments pour la seconde passe

def trim_silence_from_edges(audio, silence_thresh=-35, min_silence_len=1000, padding=500):
    """
    Rogne les silences au début et à la fin du fichier audio, avec une marge de sécurité pour éviter de couper des parties de texte.
    
    :param audio: Un objet AudioSegment (le segment audio à traiter).
    :param silence_thresh: Seuil de silence en dBFS.
    :param min_silence_len: Durée minimale du silence pour être considéré comme tel, en millisecondes.
    :param padding: Marge en ms ajoutée avant et après le contenu non silencieux pour éviter les coupures.
    :return: Un nouvel objet AudioSegment avec les silences d'ouverture et de clôture rognés, avec marge de sécurité.
    """
    # Fonction interne pour détecter les silences
    def detect_leading_silence(audio, silence_thresh=-35):
        trim_ms = 0  # durée en ms à rogner au début
        while trim_ms < len(audio) and audio[trim_ms:trim_ms+10].dBFS < silence_thresh:
            trim_ms += 10
        return trim_ms

    # Calculer le silence au début et à la fin
    start_trim = detect_leading_silence(audio, silence_thresh=silence_thresh)
    end_trim = detect_leading_silence(audio.reverse(), silence_thresh=silence_thresh)

    # Ajouter une marge de sécurité pour conserver les transitions naturelles
    start_trim = max(0, start_trim - padding)
    end_trim = max(0, end_trim - padding)

    # Rogner les silences avec la marge
    trimmed_audio = audio[start_trim:len(audio) - end_trim]
    return trimmed_audio


def remove_salambo_from_segments(segment_files, output_folder):
    model = whisper.load_model("base")
    
    # Créer le sous-dossier pour les transcriptions de segments
    transcripts_folder = os.path.join(output_folder, "transcrits_segments")
    if not os.path.exists(transcripts_folder):
        os.makedirs(transcripts_folder)
    
    for segment_path in segment_files:
        segment_audio = AudioSegment.from_mp3(segment_path)
        
        # Transcrire chaque segment pour détecter "Salambo"
        result = model.transcribe(segment_path)
        
        # Créer un fichier de transcription spécifique pour chaque segment dans le sous-dossier
        segment_name = os.path.basename(segment_path).replace(".mp3", "")
        segment_transcript_file = os.path.join(transcripts_folder, f"{segment_name}_transcription.txt")
        
        with open(segment_transcript_file, "w") as f:
            f.write(f"Transcription du segment {segment_name}:\n\n")
            
            salambo_intervals = []
            for seg in result["segments"]:
                text = seg['text']
                start_time = seg['start'] * 1000
                end_time = seg['end'] * 1000
                f.write(f"[{seg['start']} - {seg['end']}] {text}\n")
                
                # Si une variante de "Salambo" est détectée, ajouter l'intervalle pour suppression
                if any(variant in text.lower() for variant in SALAMBO_VARIANTS):
                    salambo_intervals.append((start_time, end_time))

        for start_time, end_time in salambo_intervals:
            segment_audio = segment_audio[:start_time] + segment_audio[end_time:]
        
        # Rogner uniquement les silences en début et fin du segment audio
        segment_audio = trim_silence_from_edges(segment_audio)

        # Sauvegarder le segment mis à jour
        segment_audio.export(segment_path, format="mp3")
        print(f"Updated segment saved without 'Salambo' and silence: {segment_path}")

# Chemins relatifs
mp4_path = "Untitled Video.mp4"
mp3_base_path = "votre_fichier_base.mp3"

# Conversion du MP4 en MP3
convert_mp4_to_mp3(mp4_path, mp3_base_path)

# Transcription de l'audio en segments avec Whisper en local
transcription_segments = transcribe_audio(mp3_base_path)

# Identifier les segments contenant "Salambo" et sauvegarder la transcription
output_folder = "audio_by_keyword"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

salambo_times = find_salambo_segments(transcription_segments, output_folder)

# Générer les fichiers audio en excluant les intervalles autour de "Salambo"
base_audio = AudioSegment.from_mp3(mp3_base_path)
segment_files = generate_audio_segments_excluding_salambo(salambo_times, base_audio, output_folder)

# Deuxième passe pour supprimer "Salambo" et rogner les silences en début et fin de chaque segment
remove_salambo_from_segments(segment_files, output_folder)
