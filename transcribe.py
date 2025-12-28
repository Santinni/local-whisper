import os
import sys
import time
import json
import datetime
import logging
import argparse
import shutil
import tempfile
import subprocess
from faster_whisper import WhisperModel, BatchedInferencePipeline
from colorama import init, Fore, Style

# Inicializace barev
init()

# Nastavení loggingu
logging.basicConfig()
logger = logging.getLogger("faster_whisper")


FFMPEG_DECODE_EXTS = {
    ".m4a",
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".aac",
    ".m4b",
}


def _get_ffmpeg_exe() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe

    # Fallback: imageio-ffmpeg provides a bundled ffmpeg binary (downloads on first use).
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _maybe_decode_to_wav(input_path: str, output_dir: str) -> tuple[str, str | None]:
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".wav" or ext not in FFMPEG_DECODE_EXTS:
        return input_path, None

    ffmpeg_exe = _get_ffmpeg_exe()
    if not ffmpeg_exe:
        raise RuntimeError(
            "Pro dekódování .m4a/.mp4 je potřeba ffmpeg. "
            "Nainstalujte ffmpeg do systému, nebo doinstalujte závislost 'imageio-ffmpeg' a spusťte znovu."
        )

    os.makedirs(output_dir, exist_ok=True)
    fd, tmp_wav = tempfile.mkstemp(prefix="local_whisper_", suffix=".wav", dir=output_dir)
    os.close(fd)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        input_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        tmp_wav,
    ]
    subprocess.run(cmd, check=True)
    return tmp_wav, tmp_wav

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
DEFAULT_CONFIG_FILE = "config.json"
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

def load_config(config_file: str):
    config_file = os.path.normpath(os.path.expanduser(os.path.expandvars(config_file)))

    config = dict(DEFAULT_CONFIG)
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            # Odstranit komentáře (začínající _)
            loaded = {k: v for k, v in loaded.items() if not k.startswith("_")}
            config.update(loaded)

    return config


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="local-whisper",
        description="Lokální přepis řeči na text pomocí faster-whisper (GPU/CPU).",
    )
    parser.add_argument("files", nargs="*", help="Cesty k audio/video souborům")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_FILE,
        help=f"Cesta ke konfiguraci (default: {DEFAULT_CONFIG_FILE}).",
    )

    # Quality-first overrides (přebijí config.json)
    parser.add_argument("--model", dest="model_size", help="Velikost modelu (např. large-v3)")
    parser.add_argument("--lang", dest="language", help="Jazyk (např. cs)")
    parser.add_argument("--beam", dest="beam_size", type=int, help="Beam size")
    parser.add_argument("--best-of", dest="best_of", type=int, help="Best-of")
    parser.add_argument("--patience", dest="patience", type=float, help="Beam search patience")
    parser.add_argument("--hotwords", dest="hotwords", help="Preferovaná slova/fráze")
    parser.add_argument(
        "--hallucination-silence-threshold",
        dest="hallucination_silence_threshold",
        type=float,
        help="Potlačení halucinací po delším tichu (sekundy)",
    )
    parser.add_argument("--vad", dest="vad_filter", action="store_true", help="Zapnout VAD")
    parser.add_argument("--no-vad", dest="vad_filter", action="store_false", help="Vypnout VAD")
    parser.set_defaults(vad_filter=None)
    parser.add_argument("--batched", dest="use_batched_inference", action="store_true", help="Zapnout batched")
    parser.add_argument("--no-batched", dest="use_batched_inference", action="store_false", help="Vypnout batched")
    parser.set_defaults(use_batched_inference=None)

    return parser.parse_args(argv)

# --- HLAVNÍ LOGIKA ---
def transcribe_file(audio_path, config, model_cache):

    # Normalizace cesty (podpora %USERPROFILE%, ~, relativních cest)
    audio_path = os.path.normpath(os.path.expanduser(os.path.expandvars(audio_path)))
    
    if not os.path.exists(audio_path):
        print(f"{Fore.RED}[CHYBA]{Style.RESET_ALL} Soubor '{audio_path}' nenalezen.")
        return

    # Příprava výstupní složky
    output_dir = config.get("output_dir", "transcriptions")
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]

    decoded_audio_path = audio_path
    decoded_cleanup_path: str | None = None
    
    # Detekce zařízení
    device = config.get("device", "auto")
    compute_type = config.get("compute_type", "float16")
    
    if device == "auto":
        cuda_available = False

        # 1) Preferovat PyTorch detekci (když je nainstalovaný)
        try:
            import torch
            cuda_available = torch.cuda.is_available()
        except Exception:
            cuda_available = False

        # 2) Fallback: ctranslate2 detekce (faster-whisper backend)
        if not cuda_available:
            try:
                import ctranslate2
                if hasattr(ctranslate2, "get_cuda_device_count"):
                    cuda_available = ctranslate2.get_cuda_device_count() > 0
            except Exception:
                cuda_available = False

        if cuda_available:
            device = "cuda"
            print(f"{Fore.GREEN}[DEVICE]{Style.RESET_ALL} Používám NVIDIA GPU (CUDA).")
        else:
            device = "cpu"
            compute_type = "int8"
            print(f"{Fore.YELLOW}[DEVICE]{Style.RESET_ALL} Používám CPU (přepínám na int8).")

    try:
        # Dekódování formátů jako .m4a (bez systémového ffmpeg se použije imageio-ffmpeg)
        decoded_audio_path, decoded_cleanup_path = _maybe_decode_to_wav(audio_path, output_dir)
        if decoded_cleanup_path:
            print(f"{Fore.CYAN}[DECODE]{Style.RESET_ALL} Vstup '{os.path.basename(audio_path)}' → dočasný WAV pro přepis")

        model_key = (config.get("model_size"), device, compute_type)

        if model_key in model_cache:
            model = model_cache[model_key]
        else:
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
            model_cache[model_key] = model

        # Konfigurace loggingu (pro cached model taky)
        if config.get("log_progress", True):
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)

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
            "audio": decoded_audio_path,
            "beam_size": config.get("beam_size", 5),
            "language": config.get("language"),
            "vad_filter": config.get("vad_filter", True),
            "log_progress": config.get("log_progress", True),
            "word_timestamps": config.get("word_timestamps", False),
            "condition_on_previous_text": config.get("condition_on_previous_text", True),
        }

        # Další podporované parametry (pokud jsou v configu), pro vyšší kvalitu / kontrolu
        passthrough_keys = {
            "task",
            "best_of",
            "patience",
            "length_penalty",
            "prompt_reset_on_temperature",
            "initial_prompt",
            "prefix",
            "suppress_blank",
            "suppress_tokens",
            "without_timestamps",
            "max_initial_timestamp",
            "prepend_punctuations",
            "append_punctuations",
            "max_new_tokens",
            "chunk_length",
            "clip_timestamps",
            "hallucination_silence_threshold",
            "hotwords",
            "language_detection_threshold",
            "language_detection_segments",
            "multilingual",
        }
        for key in passthrough_keys:
            if key in config and config[key] is not None and key not in transcribe_params:
                transcribe_params[key] = config[key]
        
        # Přidat VAD parametry pouze pokud je VAD zapnutý
        if config.get("vad_filter", True):
            # Umožnit plné přepsání vad_parameters z configu (dict nebo VadOptions)
            if "vad_parameters" in config and config["vad_parameters"] is not None:
                transcribe_params["vad_parameters"] = config["vad_parameters"]
            else:
                transcribe_params["vad_parameters"] = dict(
                    min_silence_duration_ms=config.get("min_silence_duration_ms", 500)
                )
        
        # Přidat initial_prompt pokud je nastaven
        initial_prompt = (config.get("initial_prompt") or "").strip()
        if initial_prompt and "initial_prompt" not in transcribe_params:
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

    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}[CHYBA]{Style.RESET_ALL} Nepodařilo se dekódovat audio přes ffmpeg: {e}")
        print(
            f"{Fore.YELLOW}[TIP]{Style.RESET_ALL} Zkuste nainstalovat ffmpeg (winget install Gyan.FFmpeg) "
            "nebo použít MP3/WAV vstup."
        )
    except Exception as e:
        print(f"{Fore.RED}[CHYBA]{Style.RESET_ALL} {e}")
        if "cudnn" in str(e).lower() or "cublas" in str(e).lower():
            print(f"{Fore.YELLOW}[TIP]{Style.RESET_ALL} Chybí NVIDIA knihovny (cuDNN/cuBLAS). Viz README.md sekce 'Zprovoznění na NVIDIA GPU'.")
        elif "out of memory" in str(e).lower():
            print(f"{Fore.YELLOW}[TIP]{Style.RESET_ALL} Nedostatek GPU paměti. Zkuste menší model nebo batch_size v config.json.")
        import traceback
        traceback.print_exc()

    finally:
        if decoded_cleanup_path and os.path.exists(decoded_cleanup_path):
            try:
                os.remove(decoded_cleanup_path)
            except Exception:
                pass

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    if not args.files:
        print(f"{Fore.CYAN}Local Whisper Transcriber v0.1.0-beta{Style.RESET_ALL}")
        print(f"Použití: uv run transcribe.py [--config config.json] <cesta_k_souboru> [<další_soubor> ...]")
        print(f"\nPříklady:")
        print(f"  uv run transcribe.py audio.mp3")
        print(f"  uv run transcribe.py --config config.hq.json audio.mp3")
        print(f"  uv run transcribe.py audio1.mp3 audio2.wav video.mp4")
        print(f"\nNastavení upravte v souboru config.json")
    else:
        config = load_config(args.config)

        # CLI overrides (jen pokud jsou zadány)
        if args.model_size:
            config["model_size"] = args.model_size
        if args.language:
            config["language"] = args.language
        if args.beam_size is not None:
            config["beam_size"] = args.beam_size
        if args.best_of is not None:
            config["best_of"] = args.best_of
        if args.patience is not None:
            config["patience"] = args.patience
        if args.hotwords:
            config["hotwords"] = args.hotwords
        if args.hallucination_silence_threshold is not None:
            config["hallucination_silence_threshold"] = args.hallucination_silence_threshold
        if args.vad_filter is not None:
            config["vad_filter"] = args.vad_filter
        if args.use_batched_inference is not None:
            config["use_batched_inference"] = args.use_batched_inference

        model_cache = {}
        # Podpora více souborů najednou
        for audio_file in args.files:
            transcribe_file(audio_file, config=config, model_cache=model_cache)
            print()  # Prázdný řádek mezi soubory
