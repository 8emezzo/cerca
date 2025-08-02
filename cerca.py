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

# Common binary files to exclude
BINARY_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib', '.pdf', '.jpg', '.jpeg', 
                    '.png', '.gif', '.ico', '.zip', '.rar', '.7z', '.tar', 
                    '.gz', '.bz2', '.mp3', '.mp4', '.avi', '.mov', '.mkv',
                    '.pyc', '.pyo', '.class', '.o', '.obj', '.lib'}

# Directories to exclude
EXCLUDE_DIRS = {'.git', '.svn', '__pycache__', 'node_modules', '.venv', 
                'venv', 'env', '.idea', '.vscode', 'build', 'dist'}

def is_binary_file(filepath):
    """Check if a file is binary."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except:
        return True

def search_in_file(filepath, pattern, case_sensitive, show_context=False):
    """Search in a single file and return detailed results."""
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
    """Search pattern in parallel."""
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
            print(f"\rAnalyzed {completed}/{total} files...", end='', flush=True)
            
            result = future.result()
            if result:
                results[result['path']] = result
    
    print("\r" + " " * 50 + "\r", end='')
    return results

def format_size(size):
    """Format file size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def print_results(results, args, header="Files found:"):
    """Print results."""
    sorted_results = sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"\n{header}\n")
    total_occurrences = 0
    
    for i, (filepath, data) in enumerate(sorted_results, 1):
        count = data['count']
        total_occurrences += count
        
        try:
            file_size = format_size(Path(filepath).stat().st_size)
            print(f"{i:3d}. {filepath} ({count} occurrence{'s' if count != 1 else ''}, {file_size})")
        except:
            print(f"{i:3d}. {filepath} ({count} occurrence{'s' if count != 1 else ''})")
        
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
                    print(f"     Line {line_num}: {highlighted}")
                else:
                    print(f"     Line {line_num}: {line_content}")
            print()
    
    return sorted_results, total_occurrences

def filter_by_extensions(results):
    """Allows filtering results by extension."""
    # Count extensions
    ext_counter = Counter()
    for data in results.values():
        ext = data.get('extension', '')
        if not ext:
            ext = '(no extension)'
        ext_counter[ext] += 1
    
    if len(ext_counter) <= 1:
        return results
    
    # Show extensions summary
    print("\nExtensions summary:")
    sorted_exts = sorted(ext_counter.items(), key=lambda x: x[1], reverse=True)
    for i, (ext, count) in enumerate(sorted_exts, 1):
        print(f"  {i:2d}. {ext:15s} {count:4d} file")
    
    # Ask if they want to exclude
    risposta = input("\nDo you want to exclude any extension? (Y/N) [Enter=N]: ").strip().upper()
    if risposta != 'Y':
        return results
    
    # Ask which ones to exclude
    print("\nEnter the numbers of extensions to EXCLUDE separated by spaces")
    print("(e.g.: '1 3 5' to exclude the 1st, 3rd and 5th extension)")
    scelta = input("Numbers to exclude (enter for none): ").strip()
    
    if not scelta:
        return results
    
    try:
        # Parse numbers
        numeri = [int(n) for n in scelta.split()]
        escludi_ext = set()
        
        for num in numeri:
            if 1 <= num <= len(sorted_exts):
                ext = sorted_exts[num-1][0]
                escludi_ext.add(ext)
        
        if escludi_ext:
            print(f"\nExcluding: {', '.join(escludi_ext)}")
            # Filter results
            filtered_results = {}
            for path, data in results.items():
                ext = data.get('extension', '') or '(no extension)'
                if ext not in escludi_ext:
                    filtered_results[path] = data
            return filtered_results
            
    except ValueError:
        print("Invalid input, no filter applied")
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description='Search strings in files and open with specified editor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
ESEMPI:
  cerca.py "TODO"                   Search "TODO" (case-sensitive)
  cerca.py "todo" -i                Search "todo" ignoring case
  cerca.py "import pandas" -e .py   Search only in Python files
  cerca.py "error" -c               Show context of occurrences
  cerca.py "bug" -r "fix"           Replace "bug" with "fix" (preview)
  cerca.py "TODO" --editor code     Open files with VS Code
        ''')
    
    parser.add_argument('pattern', help='String to search')
    parser.add_argument('-i', '--ignore-case', action='store_true', 
                       help='Case-insensitive search')
    parser.add_argument('-e', '--extensions', nargs='+', 
                       help='File extensions to include (e.g.: .py .txt)')
    parser.add_argument('-n', '--no-open', action='store_true',
                       help='Don\'t open files, only show results')
    parser.add_argument('-l', '--limit', type=int, default=0,
                       help='Limit the number of files to open')
    parser.add_argument('-c', '--context', action='store_true',
                       help='Show context of occurrences')
    parser.add_argument('-r', '--replace', type=str,
                       help='Show replacement preview (doesn\'t modify files)')
    parser.add_argument('--include-binary', action='store_true',
                       help='Include binary files in search')
    parser.add_argument('-w', '--workers', type=int, default=8,
                       help='Number of parallel threads (default: 8)')
    parser.add_argument('--editor', type=str, default=None,
                       help='Editor to use for opening files (default: uedit64 or EDITOR env var)')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    print(f"\n{'Case-insensitive' if args.ignore_case else 'Case-sensitive'} search for '{args.pattern}' in progress...")
    print(f"Directory: {Path.cwd().absolute()}")
    
    if args.extensions:
        print(f"Filtering by extensions: {', '.join(args.extensions)}")
    
    print()
    
    # Search files
    results = search_files_parallel(
        args.pattern, 
        not args.ignore_case, 
        args.extensions,
        not args.include_binary,
        args.context or args.replace,
        args.workers
    )
    
    if not results:
        print(f"No files found containing '{args.pattern}'")
        return
    
    # First print ALL results
    sorted_results, total_occurrences = print_results(results, args)
    
    elapsed = time.time() - start_time
    print(f"\nFound {len(results)} files with {total_occurrences} total occurrences in {elapsed:.2f} seconds")
    
    # Then offer to filter by extensions
    filtered_results = filter_by_extensions(results)
    
    # If filtered, reprint results
    if len(filtered_results) < len(results):
        sorted_results, total_occurrences = print_results(filtered_results, args, 
                                                         "Files found after filtering:")
        print(f"\n{len(filtered_results)} files remaining with {total_occurrences} occurrences after filtering")
    
    if args.no_open:
        return
    
    # Determine which editor to use
    editor = args.editor
    if not editor:
        # Try to get from EDITOR environment variable
        editor = os.environ.get('EDITOR', 'uedit64')
    
    # Ask for confirmation to open (use filtered results)
    risposta = input(f"\nDo you want to open all files with {editor}? (Y/N) [Enter=Y]: ").strip().upper()

    
    if risposta in ['Y', '']:  # Accept both 'Y' and empty enter
        files_to_open = sorted_results
        if args.limit > 0:
            files_to_open = files_to_open[:args.limit]
            print(f"\nOpening the first {args.limit} files...")
        
        for filepath, _ in files_to_open:
            try:
                subprocess.Popen([editor, filepath], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print(f"Error: {editor} not found in PATH")
                break
    else:
        print("Operation cancelled")

if __name__ == "__main__":
    main()