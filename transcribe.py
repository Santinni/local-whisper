import os
import sys
import time
import json
import datetime
import logging
from faster_whisper import WhisperModel, BatchedInferencePipeline
from colorama import init, Fore, Style

# Inicializace barev
init()

# Nastavení loggingu
logging.basicConfig()
logger = logging.getLogger("faster_whisper")

# --- POMOCNÉ FUNKCE PRO FORMÁTOVÁNÍ ČASU ---
def format_timestamp_srt(seconds):
    """Převede sekundy na formát SRT (HH:MM:SS,mmm)"""
    td = datetime.timedelta(seconds=seconds)
    # timedelta string je např. "0:00:12.345000"
    # Potřebujeme ho rozebrat a zformátovat
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def format_timestamp_vtt(seconds):
    """Převede sekundy na formát VTT (HH:MM:SS.mmm)"""
    return format_timestamp_srt(seconds).replace(",", ".")

# --- NAČTENÍ KONFIGURACE ---
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "model_size": "medium",
    "device": "auto",
    "output_formats": ["txt", "srt"],
    "output_dir": "transcriptions",
    "use_batched_inference": False,
    "batch_size": 16,
    "word_timestamps": False,
    "log_progress": True
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Odstranit komentáře (začínající _)
            return {k: v for k, v in config.items() if not k.startswith("_")}
    return DEFAULT_CONFIG

# --- HLAVNÍ LOGIKA ---
def transcribe_file(audio_path):
    config = load_config()
    
    if not os.path.exists(audio_path):
        print(f"{Fore.RED}[CHYBA]{Style.RESET_ALL} Soubor '{audio_path}' nenalezen.")
        return

    # Příprava výstupní složky
    output_dir = config.get("output_dir", "transcriptions")
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    
    # Detekce zařízení
    device = config.get("device", "auto")
    compute_type = config.get("compute_type", "float16")
    
    if device == "auto":
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            print(f"{Fore.GREEN}[DEVICE]{Style.RESET_ALL} Používám NVIDIA GPU (CUDA).")
        else:
            device = "cpu"
            compute_type = "int8"
            print(f"{Fore.YELLOW}[DEVICE]{Style.RESET_ALL} Používám CPU (přepínám na int8).")

    try:
        print(f"{Fore.CYAN}[INIT]{Style.RESET_ALL} Načítám model '{config['model_size']}'...")
        
        # Konfigurace loggingu
        if config.get("log_progress", True):
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
        
        model = WhisperModel(
            config['model_size'], 
            device=device, 
            compute_type=compute_type,
            download_root=os.path.join(os.getcwd(), "models")
        )

        print(f"{Fore.CYAN}[START]{Style.RESET_ALL} Začínám přepis: {audio_path}")
        start_time = time.time()

        # Rozhodnutí mezi batched a sequential inference
        use_batched = config.get("use_batched_inference", False)
        
        if use_batched:
            print(f"{Fore.MAGENTA}[MODE]{Style.RESET_ALL} Používám BatchedInferencePipeline (4-8x rychlejší)")
            batched_model = BatchedInferencePipeline(model=model)
            transcribe_func = batched_model.transcribe
        else:
            print(f"{Fore.MAGENTA}[MODE]{Style.RESET_ALL} Používám standardní režim")
            transcribe_func = model.transcribe

        # Sestavení parametrů pro transcribe
        transcribe_params = {
            "audio": audio_path,
            "beam_size": config.get("beam_size", 5),
            "language": config.get("language"),
            "vad_filter": config.get("vad_filter", True),
            "log_progress": config.get("log_progress", True),
            "word_timestamps": config.get("word_timestamps", False),
            "condition_on_previous_text": config.get("condition_on_previous_text", True),
        }
        
        # Přidat VAD parametry pouze pokud je VAD zapnutý
        if config.get("vad_filter", True):
            transcribe_params["vad_parameters"] = dict(
                min_silence_duration_ms=config.get("min_silence_duration_ms", 500)
            )
        
        # Přidat initial_prompt pokud je nastaven
        initial_prompt = config.get("initial_prompt", "").strip()
        if initial_prompt:
            transcribe_params["initial_prompt"] = initial_prompt
            print(f"{Fore.YELLOW}[PROMPT]{Style.RESET_ALL} Použit initial prompt pro zlepšení kvality")
        
        # Přidat temperature fallback pro zvýšení spolehlivosti
        if "temperature" in config:
            transcribe_params["temperature"] = config["temperature"]
        
        # Pokročilé parametry kvality
        if "compression_ratio_threshold" in config:
            transcribe_params["compression_ratio_threshold"] = config["compression_ratio_threshold"]
        if "log_prob_threshold" in config:
            transcribe_params["log_prob_threshold"] = config["log_prob_threshold"]
        if "no_speech_threshold" in config:
            transcribe_params["no_speech_threshold"] = config["no_speech_threshold"]
        
        # Repetition control
        if config.get("repetition_penalty", 1.0) != 1.0:
            transcribe_params["repetition_penalty"] = config["repetition_penalty"]
        if config.get("no_repeat_ngram_size", 0) > 0:
            transcribe_params["no_repeat_ngram_size"] = config["no_repeat_ngram_size"]
        
        # Batch size pro batched inference
        if use_batched:
            transcribe_params["batch_size"] = config.get("batch_size", 16)

        # Samotný přepis
        segments_generator, info = transcribe_func(**transcribe_params)

        print(f"{Fore.MAGENTA}[INFO]{Style.RESET_ALL} Jazyk: {info.language.upper()} ({info.language_probability:.0%})")
        if hasattr(info, 'duration_after_vad'):
            print(f"{Fore.MAGENTA}[INFO]{Style.RESET_ALL} Délka zvuku: {info.duration:.2f}s (po VAD: {info.duration_after_vad:.2f}s)")
        else:
            print(f"{Fore.MAGENTA}[INFO]{Style.RESET_ALL} Délka zvuku: {info.duration:.2f}s")
        print(f"{Fore.MAGENTA}--------------------------------------------------{Style.RESET_ALL}")

        # Kolekce segmentů pro uložení
        segments = []
        
        # Iterace přes generátor (tady probíhá inference)
        for i, segment in enumerate(segments_generator, start=1):
            line = f"[{format_timestamp_srt(segment.start)} --> {format_timestamp_srt(segment.end)}] {segment.text.strip()}"
            print(f"{Fore.BLUE}#{i}{Style.RESET_ALL} {line}")
            
            # Pokud máme word timestamps, ukážeme je
            if config.get("word_timestamps", False) and hasattr(segment, 'words') and segment.words:
                for word in segment.words[:3]:  # Ukázka prvních 3 slov
                    print(f"    {Fore.CYAN}└─ {word.word} [{word.start:.2f}s]{Style.RESET_ALL}")
                if len(segment.words) > 3:
                    print(f"    {Fore.CYAN}└─ ... (+{len(segment.words)-3} slov){Style.RESET_ALL}")
            
            segments.append(segment)

        duration = time.time() - start_time
        print(f"{Fore.MAGENTA}--------------------------------------------------{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[HOTOVO]{Style.RESET_ALL} Čas zpracování: {duration:.2f}s")

        # --- EXPORTY ---
        formats = config.get("output_formats", ["txt"])
        
        # 1. TXT Export
        if "txt" in formats:
            path = os.path.join(output_dir, f"{base_name}.txt")
            with open(path, "w", encoding="utf-8") as f:
                for s in segments:
                    f.write(f"[{format_timestamp_srt(s.start)}] {s.text.strip()}\n")
            print(f" - Uloženo: {path}")

        # 2. SRT Export (Titulky)
        if "srt" in formats:
            path = os.path.join(output_dir, f"{base_name}.srt")
            with open(path, "w", encoding="utf-8") as f:
                for i, s in enumerate(segments, start=1):
                    f.write(f"{i}\n")
                    f.write(f"{format_timestamp_srt(s.start)} --> {format_timestamp_srt(s.end)}\n")
                    f.write(f"{s.text.strip()}\n\n")
            print(f" - Uloženo: {path}")

        # 3. VTT Export (Web Titulky)
        if "vtt" in formats:
            path = os.path.join(output_dir, f"{base_name}.vtt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                for s in segments:
                    f.write(f"{format_timestamp_vtt(s.start)} --> {format_timestamp_vtt(s.end)}\n")
                    f.write(f"{s.text.strip()}\n\n")
            print(f" - Uloženo: {path}")

        # 4. JSON Export (Metadata)
        if "json" in formats:
            path = os.path.join(output_dir, f"{base_name}.json")
            data = {
                "source": audio_path,
                "language": info.language,
                "duration": info.duration,
                "segments": []
            }
            
            for s in segments:
                segment_data = {
                    "id": s.id,
                    "start": s.start,
                    "end": s.end,
                    "text": s.text.strip()
                }
                
                # Přidat word timestamps pokud jsou dostupné
                if config.get("word_timestamps", False) and hasattr(s, 'words') and s.words:
                    segment_data["words"] = [
                        {
                            "word": w.word,
                            "start": w.start,
                            "end": w.end,
                            "probability": w.probability
                        } for w in s.words
                    ]
                
                data["segments"].append(segment_data)
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f" - Uloženo: {path}")

    except Exception as e:
        print(f"{Fore.RED}[CHYBA]{Style.RESET_ALL} {e}")
        if "cudnn" in str(e).lower() or "cublas" in str(e).lower():
            print(f"{Fore.YELLOW}[TIP]{Style.RESET_ALL} Chybí NVIDIA knihovny (cuDNN/cuBLAS). Viz README.md sekce 'Zprovoznění na NVIDIA GPU'.")
        elif "out of memory" in str(e).lower():
            print(f"{Fore.YELLOW}[TIP]{Style.RESET_ALL} Nedostatek GPU paměti. Zkuste menší model nebo batch_size v config.json.")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{Fore.CYAN}Local Whisper Transcriber v0.1.0-beta{Style.RESET_ALL}")
        print(f"Použití: uv run transcribe.py <cesta_k_souboru> [<další_soubor> ...]")
        print(f"\nPříklady:")
        print(f"  uv run transcribe.py audio.mp3")
        print(f"  uv run transcribe.py audio1.mp3 audio2.wav video.mp4")
        print(f"\nNastavení upravte v souboru config.json")
    else:
        # Podpora více souborů najednou
        for audio_file in sys.argv[1:]:
            transcribe_file(audio_file)
            print()  # Prázdný řádek mezi soubory
