#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# File binari comuni da escludere
BINARY_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib', '.pdf', '.jpg', '.jpeg', 
                    '.png', '.gif', '.ico', '.zip', '.rar', '.7z', '.tar', 
                    '.gz', '.bz2', '.mp3', '.mp4', '.avi', '.mov', '.mkv',
                    '.pyc', '.pyo', '.class', '.o', '.obj', '.lib'}

# Directory da escludere
EXCLUDE_DIRS = {'.git', '.svn', '__pycache__', 'node_modules', '.venv', 
                'venv', 'env', '.idea', '.vscode', 'build', 'dist'}

def is_binary_file(filepath):
    """Controlla se un file è binario."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except:
        return True

def search_in_file(filepath, pattern, case_sensitive, show_context=False):
    """Cerca in un singolo file e ritorna risultati dettagliati."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if case_sensitive:
            matches = list(re.finditer(re.escape(pattern), content))
        else:
            matches = list(re.finditer(re.escape(pattern), content, re.IGNORECASE))
        
        if not matches:
            return None
            
        contexts = []
        if show_context:
            lines = content.splitlines()
            for match in matches[:3]:
                line_start = content.rfind('\n', 0, match.start()) + 1
                line_end = content.find('\n', match.end())
                line_num = content[:line_start].count('\n') + 1
                
                if line_end == -1:
                    line_end = len(content)
                    
                line_content = content[line_start:line_end].strip()
                if len(line_content) > 80:
                    rel_pos = match.start() - line_start
                    start = max(0, rel_pos - 30)
                    end = min(len(line_content), rel_pos + 50)
                    line_content = "..." + line_content[start:end] + "..."
                    
                contexts.append((line_num, line_content))
        
        return {
            'path': str(filepath.absolute()),
            'count': len(matches),
            'contexts': contexts,
            'extension': filepath.suffix.lower()
        }
    except:
        return None

def search_files_parallel(pattern, case_sensitive=True, extensions=None, 
                         exclude_binary=True, show_context=False, max_workers=8):
    """Cerca pattern in parallelo."""
    files_to_search = []
    current_dir = Path.cwd()
    
    for root, dirs, files in os.walk(current_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        root_path = Path(root)
        for file in files:
            filepath = root_path / file
            
            if extensions and filepath.suffix.lower() not in extensions:
                continue
                
            if exclude_binary and filepath.suffix.lower() in BINARY_EXTENSIONS:
                continue
                
            files_to_search.append(filepath)
    
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(search_in_file, filepath, pattern, case_sensitive, show_context): filepath
            for filepath in files_to_search
        }
        
        completed = 0
        total = len(files_to_search)
        
        for future in as_completed(future_to_file):
            completed += 1
            print(f"\rAnalizzati {completed}/{total} file...", end='', flush=True)
            
            result = future.result()
            if result:
                results[result['path']] = result
    
    print("\r" + " " * 50 + "\r", end='')
    return results

def format_size(size):
    """Formatta dimensione file."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def print_results(results, args, header="File trovati:"):
    """Stampa i risultati."""
    sorted_results = sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"\n{header}\n")
    total_occurrences = 0
    
    for i, (filepath, data) in enumerate(sorted_results, 1):
        count = data['count']
        total_occurrences += count
        
        try:
            file_size = format_size(Path(filepath).stat().st_size)
            print(f"{i:3d}. {filepath} ({count} occorrenz{'a' if count == 1 else 'e'}, {file_size})")
        except:
            print(f"{i:3d}. {filepath} ({count} occorrenz{'a' if count == 1 else 'e'})")
        
        if args.context and data['contexts']:
            for line_num, line_content in data['contexts']:
                if args.replace:
                    if args.ignore_case:
                        highlighted = re.sub(
                            re.escape(args.pattern),
                            f"[{args.pattern} → {args.replace}]",
                            line_content,
                            flags=re.IGNORECASE
                        )
                    else:
                        highlighted = line_content.replace(args.pattern, f"[{args.pattern} → {args.replace}]")
                    print(f"     Riga {line_num}: {highlighted}")
                else:
                    print(f"     Riga {line_num}: {line_content}")
            print()
    
    return sorted_results, total_occurrences

def filter_by_extensions(results):
    """Permette di filtrare i risultati per estensione."""
    # Conta le estensioni
    ext_counter = Counter()
    for data in results.values():
        ext = data.get('extension', '')
        if not ext:
            ext = '(senza estensione)'
        ext_counter[ext] += 1
    
    if len(ext_counter) <= 1:
        return results
    
    # Mostra riepilogo estensioni
    print("\nRiepilogo estensioni trovate:")
    sorted_exts = sorted(ext_counter.items(), key=lambda x: x[1], reverse=True)
    for i, (ext, count) in enumerate(sorted_exts, 1):
        print(f"  {i:2d}. {ext:15s} {count:4d} file")
    
    # Chiedi se vuole escludere
    risposta = input("\nVuoi escludere qualche estensione? (S/N) [Entrer=N]: ").strip().upper()
    if risposta != 'S':
        return results
    
    # Chiedi quali escludere
    print("\nInserisci i numeri delle estensioni da ESCLUDERE separati da spazi")
    print("(es: '1 3 5' per escludere la 1°, 3° e 5° estensione)")
    scelta = input("Numeri da escludere (invio per nessuna): ").strip()
    
    if not scelta:
        return results
    
    try:
        # Parse numeri
        numeri = [int(n) for n in scelta.split()]
        escludi_ext = set()
        
        for num in numeri:
            if 1 <= num <= len(sorted_exts):
                ext = sorted_exts[num-1][0]
                escludi_ext.add(ext)
        
        if escludi_ext:
            print(f"\nEscludendo: {', '.join(escludi_ext)}")
            # Filtra risultati
            filtered_results = {}
            for path, data in results.items():
                ext = data.get('extension', '') or '(senza estensione)'
                if ext not in escludi_ext:
                    filtered_results[path] = data
            return filtered_results
            
    except ValueError:
        print("Input non valido, nessun filtro applicato")
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description='Cerca stringhe nei file e apre con l\'editor specificato',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
ESEMPI:
  cerca.py "TODO"                   Cerca "TODO" (case-sensitive)
  cerca.py "todo" -i                Cerca "todo" ignorando maiuscole/minuscole
  cerca.py "import pandas" -e .py   Cerca solo in file Python
  cerca.py "error" -c               Mostra contesto delle occorrenze
  cerca.py "bug" -r "fix"           Sostituisci "bug" con "fix" (preview)
  cerca.py "TODO" --editor code     Apre i file con VS Code
        ''')
    
    parser.add_argument('pattern', help='Stringa da cercare')
    parser.add_argument('-i', '--ignore-case', action='store_true', 
                       help='Ricerca case-insensitive')
    parser.add_argument('-e', '--extensions', nargs='+', 
                       help='Estensioni file da includere (es: .py .txt)')
    parser.add_argument('-n', '--no-open', action='store_true',
                       help='Non aprire i file, mostra solo i risultati')
    parser.add_argument('-l', '--limit', type=int, default=0,
                       help='Limita il numero di file da aprire')
    parser.add_argument('-c', '--context', action='store_true',
                       help='Mostra il contesto delle occorrenze')
    parser.add_argument('-r', '--replace', type=str,
                       help='Mostra preview di sostituzione (non modifica i file)')
    parser.add_argument('--include-binary', action='store_true',
                       help='Includi file binari nella ricerca')
    parser.add_argument('-w', '--workers', type=int, default=8,
                       help='Numero di thread paralleli (default: 8)')
    parser.add_argument('--editor', type=str, default=None,
                       help='Editor da usare per aprire i file (default: uedit64 o EDITOR env var)')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    print(f"\nRicerca {'case-insensitive' if args.ignore_case else 'case-sensitive'} di '{args.pattern}' in corso...")
    print(f"Directory: {Path.cwd().absolute()}")
    
    if args.extensions:
        print(f"Filtrando per estensioni: {', '.join(args.extensions)}")
    
    print()
    
    # Cerca i file
    results = search_files_parallel(
        args.pattern, 
        not args.ignore_case, 
        args.extensions,
        not args.include_binary,
        args.context or args.replace,
        args.workers
    )
    
    if not results:
        print(f"Nessun file trovato contenente '{args.pattern}'")
        return
    
    # Prima stampa TUTTI i risultati
    sorted_results, total_occurrences = print_results(results, args)
    
    elapsed = time.time() - start_time
    print(f"\nTrovati {len(results)} file con {total_occurrences} occorrenze totali in {elapsed:.2f} secondi")
    
    # Poi offri di filtrare per estensioni
    filtered_results = filter_by_extensions(results)
    
    # Se sono stati filtrati, ristampa i risultati
    if len(filtered_results) < len(results):
        sorted_results, total_occurrences = print_results(filtered_results, args, 
                                                         "File trovati dopo il filtro:")
        print(f"\nRimasti {len(filtered_results)} file con {total_occurrences} occorrenze dopo il filtro")
    
    if args.no_open:
        return
    
    # Determina quale editor usare
    editor = args.editor
    if not editor:
        # Prova a prendere dalla variabile d'ambiente EDITOR
        editor = os.environ.get('EDITOR', 'uedit64')
    
    # Chiedi conferma apertura (usa i risultati filtrati)
    risposta = input(f"\nVuoi aprire tutti i file con {editor}? (S/N) [Enter=S]: ").strip().upper()

    
    if risposta in ['S', '']:  # Accetta sia 'S' che invio vuoto
        files_to_open = sorted_results
        if args.limit > 0:
            files_to_open = files_to_open[:args.limit]
            print(f"\nApertura dei primi {args.limit} file...")
        
        for filepath, _ in files_to_open:
            try:
                subprocess.Popen([editor, filepath], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print(f"Errore: {editor} non trovato nel PATH")
                break
    else:
        print("Operazione annullata")

if __name__ == "__main__":
    main()