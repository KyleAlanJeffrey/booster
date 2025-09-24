#!/bin/bash
set -euo pipefail

say() { printf "%b\n" "$*"; }
ok()  { say "✅ $*"; }
info(){ say "ℹ️  $*"; }
step(){ say ""; say "▶️  $*"; }

step "Detecting Python used by CMake"
# If you know CMake picks a specific Python, set it; otherwise try to read from cache or fall back.
PY_EXE_DEFAULT="/usr/local/python/current/bin/python3"
if command -v cmake >/dev/null 2>&1 && [ -f CMakeCache.txt ]; then
  # Try to parse an existing CMakeCache (best-effort)
  PY_EXE=$(grep -E '^Python3_EXECUTABLE:FILEPATH=' CMakeCache.txt | cut -d= -f2 || true)
  PY_EXE=${PY_EXE:-$PY_EXE_DEFAULT}
else
  PY_EXE="$PY_EXE_DEFAULT"
fi

if ! [ -x "$PY_EXE" ]; then
  info "CMake-reported Python not found; falling back to python3 on PATH"
  PY_EXE="$(command -v python3 || true)"
fi

if ! [ -x "$PY_EXE" ]; then
  say "❌ Could not find a Python interpreter. Install Python 3."
  exit 1
fi

info "Using Python: $PY_EXE"

step "Ensuring pybind11 + tools are installed for THIS Python"
# Use --user unless running as root without HOME; fall back to --prefix if needed.
PIP_ARGS=()
if [ "$(id -u)" -ne 0 ]; then
  PIP_ARGS+=(--user)
fi

"$PY_EXE" -m pip install -q "${PIP_ARGS[@]}" --upgrade pip
"$PY_EXE" -m pip install -q "${PIP_ARGS[@]}" pybind11 pybind11-stubgen
ok "Installed pybind11 for $("$PY_EXE" -V)"

# Ensure user's local bin is on PATH (for stubgen etc.)
USER_BIN="$("$PY_EXE" -c 'import site,sys; print(site.getuserbase()+"/bin")' 2>/dev/null || true)"
if [ -n "$USER_BIN" ] && [ -d "$USER_BIN" ]; then
  export PATH="$USER_BIN:$PATH"
  info "🔧 Updated PATH to include local bin: $USER_BIN"
fi

step "Locating pybind11 CMake package directory"
# Reliable way: pybind11 exposes its cmake dir
PYBIND11_DIR="$("$PY_EXE" -m pybind11 --cmakedir)"
ok "pybind11_DIR = $PYBIND11_DIR"

# Help CMake find it (both ways are fine; we’ll pass the var explicitly too)
export CMAKE_PREFIX_PATH="${PYBIND11_DIR}:${CMAKE_PREFIX_PATH:-}"

step "Configuring build directory"
mkdir -p build
cd build

step "Running CMake with Python bindings enabled"
cmake .. \
  -DBUILD_PYTHON_BINDING=on \
  -Dpybind11_DIR="$PYBIND11_DIR"

step "Building"
make -j"$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)"

step "Installing (may require sudo)"
# If your install prefix is system-wide, this likely needs sudo
if [ "${SUDO:-}" = "1" ]; then
  sudo make install
else
  # Try without sudo first; if it fails, suggest sudo
  if make install; then
    :
  else
    say "🛑 Install failed without sudo. Retrying with sudo..."
    sudo make install
  fi
fi

ok "Build and install complete!"

step "Verifying Python import"
# Try to import the module if you know its name; replace 'booster' if different.
MOD_TEST="import booster as _m; print('booster loaded from:', getattr(_m, '__file__', '<unknown>'))"
if "$PY_EXE" -c "$MOD_TEST" 2>/tmp/booster_import_err.log; then
  ok "Python import succeeded 🎉"
else
  say "⚠️  Import failed. Here’s the last error:"
  tail -n 20 /tmp/booster_import_err.log || true
  say "💡 Tips:"
  say "   • Ensure the install prefix is on PYTHONPATH (site-packages)."
  say "   • If you installed to /usr/local, Python usually finds it automatically."
  say "   • Confirm the extension module name matches your import (e.g., 'booster')."
fi