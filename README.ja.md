<p align="center">
  <a href="./README.md">Русский</a> · <a href="./README.en.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <strong>日本語</strong> · <a href="./README.de.md">Deutsch</a>
</p>

<h1 align="center">患者記録簿</h1>

<p align="center">
  <strong>手術と麻酔の記録を、ひとつの記録簿に。</strong><br>
  ローカルまたはネットワーク共有上の SQLite データベースで、症例の記録・検索・集計を行う Windows アプリです。
</p>

<p align="center">
  <a href="./app_version.py"><img src="https://img.shields.io/badge/v1.0.9-007aff?style=flat-square" alt="バージョン 1.0.9"></a>
  <img src="https://img.shields.io/badge/Windows-10%20%2F%2011-007aff?style=flat-square" alt="Windows 10 および 11">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square" alt="Python 3.10 以降">
  <img src="https://img.shields.io/badge/SQLite-local-6e6e73?style=flat-square" alt="SQLite によるローカル保存">
</p>

<p align="center">
  <img src="./assets/readme/interface.webp" width="100%" alt="現在の画面：架空のデータを使った手術一覧、検索機能、症例入力フォーム">
</p>

*現在のアプリ画面です。データはすべて架空のものです。アプリの表示言語はロシア語で、README の翻訳はドキュメントのみを対象としています。*

## 主な機能

- **症例の記録。** 予定手術と緊急手術に対応。同じ患者の再手術も個別の症例として保存します。
- **検索。** 患者氏名と手術日で絞り込み、選択した記録を編集・削除できます。
- **麻酔時間。** 日付をまたぐ場合も含め、麻酔の継続時間を自動計算します。
- **レポート。** 指定期間の統計を麻酔の種類、医師、看護師別に確認できます。
- **共通マスター。** 麻酔の種類と職員の一覧、週ごとのバックアップ、共有フォルダーからの更新を利用できます。

**利用形態：** 記録簿のフォルダーはローカルにもネットワーク共有にも置けます。同じ記録簿を同時に利用できるのは **1 台の端末のみ** です。

## クイックスタート

ソースから実行するには **Windows 10/11 と Python 3.10 以降** が必要です。画面は PySide6 で構築されています。

```powershell
git clone https://github.com/Donkiton/Oper-Journal.git
cd Oper-Journal
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe modern_app.py
```

初回起動時は、空のテスト用フォルダーを作成し、接続ダイアログで選択してください。アプリがデータベースとサブフォルダーを作成します。架空の症例を追加して、検索と「レポート」（«Отчёты»）の画面を試してください。

## 詳細

<details>
<summary><strong>データの保存とバックアップ</strong></summary>

選択した記録簿フォルダーには、次のファイルとフォルダーが置かれます。

| パス | 内容 |
|---|---|
| `data/journal.db` | SQLite の症例データベース |
| `settings.json` | 共通設定とマスター一覧 |
| `backups/` | データベースのバックアップ |
| `.journal.lock` | 同時利用を防ぐロックファイル |
| `UPD/` | 更新マニフェストとリリースのアーカイブ |

記録簿への接続時に、ISO 週ごとに 1 回バックアップを作成します。この確認はアプリの動作中に行われ、独立したバックグラウンドの定期処理ではありません。

配布用ビルドは記録簿のパスを `%LOCALAPPDATA%\JornalPatients\connection.json` に保存します。ソースからの実行では、コードと同じディレクトリの `connection.json` を使います。配布用ビルドは、ログと更新キャッシュもローカルに保存します。

</details>

<details>
<summary><strong>マスター一覧と自由入力</strong></summary>

「設定」（«Настройки»）では、各マスター一覧の下に「独自の値の入力を許可する」（«Разрешить ввод своего значения»）チェックボックスがあります。初期設定では、麻酔の種類は自由入力が無効、医師と看護師は有効です。

自由入力が無効の場合は、一覧の値だけを選択できます。一覧にない過去の値は、元の記録で変更せずに保存できます。この設定は、選択した記録簿で共通です。

</details>

<details>
<summary><strong>Windows アプリのビルドと更新</strong></summary>

`.venv` を作成した後、プロジェクトのディレクトリで実行します。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build_release.py
```

`dist/JournalPatients/` フォルダーと `dist/JournalPatients-1.0.9.zip` が生成されます。移動する際は、アプリのフォルダー全体をコピーしてください。バージョンの定義元は [`app_version.py`](./app_version.py) です。ソースのバージョンが最新の GitHub Release より新しい場合があります。

記録簿の共有フォルダーに更新を配置するには、次を実行します。

```powershell
.\.venv\Scripts\python.exe build_release.py --publish-root "\\server\share\Jornal-oper"
```

スクリプトがアーカイブと `UPD/latest.json` を作成します。配布用ビルドは終了時に更新を確認します。データベースのスキーマが新しいアプリのバージョンを必要とする場合は、メインウィンドウを開く前に確認します。インストール前にアーカイブのサイズと SHA-256 を検証します。

</details>

<details>
<summary><strong>開発とテスト</strong></summary>

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

テストでは、データベースの移行、同じ患者の複数症例、マスター一覧、職員名、ドロップダウン、起動時の更新を確認します。

| ファイル | 用途 |
|---|---|
| [`modern_app.py`](./modern_app.py) | PySide6 の画面と記録簿の操作 |
| [`database_schema.py`](./database_schema.py) | SQLite のスキーマと移行 |
| [`update_system.py`](./update_system.py) | 更新の確認とインストール |
| [`build_release.py`](./build_release.py) | ビルドと共有フォルダーへのリリース配置 |
| [`tests/`](./tests/) | 回帰テスト |

貢献のルールは [`CONTRIBUTING.md`](./CONTRIBUTING.md)（ロシア語）を参照してください。サンプルとテストには、架空のデータのみを使用してください。

</details>

## 利用前の確認

本アプリは医療情報システムの代替ではありません。ユーザーアカウントやロールの機能はなく、フォルダーへのアクセスは Windows の権限で制御します。実際の患者データを使用する前に、所属組織の IT 担当者および個人データの取り扱い責任者の承認を得てください。

脆弱性は [`SECURITY.md`](./SECURITY.md) の手順に従って報告してください。アイコンの出典は [`ATTRIBUTION.md`](./ATTRIBUTION.md) に記載しています。現在 `LICENSE` ファイルはなく、利用・再配布の条件はオープンソースライセンスで定められていません。
