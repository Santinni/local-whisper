"""
🚀 Performance Benchmark Script

Porovnání rychlosti různých konfigurací faster-whisper.
Použití: uv run benchmark.py <audio_file>
"""

import sys
import time
import json
from faster_whisper import WhisperModel, BatchedInferencePipeline

def benchmark_config(audio_path, config_name, model_size, use_batched, batch_size, beam_size):
    """Benchmarkuje jednu konfiguraci"""
    print(f"\n{'='*60}")
    print(f"🔬 Test: {config_name}")
    print(f"{'='*60}")
    
    try:
        # Načtení modelu
        print(f"⏳ Načítám model '{model_size}'...")
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        
        # Přepis
        start_time = time.time()
        
        if use_batched:
            print(f"📦 Batched inference (batch_size={batch_size})")
            batched_model = BatchedInferencePipeline(model=model)
            segments, info = batched_model.transcribe(
                audio_path,
                batch_size=batch_size,
                beam_size=beam_size,
                vad_filter=True
            )
        else:
            print(f"📝 Sequential inference")
            segments, info = model.transcribe(
                audio_path,
                beam_size=beam_size,
                vad_filter=True
            )
        
        # Konzumace generátoru
        segment_count = sum(1 for _ in segments)
        
        # Výpočet metrik
        elapsed = time.time() - start_time
        audio_duration = info.duration
        rtf = audio_duration / elapsed  # Real-Time Factor
        
        print(f"\n✅ VÝSLEDKY:")
        print(f"   Audio délka: {audio_duration:.2f}s")
        print(f"   Čas zpracování: {elapsed:.2f}s")
        print(f"   RTF: {rtf:.2f}x (vyšší = rychlejší)")
        print(f"   Segmentů: {segment_count}")
        print(f"   Jazyk: {info.language} ({info.language_probability:.1%})")
        
        return {
            "config": config_name,
            "audio_duration": audio_duration,
            "processing_time": elapsed,
            "rtf": rtf,
            "segments": segment_count
        }
        
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Použití: uv run benchmark.py <audio_file>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🎯 FASTER-WHISPER PERFORMANCE BENCHMARK                    ║
╚══════════════════════════════════════════════════════════════╝

Audio soubor: {audio_path}

Tento test porovná různé konfigurace a ukáže, která je
nejrychlejší pro váš hardware.
""")
    
    results = []
    
    # Test 1: Medium + Batched (doporučená konfigurace)
    results.append(benchmark_config(
        audio_path,
        "Medium + Batched (DOPORUČENO)",
        "medium",
        use_batched=True,
        batch_size=16,
        beam_size=5
    ))
    
    # Test 2: Medium bez Batched
    results.append(benchmark_config(
        audio_path,
        "Medium bez Batched",
        "medium",
        use_batched=False,
        batch_size=None,
        beam_size=5
    ))
    
    # Test 3: Small + Agresivní batching
    results.append(benchmark_config(
        audio_path,
        "Small + Velký Batch (RYCHLOST)",
        "small",
        use_batched=True,
        batch_size=32,
        beam_size=3
    ))
    
    # Vyhodnocení
    print(f"\n\n{'='*60}")
    print("📊 SOUHRNNÉ VÝSLEDKY")
    print(f"{'='*60}\n")
    
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        print("❌ Žádné úspěšné testy")
        return
    
    # Seřazení podle RTF (nejvyšší = nejrychlejší)
    valid_results.sort(key=lambda x: x["rtf"], reverse=True)
    
    print(f"{'Konfigurace':<35} {'RTF':>8} {'Čas':>10}")
    print("-" * 60)
    for r in valid_results:
        print(f"{r['config']:<35} {r['rtf']:>7.2f}x {r['processing_time']:>9.2f}s")
    
    print("\n🏆 VÍTĚZ:")
    winner = valid_results[0]
    print(f"   {winner['config']}")
    print(f"   Rychlost: {winner['rtf']:.2f}x real-time")
    
    # Uložení výsledků
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(valid_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Detailní výsledky uloženy do: benchmark_results.json")

if __name__ == "__main__":
    main()
