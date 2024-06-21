import os
import math
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure o pydub para usar o ffmpeg
AudioSegment.converter = which("ffmpeg")


def convert_audio_to_wav(input_file):
    # Define o arquivo de saída como WAV
    output_file = "converted_audio.wav"

    try:
        # Converte o arquivo para WAV usando pydub
        audio = AudioSegment.from_file(input_file)
        audio.export(output_file, format="wav")
        print(f"Arquivo convertido para WAV: {output_file}")
        return output_file
    except Exception as e:
        print(f"Erro ao converter o arquivo: {e}")
        return None


def transcribe_chunk(chunk, recognizer):
    try:
        with sr.AudioFile(chunk) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="pt-BR")
                return text
            except sr.UnknownValueError:
                return "[Inaudível]"
            except sr.RequestError as e:
                return f"[Erro ao transcrever o áudio: {e}]"
    except Exception as e:
        return f"[Erro ao processar o chunk {chunk}: {e}]"


def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()

    try:
        # Carrega o arquivo de áudio usando pydub
        audio = AudioSegment.from_wav(audio_file)
        duration_in_sec = len(audio) / 1000
        chunk_size = 30 * 1000  # 30 segundos em milissegundos
        chunks = []

        for i in range(0, math.ceil(duration_in_sec * 1000), chunk_size):
            chunk = audio[i:i + chunk_size]
            chunk_file = f"temp_chunk_{i}.wav"
            chunk.export(chunk_file, format="wav")
            chunks.append(chunk_file)
            print(f"Chunk criado: {chunk_file}")

        # Processa os chunks em paralelo
        transcription = ""
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(transcribe_chunk, chunk, recognizer) for chunk in chunks]
            for future in as_completed(futures):
                transcription += future.result() + " "

        # Limpa os arquivos temporários
        for chunk_file in chunks:
            os.remove(chunk_file)
            print(f"Chunk removido: {chunk_file}")

        return transcription
    except Exception as e:
        return f"Erro ao processar o arquivo de áudio: {e}"


def main(input_file, output_file):
    # Verifica se o arquivo de entrada existe
    if not os.path.isfile(input_file):
        print(f"O arquivo {input_file} não existe.")
        return

    # Verifica se o arquivo de entrada é um WAV
    if not input_file.lower().endswith('.wav'):
        print("Convertendo o arquivo para WAV...")
        wav_file = convert_audio_to_wav(input_file)
        if wav_file is None:
            print("Falha na conversão do arquivo.")
            return
    else:
        wav_file = input_file

    print("Transcrevendo o áudio...")
    transcription = transcribe_audio(wav_file)

    # Salva a transcrição em um arquivo
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(transcription)

        print("Transcrição salva em:", output_file)
    except Exception as e:
        print(f"Erro ao salvar a transcrição: {e}")


# arquivo e caminho
if __name__ == "__main__":
    # caminho do arquivo de audio
    input_file = "/Users/albersonferreira/Downloads/Entrevistas/Gravações/2.[André Santos][07-jun-2024][on-line][laptop].m4a"
    # camimho de armazenamento da transcrição
    output_file = "./AndreSantos.txt"
    main(input_file, output_file)
