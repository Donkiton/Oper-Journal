<p align="center">
  <a href="./README.md">Русский</a> · <strong>English</strong> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.ja.md">日本語</a> · <a href="./README.de.md">Deutsch</a>
</p>

<h1 align="center">Patient Journal</h1>

<p align="center">
  <strong>Surgery and anesthesia records in one journal.</strong><br>
  A Windows app for recording cases, searching records, and viewing statistics with a local or network SQLite database.
</p>

<p align="center">
  <a href="./app_version.py"><img src="https://img.shields.io/badge/v1.0.9-007aff?style=flat-square" alt="Version 1.0.9"></a>
  <img src="https://img.shields.io/badge/Windows-10%20%2F%2011-007aff?style=flat-square" alt="Windows 10 and 11">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square" alt="Python 3.10 or later">
  <img src="https://img.shields.io/badge/SQLite-local-6e6e73?style=flat-square" alt="Local SQLite storage">
</p>

<p align="center">
  <img src="./assets/readme/interface.webp" width="100%" alt="Current interface: surgery records, search, and a case entry form with fictional data">
</p>

*The current app with fictional data. The interface is in Russian; these README translations cover the documentation.*

## Features

- **Case records.** Scheduled and emergency surgery; repeat operations for a patient are stored as separate cases.
- **Search.** Filter by patient name and surgery date; edit or delete the selected record.
- **Anesthesia duration.** Automatic calculation, including procedures that cross midnight.
- **Reports.** Statistics for a selected period by anesthesia type, physician, and nurse.
- **Shared reference lists.** Anesthesia types and staff, weekly backups, and updates from the shared folder.

**Usage:** the journal folder can be local or on a network share. Only **one workstation at a time** can use a given journal.

## Quick start

Running from source requires **Windows 10/11 and Python 3.10+**. The interface uses PySide6.

```powershell
git clone https://github.com/Donkiton/Oper-Journal.git
cd Oper-Journal
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe modern_app.py
```

On first launch, create an empty test folder and select it in the connection dialog. The app will create the database and subfolders. Add a fictional case, then try search and the reports page («Отчёты»).

## Details

<details>
<summary><strong>Storage and backups</strong></summary>

The selected journal folder contains:

| Path | Contents |
|---|---|
| `data/journal.db` | SQLite case database |
| `settings.json` | Shared settings and reference lists |
| `backups/` | Database backups |
| `.journal.lock` | Lock preventing simultaneous use |
| `UPD/` | Update manifest and release archives |

One backup is created per ISO week when connecting to the journal. This check runs within the app, rather than on an independent background schedule.

The packaged app stores the journal path in `%LOCALAPPDATA%\JornalPatients\connection.json`; source runs use `connection.json` beside the code. The packaged app also keeps local logs and an update cache.

</details>

<details>
<summary><strong>Reference lists and custom values</strong></summary>

In settings («Настройки»), each reference list has an “Allow custom values” checkbox («Разрешить ввод своего значения»). It is off by default for anesthesia types and on for physicians and nurses.

When custom entry is disabled, only listed values can be selected. An existing value absent from the list can be kept unchanged in its original record. These settings are shared by the selected journal.

</details>

<details>
<summary><strong>Windows builds and updates</strong></summary>

From the project directory, after creating `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build_release.py
```

The output is `dist/JournalPatients/` and `dist/JournalPatients-1.0.9.zip`. Copy the entire application folder. [`app_version.py`](./app_version.py) is the version source; the code may be newer than the latest GitHub Release.

To place an update in the shared journal folder:

```powershell
.\.venv\Scripts\python.exe build_release.py --publish-root "\\server\share\Jornal-oper"
```

The script creates an archive and `UPD/latest.json`. The packaged app checks for updates on exit, or before opening the main window if the database schema requires a newer version. Archive size and SHA-256 are checked before installation.

</details>

<details>
<summary><strong>Development and tests</strong></summary>

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover migrations, repeat cases, reference lists, staff names, dropdowns, and startup updates.

| File | Purpose |
|---|---|
| [`modern_app.py`](./modern_app.py) | PySide6 interface and journal operations |
| [`database_schema.py`](./database_schema.py) | SQLite schema and migrations |
| [`update_system.py`](./update_system.py) | Update checks and installation |
| [`build_release.py`](./build_release.py) | Builds and release placement in the shared folder |
| [`tests/`](./tests/) | Regression tests |

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for contribution rules (in Russian). Use fictional data only in examples and tests.

</details>

## Before use

The app does not replace a medical information system. It has no built-in accounts or roles; Windows permissions control folder access. Before using real patient data, obtain approval from your organization’s IT and personal data officers.

Report vulnerabilities as described in [`SECURITY.md`](./SECURITY.md). Icon credits are in [`ATTRIBUTION.md`](./ATTRIBUTION.md). There is currently no `LICENSE` file; use and distribution terms are not defined by an open-source license.
