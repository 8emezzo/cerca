# 🔍 Cerca

**Cerca** è uno strumento Python per la ricerca veloce di stringhe all'interno di file, con supporto per ricerca parallela e integrazione con editor di testo. Effettua una ricerca ricorsiva in tutti i file e sottocartelle a partire dalla directory corrente.

## ✨ Caratteristiche

- 🔍 **Ricerca ricorsiva** - Cerca in tutti i file e sottocartelle dalla directory di lavoro corrente
- 🚀 **Ricerca parallela** - Utilizza più thread per cercare simultaneamente in molti file
- 🎯 **Ricerca case-sensitive o insensitive** - Scegli come cercare
- 📁 **Filtro per estensioni** - Cerca solo nei tipi di file che ti interessano
- 🚫 **Esclusione automatica** - Ignora file binari e cartelle di sistema (.git, node_modules, ecc.)
- 📝 **Mostra contesto** - Visualizza le righe dove appare il testo cercato
- 🔄 **Preview sostituzioni** - Anteprima delle modifiche senza modificare i file
- 📊 **Statistiche dettagliate** - Numero di occorrenze per file e dimensioni
- 🎛️ **Filtro interattivo** - Escludi estensioni dopo la ricerca
- ⚡ **Integrazione con editor** - Apre automaticamente i file trovati nel tuo editor preferito

## 📦 Installazione

```bash
git clone https://github.com/8emezzo/cerca.git
cd cerca
```

Assicurati di avere Python 3.6+ installato.

## 🚀 Utilizzo

### Ricerca base
```bash
python cerca.py "TODO"
# Cerca "TODO" in tutti i file e sottocartelle dalla directory corrente
```

### Ricerca case-insensitive
```bash
python cerca.py "todo" -i
```

### Cerca solo in file Python
```bash
python cerca.py "import pandas" -e .py
```

### Mostra il contesto delle occorrenze
```bash
python cerca.py "error" -c
```

### Preview di sostituzione
```bash
python cerca.py "bug" -r "fix"
```

### Solo mostra risultati (non aprire editor)
```bash
python cerca.py "search_term" -n
```

## 🎯 Opzioni

| Opzione | Descrizione |
|---------|-------------|
| `-i, --ignore-case` | Ricerca case-insensitive |
| `-e, --extensions` | Estensioni file da includere (es: .py .txt) |
| `-n, --no-open` | Non aprire i file, mostra solo i risultati |
| `-l, --limit` | Limita il numero di file da aprire |
| `-c, --context` | Mostra il contesto delle occorrenze |
| `-r, --replace` | Mostra preview di sostituzione (non modifica i file) |
| `--include-binary` | Includi file binari nella ricerca |
| `-w, --workers` | Numero di thread paralleli (default: 8) |
| `--editor` | Specifica l'editor da usare (default: uedit64 o variabile EDITOR) |

## 🔧 Configurazione

Il programma esclude automaticamente:

**Directory**: `.git`, `.svn`, `__pycache__`, `node_modules`, `.venv`, `venv`, `env`, `.idea`, `.vscode`, `build`, `dist`

**File binari**: `.exe`, `.dll`, `.so`, `.pdf`, `.jpg`, `.png`, `.zip`, `.mp3`, `.mp4`, ecc.

## 💡 Esempi d'uso

### Trovare tutti i TODO nel codice
```bash
python cerca.py "TODO" -e .py .js .java -c
```

### Cercare errori nei log
```bash
python cerca.py "ERROR" -i -e .log -c
```

### Verificare import non utilizzati
```bash
python cerca.py "import" -e .py -n
```

### Cercare e preparare una sostituzione
```bash
python cerca.py "vecchia_funzione" -r "nuova_funzione" -e .py
```

### Usare editor diversi
```bash
# Usa VS Code
python cerca.py "TODO" --editor code

# Usa Vim
python cerca.py "TODO" --editor vim

# Imposta editor di default tramite variabile d'ambiente
export EDITOR=nano
python cerca.py "TODO"
```

## ⚙️ Funzionalità avanzate

### Filtro interattivo per estensioni
Dopo la ricerca iniziale, il programma mostra un riepilogo delle estensioni trovate e permette di escluderne alcune interattivamente.

### Ricerca parallela
Utilizza un pool di thread (default: 8) per cercare simultaneamente in più file, migliorando notevolmente le prestazioni su progetti grandi.

### Integrazione con editor
Il programma può aprire automaticamente i file trovati nel tuo editor preferito. Di default, usa:
1. L'editor specificato con l'opzione `--editor`
2. La variabile d'ambiente `EDITOR` (se impostata)
3. `uedit64` come fallback

Puoi limitare il numero di file aperti con l'opzione `-l`.

## 📝 Note

- La ricerca utilizza espressioni regolari con escape automatico del pattern
- I file vengono ordinati per numero di occorrenze (decrescente)
- Il contesto mostra fino a 3 occorrenze per file
- Le righe lunghe vengono troncate per una migliore leggibilità

## 🤝 Contributi

I contributi sono benvenuti! Sentiti libero di aprire issue o pull request.

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT.