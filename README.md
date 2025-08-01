# 🔍 Cerca

**Cerca** is a fast Python tool for searching strings within files, with parallel search support and text editor integration.

> 🇮🇹 [Versione italiana](README.it.md)

## ✨ Features

- 🚀 **Parallel search** - Uses multiple threads to search simultaneously across many files
- 🎯 **Case-sensitive or insensitive search** - Choose your search mode
- 📁 **Extension filtering** - Search only in file types you care about
- 🚫 **Automatic exclusion** - Ignores binary files and system folders (.git, node_modules, etc.)
- 📝 **Show context** - Display lines where the searched text appears
- 🔄 **Replacement preview** - Preview changes without modifying files
- 📊 **Detailed statistics** - Number of occurrences per file and file sizes
- 🎛️ **Interactive filtering** - Exclude extensions after the search
- ⚡ **UEEdit64 integration** - Automatically opens found files in the editor

## 📦 Installation

```bash
git clone https://github.com/8emezzo/cerca.git
cd cerca
```

Make sure you have Python 3.6+ installed.

## 🚀 Usage

### Basic search
```bash
python cerca.py "TODO"
```

### Case-insensitive search
```bash
python cerca.py "todo" -i
```

### Search only in Python files
```bash
python cerca.py "import pandas" -e .py
```

### Show occurrence context
```bash
python cerca.py "error" -c
```

### Replacement preview
```bash
python cerca.py "bug" -r "fix"
```

### Show results only (don't open editor)
```bash
python cerca.py "search_term" -n
```

## 🎯 Options

| Option | Description |
|--------|-------------|
| `-i, --ignore-case` | Case-insensitive search |
| `-e, --extensions` | File extensions to include (e.g.: .py .txt) |
| `-n, --no-open` | Don't open files, show results only |
| `-l, --limit` | Limit the number of files to open |
| `-c, --context` | Show occurrence context |
| `-r, --replace` | Show replacement preview (doesn't modify files) |
| `--include-binary` | Include binary files in search |
| `-w, --workers` | Number of parallel threads (default: 8) |
| `--editor` | Specify the editor to use (default: uedit64 or EDITOR env var) |

## 🔧 Configuration

The program automatically excludes:

**Directories**: `.git`, `.svn`, `__pycache__`, `node_modules`, `.venv`, `venv`, `env`, `.idea`, `.vscode`, `build`, `dist`

**Binary files**: `.exe`, `.dll`, `.so`, `.pdf`, `.jpg`, `.png`, `.zip`, `.mp3`, `.mp4`, etc.

## 💡 Usage Examples

### Find all TODOs in code
```bash
python cerca.py "TODO" -e .py .js .java -c
```

### Search for errors in logs
```bash
python cerca.py "ERROR" -i -e .log -c
```

### Check unused imports
```bash
python cerca.py "import" -e .py -n
```

### Search and prepare a replacement
```bash
python cerca.py "old_function" -r "new_function" -e .py
```

### Use different editors
```bash
# Use VS Code
python cerca.py "TODO" --editor code

# Use Vim
python cerca.py "TODO" --editor vim

# Set default editor via environment variable
export EDITOR=nano
python cerca.py "TODO"
```

## ⚙️ Advanced Features

### Interactive extension filtering
After the initial search, the program shows a summary of found extensions and allows you to exclude some interactively.

### Parallel search
Uses a thread pool (default: 8) to search simultaneously in multiple files, significantly improving performance on large projects.

### Editor integration
The program can automatically open found files in your preferred editor. By default, it uses:
1. The editor specified with `--editor` option
2. The `EDITOR` environment variable (if set)
3. `uedit64` as fallback

You can limit the number of opened files with the `-l` option.

## 📝 Notes

- Search uses regular expressions with automatic pattern escaping
- Files are sorted by number of occurrences (descending)
- Context shows up to 3 occurrences per file
- Long lines are truncated for better readability

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## 📄 License

This project is distributed under the MIT License.