#!/bin/bash

set -e

# Determine OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
elif [[ "$OSTYPE" == "msys" ]]; then
    OS="windows"
elif [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    echo "Unsupported OS"
    exit 1
fi
echo "🖥️ Detected OS: $OS"
echo "🚀 Installing Fleet Status CLI..."

# Create virtual environment based on OS
if [[ "$OS" == "linux" || "$OS" == "macos" ]]; then
    echo "🐍 Setting up virtual environment for macOS/Linux..."
    python3 -m venv ~/.boost_cli_env
    source ~/.boost_cli_env/bin/activate
    echo "Installing boost status CLI using pip to virtual environment"
    cd python-cli
    pip install -e .

elif [[ "$OS" == "windows" ]]; then
    echo "🐍 Setting up virtual environment for Windows..."
    python3 -m venv ~/.boost_cli_env
    source ~/.boost_cli_env/Scripts/activate
    echo "Installing boost status CLI using pip to virtual environment"
    cd python-cli
    pip3 install -e . --record ~/.boost_cli_env/install_records.txt

else
    echo "Unsupported OS"
    exit 1
fi
echo "✅ Virtual environment ready!"

# Configure global wrapper script
echo "🔧 Creating 'boost' command shortcut..."
mkdir -p ~/.local/bin

# Create a wrapper script in ~/.local/bin/boost
cat <<EOF > ~/.local/bin/boost
#!/bin/bash
if [[ "$OS" == "linux" || "$OS" == "macos" ]]; then
    source ~/.boost_cli_env/bin/activate
elif [[ "$OS" == "windows" ]]; then
    source ~/.boost_cli_env/Scripts/activate
else
    echo "Unsupported OS"
    exit 1
fi
boost "\$@"
EOF

chmod +x ~/.local/bin/boost

######### Add .local/bin to PATH to assure boost shell complete works ###########
path_cmd='export PATH=$HOME/.local/bin:$PATH'
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  Warning: ~/.local/bin is NOT in your PATH!"
else
    echo "✅ ~/.local/bin is already in your PATH"
fi

# Ensure ~/.local/bin is in terminal profile
# Check if already exists
if [[ $SHELL == *"zsh"* ]]; then
    if grep -q "$path_cmd" ~/.zshrc; then
        echo ".local/bin is already in .zshrc. Not adding it"    
    else
        echo ".local/bin is not in terminal profile. Assuring its there!"    
        echo >> ~/.zshrc # newline
        echo "$path_cmd" >> ~/.zshrc
    fi
elif [[ $SHELL == *"bash"* ]]; then
    if grep -q "$path_cmd" ~/.bashrc; then
        echo ".local/bin is already in .bashrc. Not adding it"
    else
        echo ".local/bin is not in terminal profile. Assuring its there!"    
        echo >> ~/.bashrc # newline
        echo "$path_cmd" >> ~/.bashrc
    fi
else
    echo "Shell not supported"
fi

######################## Configure Autocomplete ###############################
# Configure autocomplete based on shell
echo "🔍 Detecting shell and setting up autocompletion..."

# Check if already exists
if [[ $SHELL == *"zsh"* ]]; then
    if grep -q "_BOOST_COMPLETE=zsh_source boost" ~/.zshrc; then
        echo "✅ Autocomplete already set up for zsh!"
    else
        echo "✨ Configuring zsh autocomplete..."
        echo >> ~/.zshrc # newline
        echo "eval \"\$(_BOOST_COMPLETE=zsh_source boost)\"" >> ~/.zshrc
    fi
elif [[ $SHELL == *"bash"* ]]; then
    if grep -q "_BOOST_COMPLETE=bash_source boost" ~/.bashrc; then
        echo "✅ Autocomplete already set up for bash!"
        exit 0
    else
        echo "✨ Configuring bash autocomplete..."
        echo >> ~/.bashrc # newline
        echo "eval \"\$(_BOOST_COMPLETE=bash_source boost)\"" >> ~/.bashrc
    fi
else
    echo "Shell not supported"
    exit 1
fi

echo "🎉 Installation complete!"
echo "Please restart your shell or run 'source ~/.bashrc' or 'source ~/.zshrc' to apply changes"
echo "👉 Use the command 'boost' to get started with your Fleet CLI!"