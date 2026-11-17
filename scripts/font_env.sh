#!/usr/bin/env bash
# Configure an isolated font toolchain only when the current Python lacks it.
ensure_font_environment() {
    local font_project_dir
    font_project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    if python3 "$font_project_dir/scripts/build_fonts.py" --check-dependencies >/dev/null 2>&1; then
        return
    fi
    local font_environment="$font_project_dir/.tools/font-env"
    if [[ ! -x "$font_environment/bin/python" ]]; then
        if command -v uv >/dev/null 2>&1; then
            UV_CACHE_DIR="$font_project_dir/.tools/uv-cache" uv venv --python "$(command -v python3)" "$font_environment"
        else
            python3 -m venv "$font_environment"
        fi
    fi
    if ! "$font_environment/bin/python" "$font_project_dir/scripts/build_fonts.py" --check-dependencies >/dev/null 2>&1; then
        if command -v uv >/dev/null 2>&1; then
            UV_CACHE_DIR="$font_project_dir/.tools/uv-cache" uv pip install --python "$font_environment/bin/python" -r "$font_project_dir/requirements-fonts.txt"
        else
            "$font_environment/bin/python" -m pip install -r "$font_project_dir/requirements-fonts.txt"
        fi
    fi
    export PATH="$font_environment/bin:$PATH"
}
ensure_font_environment
