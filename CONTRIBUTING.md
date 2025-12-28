# Contributing to Local Whisper Transcriber

Děkujeme za váš zájem přispět do projektu! 🎉

## 🐛 Hlášení chyb

Pokud najdete chybu, vytvořte [nový issue](../../issues/new) s těmito informacemi:

- **Popis problému**: Co se pokazilo?
- **Kroky k reprodukci**: Jak chybu vyvolat?
- **Očekávané chování**: Co by se mělo stát?
- **Prostředí**:
  - OS (Windows/Linux/macOS)
  - Python verze
  - GPU/CPU
  - Model size
  - Relevantní část config.json

## 💡 Návrhy na vylepšení

Máte nápad na novou funkci? Skvělé!

1. Zkontrolujte [existující issues](../../issues), zda už někdo podobný nápad neměl
2. Vytvořte nový issue s popisem:
   - **Use case**: K čemu by funkce sloužila?
   - **Návrh řešení**: Jak by to mohlo fungovat?
   - **Alternativy**: Zvažovali jste jiné přístupy?

## 🔧 Pull Requests

### Než začnete

1. **Forkněte** repozitář
2. **Vytvořte branch** pro vaši změnu: `git checkout -b feature/vase-vylepseni`
3. **Diskutujte** větší změny nejdřív v issue

### Coding Standards

- **Python**: Dodržujte PEP 8
- **Komentáře**: Důležitý kód komentujte česky
- **Docstringy**: Pro funkce používejte Google style
- **Formátování**: Použijte `black` a `isort`

```bash
pip install black isort
black .
isort .
```

### Testování

Před odesláním PR:

1. Otestujte na reálných audio souborech
2. Zkontrolujte různé konfigurace (config.examples.json)
3. Ověřte, že nerozbíjíte existující funkce

### Commit Messages

Používejte jasné commit zprávy:

```
feat: Přidána podpora pro formát FLAC
fix: Opravena chyba v word timestamps exportu
docs: Aktualizace README s novými příklady
perf: Optimalizace batch processingu
```

### Pull Request Process

1. **Aktualizujte dokumentaci** (README.md, CODE_REVIEW.md)
2. **Přidejte záznam do CHANGELOG.md**
3. **Popište změny** v PR description:
   - Co jste změnili a proč?
   - Jak to otestovat?
   - Screenshoty/výstupy (pokud relevantní)

## 📝 Dokumentace

Při přidávání nových funkcí:

- Aktualizujte README.md
- Přidejte příklad do config.examples.json
- Updatujte CODE_REVIEW.md s technickými detaily

## 🎯 Priority projektu

Aktuálně hledáme příspěvky v těchto oblastech:

- 🧪 Testy a benchmarky
- 📚 Překklady dokumentace (EN)
- 🐧 Testování na Linuxu/macOS
- 🎨 GUI wrapper (optional)
- 🔊 Real-time transcription
- 📦 Docker kontejner

## 💬 Komunikace

- **Issues**: Pro bugy a feature requests
- **Discussions**: Pro obecné otázky a diskuze
- **Pull Requests**: Pro konkrétní změny kódu

## 📜 Code of Conduct

- Buďte přátelští a respektující
- Konstruktivní kritika je vítána
- Netolerujeme urážky nebo diskriminaci

## 🙏 Děkujeme!

Každý příspěvek je důležitý, ať už je to:
- 🐛 Bug report
- 💡 Feature návrh
- 📝 Dokumentace
- 💻 Kód
- ⭐ Hvězdička na GitHubu!

Těšíme se na vaši spolupráci! 🚀
