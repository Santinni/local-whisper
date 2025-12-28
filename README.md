# 🎙️ Local Whisper Transcriber

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-orange.svg)
![GPU](https://img.shields.io/badge/GPU-CUDA%20Ready-brightgreen.svg)

**Extrémně rychlý lokální Speech-to-Text pomocí faster-whisper**

[Funkce](#-klíčové-vlastnosti) • [Instalace](#-instalace-na-novém-počítači) • [Použití](#-použití) • [Konfigurace](#%EF%B8%8F-konfigurace-configjson) • [Dokumentace](#-další-dokumentace)

</div>

---

Jednoduchý, ale **extrémně výkonný** nástroj pro **lokální přepis řeči na text** (Speech-to-Text). Využívá optimalizovaný engine `faster-whisper` (až 4x rychlejší než originální OpenAI Whisper) a běží kompletně offline na vašem počítači.

## ✨ Klíčové vlastnosti

*   **100% Soukromí:** Žádná data se neposílají do cloudu. Vše běží u vás.
*   **GPU Akcelerace:** Plná podpora pro NVIDIA karty (CUDA) s automatickým přepnutím na CPU, pokud GPU není dostupné.
*   **Batched Inference:** Až **8x rychlejší** zpracování pomocí paralelního batch processingu.
*   **Word-level Timestamps:** Časové značky pro každé slovo (karaoke, detailní analýza).
*   **Initial Prompt:** Zlepšení přesnosti pro vlastní jména a odbornou terminologii.
*   **Temperature Fallback:** Automatická oprava při špatné kvalitě zvuku.
*   **Formáty:** Generuje nejen text (`.txt`), ale i titulky (`.srt`, `.vtt`) a metadata (`.json`).
*   **Detekce řeči (VAD):** Automaticky filtruje tichá místa pro přesnější přepis.
*   **Portable:** Díky nástroji `uv` má projekt izolované Python prostředí.
*   **Podpora `.m4a/.mp4/...`:** Automatické dekódování (ffmpeg) bez systémové instalace.

---

## 🚀 Instalace na novém počítači

Tento projekt používá moderní správce balíčků **`uv`**, který automaticky spravuje verzi Pythonu.

1.  **Nainstalujte `uv`** (pokud nemáte):
    ```powershell
    pip install uv
    # nebo
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Přejděte do složky projektu:**
    ```powershell
    cd local-whisper
    ```

3.  **Připravte prostředí (jednorázově):**
    Tento příkaz stáhne Python a všechny knihovny.
    ```powershell
    uv sync
    ```

---

## 🎮 Použití

### Základní přepis:
```powershell
uv run transcribe.py nahravka.mp3
```

### Přepis více souborů najednou:
```powershell
uv run transcribe.py audio1.mp3 audio2.wav video.mp4
```

### Změna nastavení:
Všechna nastavení (velikost modelu, jazyk, výstupní formáty, optimalizace) se dají měnit v souboru **`config.json`**.
Není potřeba zasahovat do kódu.

### Kvalita „1:1“ (doporučeno pro finální přepis)
Použijte připravený profil **`config.hq.json`**:
```powershell
uv run transcribe.py --config config.hq.json nahravka.mp3
```

### CLI přepínače (rychlé override bez úprav configu)
Skript podporuje několik přepínačů, které přepíší hodnoty z configu jen pro daný běh:
```powershell
uv run transcribe.py --config config.hq.json nahravka.mp3 --beam 10 --best-of 10 --no-vad --no-batched
```
Nejčastější:
- `--config` (jiný config soubor)
- `--model`, `--lang`, `--beam`, `--best-of`, `--patience`
- `--vad` / `--no-vad`
- `--batched` / `--no-batched`

---

## ⚡ Zprovoznění na NVIDIA GPU

Projekt je nastavený tak, aby se v prostředí `uv` nainstaloval **CUDA-enabled PyTorch** (viz `pyproject.toml` → `tool.uv.index` a mapování `torch` na `pytorch-cu124`). V praxi to znamená:

1. `uv sync`
2. spusťte přepis
3. ověřte, že v logu vidíte:
   - `[DEVICE] Používám NVIDIA GPU (CUDA).`

Pokud vidíte `[DEVICE] Používám CPU (přepínám na int8).`:
- Zkontrolujte, že máte aktuální NVIDIA driver.
- Ověřte, že se nainstaloval CUDA torch build (v `uv` prostředí).
- Pokud jste měnili závislosti, udělejte znovu `uv sync`.

---

## ⚙️ Konfigurace (config.json)

### Základní nastavení

| Klíč | Hodnoty | Popis |
| :--- | :--- | :--- |
| `model_size` | `tiny`, `base`, `small`, `medium`, `large-v3`, `turbo` | Velikost modelu. `large-v3` je nejpřesnější, `medium` je zlatý střed, `turbo` je nejrychlejší. |
| `device` | `auto`, `cuda`, `cpu` | `auto` se pokusí najít GPU samo. |
| `language` | `cs`, `en`, `sk`, ... | Jazyk přepisu (ISO 639-1 kód). |
| `output_formats` | `["txt", "srt", "vtt", "json"]` | Jaké soubory se mají vygenerovat. |
| `output_dir` | např. `"transcriptions"` | Kam se ukládají výstupy. |

### Výkonnostní nastavení (⚡ DŮLEŽITÉ pro rychlost!)

| Klíč | Hodnoty | Popis |
| :--- | :--- | :--- |
| `use_batched_inference` | `true` / `false` | **Zapněte pro 4-8x rychlejší zpracování!** Doporučeno: `true` |
| `batch_size` | `8-32` | Počet paralelních chunk. Vyšší = rychlejší, ale více paměti. Doporučeno: `16` |
| `beam_size` | `1-10` | Vyšší = kvalitnější, ale pomalejší. Doporučeno: `5` |

### Kvalita přepisu

| Klíč | Hodnoty | Popis |
| :--- | :--- | :--- |
| `word_timestamps` | `true` / `false` | Časové značky pro každé slovo (užitečné pro karaoke, analýzu). |
| `initial_prompt` | text | Vlastní jména, terminologie pro zlepšení přesnosti. Např: `"Ahoj, jmenuji se Jan Novák a pracuji v IT."` |
| `temperature` | `[0.0, 0.2, ...]` | Automatický fallback při špatné kvalitě. Default: `[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]` |
| `vad_filter` | `true` / `false` | Filtrování ticha (doporučeno: `true`). |
| `repetition_penalty` | `1.0-1.5` | Proti opakování textu. `1.0` = vypnuto, `1.2` = mírné potlačení. |

### Pokročilé parametry

| Klíč | Význam |
| :--- | :--- |
| `compression_ratio_threshold` | Detekce špatně přepsaných segmentů (default: `2.4`) |
| `log_prob_threshold` | Práh pravděpodobnosti pro zamítnutí segmentu (default: `-1.0`) |
| `no_speech_threshold` | Práh pro detekci "žádná řeč" (default: `0.6`) |
| `condition_on_previous_text` | Kontext z předchozích segmentů (default: `true`) |

---

## 📂 Struktura složek

```
local-whisper/
├── transcribe.py          # Hlavní přepisový skript
├── benchmark.py           # Performance testing
├── config.json            # Vaše konfigurace
├── config.examples.json   # Hotové příklady
├── pyproject.toml         # Python dependencies (uv)
├── README.md              # Tato dokumentace
├── CODE_REVIEW.md         # Technické detaily
├── CHANGELOG.md           # Historie změn
├── LICENSE                # MIT License
├── models/                # AI modely (auto-download)
└── transcriptions/        # Výstupní přepisy
```

Pozn.: konkrétní výstupní složka se řídí `output_dir` v configu (např. `transcriptions/` nebo `transcriptions/result/`).

---

## 🎬 Podporované vstupy (`.m4a/.mp4/...`)

Skript umí přepsat běžné audio soubory (`.mp3`, `.wav`) a také vybrané kontejnery/video formáty.

- Pokud je vstup např. `.m4a/.mp4/.mov/.mkv/.webm/.aac/.m4b`, skript ho automaticky převede do **dočasného WAV** (16 kHz, mono) přes `ffmpeg`.
- `ffmpeg` se vezme ze systému, pokud je k dispozici; jinak se použije **zabalený ffmpeg** z Python balíčku `imageio-ffmpeg` (může se stáhnout při prvním použití).

Příklad (Windows cesta s diakritikou):
```powershell
uv run transcribe.py --config config.hq.json "C:\Users\<USER>\Downloads\recording_part_3.m4a"
```

---

## 🆕 Hlavní funkce

✅ **BatchedInferencePipeline** - Až 8x rychlejší zpracování  
✅ **Word-level timestamps** - Pro karaoke a detailní analýzu  
✅ **Initial prompt** - Zlepšení přesnosti pro vlastní jména a terminologii  
✅ **Temperature fallback** - Automatická oprava při špatném zvuku  
✅ **Repetition control** - Prevence opakování textu  
✅ **Multi-file support** - Zpracování více souborů najednou  
✅ **Progress bar** - Vizuální zpětná vazba při dlouhých přepisech  
✅ **Smart error handling** - Detailní chybové hlášky s tipy na řešení

---

## 💡 Tipy pro maximální výkon

### Pro RTX 4070:
```json
{
  "model_size": "large-v3",
  "use_batched_inference": true,
  "batch_size": 24,
  "compute_type": "float16"
}
```

### Pro CPU (když GPU není k dispozici):
```json
{
  "model_size": "medium",
  "use_batched_inference": false,
  "compute_type": "int8"
}
```

### Pro nejlepší kvalitu (pomalejší):
```json
{
  "model_size": "large-v3",
  "beam_size": 10,
  "word_timestamps": true,
  "initial_prompt": "Text s vlastními jmény, která se vyskytují v nahrávce..."
}
```

---

## 🐛 Troubleshooting

### "Používám CPU" i když mám NVIDIA kartu
➡️ Viz sekce "Zprovoznění na NVIDIA GPU" výše.

### "Out of memory" chyba
➡️ Snižte `batch_size` v config.json (např. z 24 na 16 nebo 8).

### Špatná kvalita přepisu
➡️ 1. Zvyšte `beam_size` na 8-10  
➡️ 2. Použijte `initial_prompt` s kontextem  
➡️ 3. Zkontrolujte, zda máte správný `language` nastavený

### Přepis obsahuje opakující se text
➡️ Nastavte `repetition_penalty: 1.2` a `no_repeat_ngram_size: 3`

---

## 📖 Další dokumentace

- **[CODE_REVIEW.md](CODE_REVIEW.md)** - Technická analýza a best practices
- **[CHANGELOG.md](CHANGELOG.md)** - Historie změn a release notes
- **[config.examples.json](config.examples.json)** - Hotové příklady konfigurací
- **[benchmark.py](benchmark.py)** - Performance testing nástroj

---

## 📄 Licence

Tento projekt je licencován pod [MIT License](LICENSE).

---

## 🙏 Poděkování

- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Optimalizovaný Whisper engine
- [OpenAI Whisper](https://github.com/openai/whisper) - Původní AI model
- [CTranslate2](https://github.com/OpenNMT/CTranslate2) - Rychlá inference knihovna

---

## ⭐ Podpořte projekt

Pokud se vám projekt líbí, dejte mu hvězdičku na GitHubu! ⭐

---

<div align="center">
Made with ❤️ for lokální, soukromé a rychlé přepisy řeči
</div>
