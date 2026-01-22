#!/bin/bash

set -e

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    echo "Unsupported OS"
    exit 1
fi

echo "🧠 Detected OS: $OS"
echo "🧹 Uninstalling Fleet CLI..."

# Remove all files recorded in /.boost_cli_env/install_records.txt
# xargs rm -rf < files.txt
file_list="$HOME/.boost_cli_env/install_records.txt"
if [[ -f "$file_list" ]]; then
    echo "🗑️ Removing installed files..."
    while IFS= read -r file; do
        if [[ -e "$file" ]]; then
            rm -rf "$file"
            echo "✅ Removed: $file"
        else
            echo "⚠️ File not found (already gone?): $file"
        fi
    done < "$file_list"
else
    echo "ℹ️ No install records found. Skipping file removal."
fi

# Remove virtual environment
if [[ -d "$HOME/.boost_cli_env" ]]; then
    echo "🐍 Removing virtual environment..."
    rm -rf "$HOME/.boost_cli_env"
else
    echo "ℹ️ Virtual environment not found. Skipping..."
fi

# Remove CLI wrapper script
if [[ -f "$HOME/.local/bin/boost" ]]; then
    echo "🔧 Removing Fleet CLI wrapper script..."
    rm "$HOME/.local/bin/boost"
else
    echo "ℹ️ Fleet CLI wrapper not found. Skipping..."
fi

# Remove autocomplete lines from shell configs
echo "🧽 Cleaning up shell autocomplete configs..."

# Remove from .bashrc
if [[ -f "$HOME/.bashrc" ]]; then
    sed -i.bak '/_BOOST_COMPLETE=bash_source boost/d' "$HOME/.bashrc"
    sed -i.bak '/export PATH=\$HOME\/.local\/bin:\$PATH/d' "$HOME/.bashrc"
    echo "✅ Cleaned .bashrc"
fi

# Remove from .zshrc
if [[ -f "$HOME/.zshrc" ]]; then
    sed -i.bak '/_BOOST_COMPLETE=zsh_source boost/d' "$HOME/.zshrc"
    sed -i.bak '/export PATH=\$HOME\/.local\/bin:\$PATH/d' "$HOME/.zshrc"
    echo "✅ Cleaned .zshrc"
fi

echo "🎉 Fleet CLI uninstalled successfully!"
echo "🔄 Please restart your shell or run 'source ~/.bashrc' or 'source ~/.zshrc' to finalize cleanup."