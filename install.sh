#!/bin/bash
# jtr-generator インストールスクリプト
# Usage: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/unagi/jtr-generator/main/install.sh)"

set -euo pipefail

# === 設定 ===
GITHUB_REPO="unagi/jtr-generator"
GITHUB_API_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
GITHUB_DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/download"
VERSION_FILE=".version"
SKILL_NAME="jtr-generator"

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# === 関数定義 ===

# エラーハンドリング
error_exit() {
    echo -e "${RED}エラー: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}$1${NC}"
}

warn() {
    echo -e "${YELLOW}$1${NC}"
}

header() {
    echo -e "${BLUE}$1${NC}"
}

# 依存関係チェック
check_dependencies() {
    local missing_deps=()

    command -v curl >/dev/null 2>&1 || missing_deps+=("curl")
    command -v unzip >/dev/null 2>&1 || missing_deps+=("unzip")

    if [ ${#missing_deps[@]} -ne 0 ]; then
        error_exit "必須コマンドが不足しています: ${missing_deps[*]}\n以下のコマンドでインストールしてください:\n  Ubuntu/Debian: sudo apt-get install ${missing_deps[*]}\n  macOS: brew install ${missing_deps[*]}"
    fi

    if ! command -v jq >/dev/null 2>&1; then
        warn "jq がインストールされていません。バージョン比較機能が制限されます。"
    fi
}

# 最新バージョンの取得
get_latest_version() {
    local response
    response=$(curl -fsSL "$GITHUB_API_URL" 2>/dev/null) || error_exit "GitHub API へのアクセスに失敗しました"

    # jqが利用可能な場合
    if command -v jq >/dev/null 2>&1; then
        echo "$response" | jq -r '.tag_name'
    else
        # jqが無い場合は単純なパターンマッチング
        echo "$response" | grep -oP '"tag_name":\s*"\K[^"]+' || error_exit "バージョン情報の解析に失敗しました"
    fi
}

# バージョン比較（セマンティックバージョニング）
version_compare() {
    local v1=$1
    local v2=$2

    # v接頭辞を削除
    v1=${v1#v}
    v2=${v2#v}

    if [ "$v1" = "$v2" ]; then
        return 0 # 同じ
    fi

    # バージョン比較（簡易版）
    local IFS=.
    local i ver1=($v1) ver2=($v2)

    for ((i=0; i<${#ver1[@]}; i++)); do
        if [ "${ver1[i]:-0}" -gt "${ver2[i]:-0}" ] 2>/dev/null; then
            return 1 # v1 > v2
        elif [ "${ver1[i]:-0}" -lt "${ver2[i]:-0}" ] 2>/dev/null; then
            return 2 # v1 < v2
        fi
    done

    return 0
}

# インストール先の検出
detect_install_locations() {
    local locations=()

    # Claude Code
    [ -d "$HOME/.claude/skills" ] && locations+=("$HOME/.claude/skills|Claude Code")

    # Codex
    [ -d "$HOME/.codex/skills" ] && locations+=("$HOME/.codex/skills|Codex")

    # Gemini
    [ -d "$HOME/.gemini/skills" ] && locations+=("$HOME/.gemini/skills|Gemini")

    printf '%s\n' "${locations[@]}"
}

# 既存インストールのチェック
check_existing_installation() {
    local install_dir=$1
    local skill_dir="$install_dir/$SKILL_NAME"

    if [ -d "$skill_dir" ]; then
        if [ -f "$skill_dir/$VERSION_FILE" ]; then
            cat "$skill_dir/$VERSION_FILE"
        else
            echo "unknown"
        fi
    else
        echo ""
    fi
}

# 書き込み権限チェック
check_write_permission() {
    local dir=$1

    if [ ! -w "$dir" ]; then
        error_exit "書き込み権限がありません: $dir\n以下のコマンドで権限を修正してください:\n  sudo chown -R \$USER:\$USER $dir"
    fi
}

# ディスク容量チェック
check_disk_space() {
    local install_dir=$1
    local required_space=10485760  # 10MB（バイト単位）

    local available_space=$(df -B1 "$install_dir" 2>/dev/null | awk 'NR==2 {print $4}')

    if [ -z "$available_space" ] || [ "$available_space" -lt "$required_space" ]; then
        warn "ディスク容量が不足している可能性があります"
    fi
}

# 対話的インストール先選択
select_install_locations() {
    local locations=("$@")
    local selected_dirs=()

    if [ ${#locations[@]} -eq 0 ]; then
        warn "既知のAgent Skillsディレクトリが見つかりませんでした。"
        read -p "インストール先を手動で指定しますか？ (y/N): " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            error_exit "インストールをキャンセルしました"
        fi
        read -p "インストール先ディレクトリ: " custom_dir
        custom_dir="${custom_dir/#\~/$HOME}"  # ~を展開
        mkdir -p "$custom_dir" || error_exit "ディレクトリの作成に失敗しました"
        echo "$custom_dir|Custom"
        return
    fi

    if [ ${#locations[@]} -eq 1 ]; then
        echo "${locations[0]}"
        return
    fi

    header "\n複数のAgent Skillsディレクトリが見つかりました:"
    for i in "${!locations[@]}"; do
        local dir=$(echo "${locations[$i]}" | cut -d'|' -f1)
        local name=$(echo "${locations[$i]}" | cut -d'|' -f2)
        echo "  $((i+1))) $name ($dir)"
    done
    echo "  a) すべてにインストール"
    echo "  c) カスタムパス指定"

    while true; do
        read -p "\n選択 (1-${#locations[@]}/a/c): " choice

        if [[ "$choice" == "a" ]] || [[ "$choice" == "A" ]]; then
            printf '%s\n' "${locations[@]}"
            return
        elif [[ "$choice" == "c" ]] || [[ "$choice" == "C" ]]; then
            read -p "インストール先ディレクトリ: " custom_dir
            custom_dir="${custom_dir/#\~/$HOME}"  # ~を展開
            mkdir -p "$custom_dir" || error_exit "ディレクトリの作成に失敗しました"
            echo "$custom_dir|Custom"
            return
        elif [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#locations[@]} ]; then
            echo "${locations[$((choice-1))]}"
            return
        else
            warn "無効な選択です。1-${#locations[@]}/a/c を入力してください。"
        fi
    done
}

# ダウンロードとインストール
install_skill() {
    local version=$1
    local install_dir=$2
    local agent_name=$3
    local skill_dir="$install_dir/$SKILL_NAME"
    local temp_dir=$(mktemp -d)
    local zip_file="$temp_dir/${SKILL_NAME}-${version}.zip"
    local download_url="${GITHUB_DOWNLOAD_URL}/${version}/${SKILL_NAME}-${version}.zip"

    trap "rm -rf '$temp_dir'" EXIT

    # HTTPS強制
    if [[ ! "$download_url" =~ ^https:// ]]; then
        error_exit "セキュリティエラー: HTTPS以外のURLは許可されていません"
    fi

    header "\n[$agent_name] インストール中..."
    info "ダウンロード中: $download_url"
    if ! curl -fsSL -o "$zip_file" "$download_url"; then
        error_exit "ダウンロードに失敗しました"
    fi

    info "展開中..."
    if ! unzip -q -o "$zip_file" -d "$temp_dir"; then
        error_exit "展開に失敗しました"
    fi

    # 展開後のサイズチェック（zip爆弾対策）
    local extracted_size=$(du -sb "$temp_dir" 2>/dev/null | awk '{print $1}')
    local max_size=52428800  # 50MB
    if [ "$extracted_size" -gt "$max_size" ]; then
        error_exit "展開されたファイルサイズが制限を超えています"
    fi

    # バックアップ（上書きの場合）
    if [ -d "$skill_dir" ]; then
        local backup_dir="${skill_dir}.backup.$(date +%Y%m%d-%H%M%S)"
        info "既存のインストールをバックアップ: $backup_dir"
        mv "$skill_dir" "$backup_dir"
    fi

    info "インストール中: $skill_dir"
    mkdir -p "$install_dir"

    # tempディレクトリから正しいディレクトリを見つけて移動
    if [ -d "$temp_dir/$SKILL_NAME" ]; then
        mv "$temp_dir/$SKILL_NAME" "$skill_dir" || error_exit "インストールに失敗しました"
    else
        # zipの中身が直接展開されている場合
        mkdir -p "$skill_dir"
        mv "$temp_dir"/* "$skill_dir/" 2>/dev/null || true
    fi

    # バージョンファイルの作成
    echo "$version" > "$skill_dir/$VERSION_FILE"

    info "✓ [$agent_name] インストール完了: $skill_dir"
}

# === メイン処理 ===
main() {
    header "=== jtr-generator インストーラー ==="
    echo

    # 依存関係チェック
    check_dependencies

    # 最新バージョンの取得
    info "最新バージョンを確認中..."
    local latest_version=$(get_latest_version)
    info "最新バージョン: $latest_version"

    # インストール先の検出
    local all_locations=($(detect_install_locations))
    local selected_locations_raw=$(select_install_locations "${all_locations[@]}")

    # 改行区切りの文字列を配列に変換
    local selected_locations=()
    while IFS= read -r line; do
        [ -n "$line" ] && selected_locations+=("$line")
    done <<< "$selected_locations_raw"

    # 各インストール先について処理
    local installed_dirs=()
    for location in "${selected_locations[@]}"; do
        local install_dir=$(echo "$location" | cut -d'|' -f1)
        local agent_name=$(echo "$location" | cut -d'|' -f2)

        # 既存インストールのチェック
        local existing_version=$(check_existing_installation "$install_dir")

        if [ -n "$existing_version" ]; then
            header "\n[$agent_name] 既存のインストールが見つかりました"
            if [ "$existing_version" = "unknown" ]; then
                warn "  バージョン: 不明"
            else
                info "  バージョン: $existing_version"
                version_compare "$existing_version" "$latest_version"
                case $? in
                    0) info "  → 最新バージョンが既にインストールされています" ;;
                    1) warn "  → インストール済みのバージョンの方が新しいです" ;;
                    2) info "  → アップデート可能です" ;;
                esac
            fi

            read -p "上書きインストールしますか？ (y/N): " response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                info "[$agent_name] インストールをスキップしました"
                continue
            fi
        fi

        # 権限とディスク容量のチェック
        check_write_permission "$install_dir"
        check_disk_space "$install_dir"

        # インストール実行
        install_skill "$latest_version" "$install_dir" "$agent_name"
        installed_dirs+=("$install_dir/$SKILL_NAME|$agent_name")
    done

    # 完了メッセージ
    if [ ${#installed_dirs[@]} -eq 0 ]; then
        warn "\nインストールは実行されませんでした"
        exit 0
    fi

    header "\n=== インストールが完了しました ==="
    info "インストール先:"
    for dir_info in "${installed_dirs[@]}"; do
        local dir=$(echo "$dir_info" | cut -d'|' -f1)
        local name=$(echo "$dir_info" | cut -d'|' -f2)
        info "  - [$name] $dir"
    done

    echo
    header "使い方:"
    for dir_info in "${installed_dirs[@]}"; do
        local name=$(echo "$dir_info" | cut -d'|' -f2)
        case "$name" in
            "Claude Code")
                info "  claude 'jtr-generator で履歴書を作成してください'"
                ;;
            "Codex")
                info "  codex 'jtr-generator で履歴書を作成してください'"
                ;;
            "Gemini")
                info "  gemini 'jtr-generator で履歴書を作成してください'"
                ;;
            *)
                info "  エージェントのドキュメントを参照してください"
                ;;
        esac
        break  # 最初の1つだけ表示
    done

    echo
    info "詳細: https://github.com/$GITHUB_REPO"
}

main "$@"
