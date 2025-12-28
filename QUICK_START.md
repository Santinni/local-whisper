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

🎉 **To je vše!** Hotové přepisy najdete ve složce `transcriptions/`

---

## ⚙️ Základní konfigurace

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

---

## 🔧 Troubleshooting

### ❌ "Používám CPU" (ale mám GPU)
➡️ Chybí CUDA knihovny. Viz [README.md - Zprovoznění na NVIDIA GPU](README.md#-zprovoznění-na-nvidia-gpu-rtx-30xx40xx)

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

---

## 📚 Další zdroje

- 📖 [README.md](README.md) - Kompletní dokumentace
- 🔍 [CODE_REVIEW.md](CODE_REVIEW.md) - Technické detaily
- ⚙️ [config.examples.json](config.examples.json) - Hotové příklady
- 📊 `uv run benchmark.py audio.mp3` - Otestujte rychlost

---

**Otázky?** Vytvořte [issue](../../issues/new) nebo se podívejte na [dokumentaci](README.md)! 🙋‍♂️
