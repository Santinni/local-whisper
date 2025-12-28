# ⚡ Quick Start Guide

## 🚀 5 minut k prvnímu přepisu

### 1️⃣ Instalace (jednorázově)

```powershell
# Nainstalujte uv (pokud nemáte)
pip install uv

# Klonujte repozitář
git clone https://github.com/YOUR_USERNAME/local-whisper.git
cd local-whisper

# Inicializujte projekt
uv sync
```

### 2️⃣ První přepis

```powershell
uv run transcribe.py vase_audio.mp3
```

🎉 **To je vše!** Hotové přepisy najdete ve složce `transcriptions/` (lze změnit přes `output_dir` v configu).

Tip: při startu uvidíte log řádek `[DEVICE] ...` – pokud je k dispozici CUDA, běží to na NVIDIA GPU.

---

## ⚙️ Základní konfigurace

Projekt načítá konfiguraci z `config.json`. Pro kvalitu „1:1“ je připravený profil `config.hq.json`.

### Nejvyšší kvalita (doporučeno pro finální přepis)
```powershell
uv run transcribe.py --config config.hq.json vase_audio.mp3
```

### Pro rychlost (RTX GPU)
Upravte `config.json`:
```json
{
  "model_size": "medium",
  "use_batched_inference": true,
  "batch_size": 24
}
```

### Pro kvalitu
```json
{
  "model_size": "large-v3",
  "beam_size": 8,
  "word_timestamps": true
}
```

### Pro CPU (bez GPU)
```json
{
  "model_size": "small",
  "device": "cpu",
  "compute_type": "int8",
  "use_batched_inference": false
}
```

---

## 🎯 Časté use-case

### Přepis s vlastními jmény
```json
{
  "initial_prompt": "Ahoj, jsem Jan Novák a dnes mluvím o firmě TechCorp."
}
```

### Karaoke s word timing
```json
{
  "word_timestamps": true,
  "output_formats": ["srt", "json"]
}
```

### Více souborů najednou
```powershell
uv run transcribe.py video1.mp4 audio1.mp3 audio2.wav
```

### Přepis `.m4a` (a dalších video/audio formátů)
Není potřeba instalovat systémový ffmpeg – projekt umí formáty jako `.m4a/.mp4/.mov/...` automaticky dekódovat do dočasného WAV.
```powershell
uv run transcribe.py --config config.hq.json "C:\Users\<USER>\Downloads\recording_part_1.m4a"
```

---

## 🔧 Troubleshooting

### ❌ "Používám CPU" (ale mám GPU)
➡️ Nejčastěji jde o chybějící CUDA-enabled instalaci PyTorch nebo nekompatibilní driver. Viz [README.md - Zprovoznění na NVIDIA GPU](README.md#-zprovoznění-na-nvidia-gpu)

### ❌ "Out of memory"
➡️ Snižte `batch_size` v config.json:
```json
{ "batch_size": 8 }
```

### ❌ Špatná kvalita přepisu
➡️ Zvyšte beam_size a použijte initial_prompt:
```json
{
  "beam_size": 8,
  "initial_prompt": "kontext..."
}
```

### ❌ Přepis `.m4a` selže na ffmpeg
➡️ Projekt standardně použije zabalený ffmpeg (stažený na první použití). Pokud jste offline a ještě nebyl stažený, použijte systémový ffmpeg nebo převeďte soubor do `.wav`/`.mp3`.

---

## 📚 Další zdroje

- 📖 [README.md](README.md) - Kompletní dokumentace
- 🔍 [CODE_REVIEW.md](CODE_REVIEW.md) - Technické detaily
- ⚙️ [config.examples.json](config.examples.json) - Hotové příklady
- 📊 `uv run benchmark.py audio.mp3` - Otestujte rychlost

---

**Otázky?** Vytvořte [issue](../../issues/new) nebo se podívejte na [dokumentaci](README.md)! 🙋‍♂️
