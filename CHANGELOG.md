# 📝 CHANGELOG

## v0.1.0-beta (2024-12-28) - První beta vydání

### 🚀 Hlavní funkce
- ✅ **BatchedInferencePipeline**: Až 8x rychlejší zpracování pomocí paralelního batch processingu
- ✅ **GPU/CPU Auto-detekce**: Automatické přepnutí mezi CUDA a CPU
- ✅ **Word-level timestamps**: Časové značky pro každé slovo (užitečné pro karaoke, analýzu)
- ✅ **Initial prompt support**: Zlepšení přesnosti pomocí kontextu (vlastní jména, terminologie)
- ✅ **Temperature fallback**: Automatické opakování s různými teplotami při špatné kvalitě
- ✅ **Multi-file support**: Zpracování více audio souborů v jednom příkazu
- ✅ **Progress monitoring**: Progress bar (tqdm) pro dlouhé přepisy
- ✅ **Repetition control**: Prevence opakování textu pomocí penalties
- ✅ **VAD filtrování**: Automatická detekce a odstranění ticha

### 📂 Výstupní formáty
- TXT - Prostý text s časovými značkami
- SRT - Standardní titulky pro video
- VTT - Web titulky
- JSON - Kompletní metadata včetně word timestamps

### ⚙️ Konfigurace
Všechny parametry nastavitelné v `config.json`:
```json
{
  "model_size": "tiny|base|small|medium|large-v3|turbo",
  "use_batched_inference": true,
  "batch_size": 16,
  "word_timestamps": false,
  "initial_prompt": "",
  "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
  "repetition_penalty": 1.0,
  "vad_filter": true
}
```

### 📚 Dokumentace
- README.md - Kompletní návod k použití
- CODE_REVIEW.md - Technická dokumentace a best practices
- config.examples.json - Hotové příklady konfigurací
- benchmark.py - Performance testing tool

### 🎯 Optimalizace pro hardware
- RTX 30xx/40xx: Optimalizováno pro NVIDIA GPU s float16
- CPU fallback: Automatický přepis na int8 při CPU režimu
- Podpora pro multi-GPU setup

### 🛠️ Technické detaily
- Engine: faster-whisper (CTranslate2)
- Python: 3.12+
- Package manager: uv
- Modely: OpenAI Whisper (tiny, base, small, medium, large-v3, turbo, distil varianty)

