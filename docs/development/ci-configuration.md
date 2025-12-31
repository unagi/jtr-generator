# CI/CD設定ファイル一覧

本プロジェクトで使用しているCI/CD関連の設定ファイルをまとめています。
ディレクトリ構成変更時やパス変更時は、以下のファイルを必ず確認してください。

## GitHub Actions

### `.github/workflows/ci.yml`

**目的**: PR作成時とmainブランチへのpush時にLint/Test/Coverageを実行

**重要な設定項目**:
- Python 3.11を使用
- poppler-utils（pdf2image依存）をインストール
- `uv sync --all-extras --dev`で依存関係をインストール
- Lint（ruff）→ Format check（ruff）→ Type check（mypy）→ Test（pytest）の順に実行
- `coverage.xml`をCodecovとSonarCloudに送信
- SonarCloud解析は `SonarSource/sonarqube-scan-action` で実行し、`SONAR_HOST_URL=https://sonarcloud.io` を指定

**パス関連の注意点**:
- `coverage.xml`のパスはプロジェクトルート直下（pyproject.toml設定と一致）
- テストコードは`tests/`配下を自動検出（pytest設定）

**ハッシュ固定されたアクション**:
- `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5` (v4)
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` (v5)
- `astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86` (v5)
- `codecov/codecov-action@b9fd7d16f6d7d1b5d2bec1a2887e65ceed900238` (v4)
- `SonarSource/sonarqube-scan-action@a31c9398be7ace6bbfaf30c0bd5d415f843d45e9` (v7.0.0)

**必要なシークレット/環境変数**:
- `CODECOV_TOKEN`: Codecovアップロード用
- `SONAR_TOKEN`: SonarCloudスキャン用
- `SONAR_HOST_URL`: SonarCloudの場合は `https://sonarcloud.io`（ワークフロー内で環境変数として指定）

### `.github/workflows/release.yml`

**目的**: mainブランチへのpush時またはvタグ作成時にAgent Skillsパッケージをビルド・リリース

**重要な設定項目**:
- `uv run poe build-skill`でzipパッケージを生成
- タグの場合は`jtr-generator-{version}.zip`、mainの場合は`jtr-generator-latest.zip`
- GitHub Artifactsに90日間保存
- vタグの場合はGitHub Releaseを自動作成

**パス関連の注意点**:
- ビルド成果物は`build/jtr-generator.zip`に生成される
- ビルドスクリプト（`tools/build_skill.py`）がソースコードを収集・パッケージング

**ハッシュ固定されたアクション**:
- `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5` (v4)
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` (v5)
- `astral-sh/setup-uv@d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86` (v5)
- `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` (v4.6.2)
- `softprops/action-gh-release@v2.5.0`（2025年1月時点の最新版）

**必要なシークレット**:
- `GITHUB_TOKEN`: GitHub Releaseとartifactアップロードに使用（自動提供）

## SonarCloud

### `sonar-project.properties`

**目的**: SonarCloudによる静的解析・品質ゲート・カバレッジ可視化

**重要な設定項目**:
```properties
sonar.organization=unagi
sonar.projectKey=unagi_jtr-generator
sonar.projectName=jtr-generator
sonar.projectVersion=0.1.0

# ソースコードのパス
sonar.sources=skill,tools
sonar.tests=tests

# Python設定
sonar.python.version=3.11

# カバレッジレポートのパス
sonar.python.coverage.reportPaths=coverage.xml

# 除外設定
sonar.exclusions=\
    **/outputs/**,\
    **/platforms/**,\
    **/data/**,\
    **/__pycache__/**,\
    **/.venv/**,\
    **/*.egg-info/**

sonar.test.exclusions=\
    **/tests/**

# ソースファイルのエンコーディング
sonar.sourceEncoding=UTF-8
```

**パス関連の注意点**:
- `sonar.sources`: 解析対象のソースコード配置先（`skill/`, `tools/`）
- `sonar.tests`: テストコード配置先（`tests/`）
- `sonar.python.coverage.reportPaths`: カバレッジファイル（`coverage.xml`）
- `sonar.exclusions`: 解析除外パターン

**ディレクトリ構成変更時の更新箇所**:
- モジュール名変更 → `sonar.sources`を更新
- テストディレクトリ移動 → `sonar.tests`を更新
- カバレッジファイル出力先変更 → `sonar.python.coverage.reportPaths`を更新

**必要なシークレット**:
- `SONAR_TOKEN`: SonarCloud認証用（GitHub Secretsに設定）

## Codecov

### `.codecov.yml`

**目的**: Codecovによるカバレッジレポートの可視化・閾値設定

**重要な設定項目**:
```yaml
coverage:
  status:
    project:
      default:
        target: 80  # プロジェクト全体のカバレッジ目標
        threshold: 2.0  # ±2%までの変動は許容
    patch:
      default:
        informational: true  # PR差分のカバレッジは情報提供のみ
```

**パス関連の注意点**:
- カバレッジファイルのパスは`.github/workflows/ci.yml`の`codecov-action`で指定（`coverage.xml`）
- 本ファイル自体にはパス設定なし（デフォルトでプロジェクトルート配下を検索）

**設定変更時の注意**:
- `target`: SonarCloudの品質ゲート設定と合わせる（現在80%）
- `threshold`: カバレッジ低下の許容範囲（CI失敗させたくない場合は大きくする）

**必要なシークレット**:
- `CODECOV_TOKEN`: Codecovアップロード用（GitHub Secretsに設定）

## トラブルシューティング

### CI失敗時のチェックリスト

**Lint/Format/Typecheck失敗**:
```bash
uv run poe lint         # ruffでコード品質チェック
uv run poe format-check # ruffでフォーマットチェック
uv run poe typecheck    # mypyで型チェック
```

**Test失敗**:
```bash
uv run poe test         # pytest実行
uv run poe test-cov     # カバレッジ付きテスト
```

**SonarCloud失敗**:
- `coverage.xml`が生成されているか確認
- `sonar-project.properties`のパス設定が正しいか確認
- SonarCloud Webコンソールでエラー詳細を確認

**Codecov失敗**:
- `CODECOV_TOKEN`が設定されているか確認
- `coverage.xml`が生成されているか確認
- Codecov Webコンソールでアップロード履歴を確認

### 出力ファイルパス仕様

**Agent Skillsにおける出力ファイル指定**:

`skill/main.py`の`main()`関数は`output_path`パラメータで出力先を指定できます。

**パラメータ**:
```python
output_path: Path | str | None = None
```

**動作**:
- `None`（デフォルト）: カレントディレクトリに`rirekisho.pdf`を生成
- ファイル名のみ（例: `"yamada.pdf"`）: カレントディレクトリに指定ファイル名で生成
- 相対パス（例: `"outputs/resume.pdf"`）: カレントディレクトリ基準の相対パスに生成
- 絶対パス（例: `"/tmp/result.pdf"`）: 指定された絶対パスに生成

**Agent Skills実行環境**:
- 各リクエストは独立したコンテナで実行されるため、ファイル名の競合は発生しない
- Files APIがカレントディレクトリのファイルを自動検出し、`file_id`を生成
- ハードコーディングされた固定パスは不要（柔軟性のため廃止）

**使用例**:
```python
# デフォルト
main(data)  # → rirekisho.pdf

# カスタムファイル名
main(data, output_path="yamada_resume.pdf")

# サブディレクトリ指定
main(data, output_path="outputs/2025_resume.pdf")
```

### ディレクトリ構成変更時の更新チェックリスト

モジュール名やディレクトリ構成を変更した場合、以下のファイルを確認:

- [ ] `sonar-project.properties` - `sonar.sources`、`sonar.tests`、`sonar.exclusions`、`sonar.test.exclusions`
- [ ] `.github/workflows/ci.yml` - カバレッジファイルのパス
- [ ] `tools/build_skill.py` - Agent Skillsパッケージのファイルコピー処理
- [ ] `pyproject.toml` - pytest、mypy、coverage設定
- [ ] テストコード内のモジュールスタブ（`tests/tools/test_*.py`）

### アクション更新時の注意

GitHub Actionsはセキュリティのため、コミットハッシュで固定しています。

**更新手順**:
1. GitHub APIまたはリポジトリで最新タグのハッシュを確認
2. コメント内のバージョン番号も同時に更新
3. CHANGELOG確認（破壊的変更がないか）

※ `softprops/action-gh-release` は安定性優先のため `v2.5.0` タグ指定で運用中です。

**例**:
```yaml
# ❌ 誤り（タグ指定はセキュリティリスク）
uses: actions/checkout@v4

# ✅ 正解（ハッシュ固定 + バージョンコメント）
uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4
```

## 関連ドキュメント

- [README.md](../../README.md) - プロジェクト概要・セットアップ
- [AGENTS.md](../../AGENTS.md) - プロジェクト全体仕様
- [CLAUDE.md](../../CLAUDE.md) - Agent Skills技術仕様
- [coverage.md](coverage.md) - カバレッジ改善履歴
