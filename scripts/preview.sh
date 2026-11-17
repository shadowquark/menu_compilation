#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
mdbook_version="$(tr -d '\n\r' < .mdbook-version)"
mdbook_bin="$project_dir/.tools/mdbook-v$mdbook_version/mdbook"
if [[ ! -x "$mdbook_bin" ]]; then
    case "$(uname -s)-$(uname -m)" in
        Linux-x86_64) mdbook_target=x86_64-unknown-linux-gnu ;;
        Darwin-arm64) mdbook_target=aarch64-apple-darwin ;;
        Darwin-x86_64) mdbook_target=x86_64-apple-darwin ;;
        *) echo '请安装 .mdbook-version 指定的 mdBook 版本。' >&2; exit 1 ;;
    esac
    mdbook_archive="$(mktemp)"
    trap 'rm -f "$mdbook_archive"' EXIT
    curl -fL "https://github.com/rust-lang/mdBook/releases/download/v$mdbook_version/mdbook-v$mdbook_version-$mdbook_target.tar.gz" -o "$mdbook_archive"
    mkdir -p "$(dirname "$mdbook_bin")"
    tar -xzf "$mdbook_archive" -C "$(dirname "$mdbook_bin")"
    rm -f "$mdbook_archive"
    trap - EXIT
fi
source "$project_dir/scripts/font_env.sh"
python3 scripts/build_pages.py
preview_host="${MENU_PREVIEW_HOST:-127.0.0.1}"
exec "$mdbook_bin" serve -n "$preview_host" -p 3000 "$@"
