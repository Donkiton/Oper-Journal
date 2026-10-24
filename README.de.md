<p align="center">
  <a href="./README.md">Русский</a> · <a href="./README.en.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.ja.md">日本語</a> · <strong>Deutsch</strong>
</p>

<h1 align="center">Patientenjournal</h1>

<p align="center">
  <strong>Operationen und Anästhesie in einem Journal.</strong><br>
  Eine Windows-Anwendung für Fallerfassung, Suche und Statistik mit einer lokalen SQLite-Datenbank oder einer Datenbank auf einem Netzlaufwerk.
</p>

<p align="center">
  <a href="./app_version.py"><img src="https://img.shields.io/badge/v1.0.9-007aff?style=flat-square" alt="Version 1.0.9"></a>
  <img src="https://img.shields.io/badge/Windows-10%20%2F%2011-007aff?style=flat-square" alt="Windows 10 und 11">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square" alt="Python 3.10 oder neuer">
  <img src="https://img.shields.io/badge/SQLite-lokal-6e6e73?style=flat-square" alt="Lokale Datenspeicherung mit SQLite">
</p>

<p align="center">
  <img src="./assets/readme/interface.webp" width="100%" alt="Aktuelle Oberfläche mit Operationsübersicht, Suche und Formular zur Fallerfassung mit fiktiven Daten">
</p>

*Die aktuelle Anwendung mit fiktiven Daten. Die Oberfläche ist auf Russisch; die README-Übersetzungen beziehen sich auf die Dokumentation.*

## Funktionen

- **Fallerfassung.** Geplante Operationen und Notfalleingriffe; wiederholte Operationen eines Patienten werden als separate Fälle gespeichert.
- **Suche.** Nach Patientenname und Operationsdatum filtern sowie den ausgewählten Eintrag bearbeiten oder löschen.
- **Anästhesiedauer.** Automatische Berechnung, auch bei Eingriffen über Mitternacht.
- **Berichte.** Statistiken für einen gewählten Zeitraum nach Anästhesieverfahren, Ärzten und Pflegekräften.
- **Gemeinsame Auswahllisten.** Anästhesieverfahren und Personal, wöchentliche Sicherungskopien und Updates aus dem gemeinsamen Ordner.

**Betrieb:** Der Journalordner kann lokal oder auf einer Netzwerkfreigabe liegen. Ein Journal kann jeweils nur von **einem Arbeitsplatz gleichzeitig** verwendet werden.

## Schnellstart

Für den Start aus dem Quellcode werden **Windows 10/11 und Python 3.10+** benötigt. Die Oberfläche basiert auf PySide6.

```powershell
git clone https://github.com/Donkiton/Oper-Journal.git
cd Oper-Journal
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe modern_app.py
```

Erstellen Sie für den ersten Start einen leeren Testordner und wählen Sie ihn im Verbindungsdialog aus. Die Anwendung legt die Datenbank und Unterordner an. Erfassen Sie einen fiktiven Fall und testen Sie die Suche sowie die Berichtsseite («Отчёты»).

## Details

<details>
<summary><strong>Datenspeicherung und Sicherungskopien</strong></summary>

Der ausgewählte Journalordner enthält:

| Pfad | Inhalt |
|---|---|
| `data/journal.db` | SQLite-Datenbank der Fälle |
| `settings.json` | Gemeinsame Einstellungen und Auswahllisten |
| `backups/` | Sicherungskopien der Datenbank |
| `.journal.lock` | Sperre gegen gleichzeitige Nutzung |
| `UPD/` | Update-Manifest und Versionsarchive |

Beim Verbinden mit dem Journal wird eine Sicherungskopie pro ISO-Kalenderwoche erstellt. Die Prüfung erfolgt innerhalb der Anwendung, ohne unabhängigen Zeitplan im Hintergrund.

Die gepackte Anwendung speichert den Pfad zum Journal in `%LOCALAPPDATA%\JornalPatients\connection.json`; beim Start aus dem Quellcode wird `connection.json` im Quellcodeverzeichnis verwendet. Die gepackte Anwendung speichert außerdem lokale Protokolle und einen Update-Cache.

</details>

<details>
<summary><strong>Auswahllisten und freie Eingabe</strong></summary>

In den Einstellungen («Настройки») befindet sich unter jeder Auswahlliste das Kontrollkästchen „Eigene Werte zulassen“ («Разрешить ввод своего значения»). Für Anästhesieverfahren ist es standardmäßig deaktiviert, für Ärzte und Pflegekräfte aktiviert.

Wenn die freie Eingabe deaktiviert ist, können nur Werte aus der Liste gewählt werden. Ein bereits gespeicherter Wert außerhalb der Liste kann im ursprünglichen Eintrag unverändert beibehalten werden. Diese Einstellungen gelten gemeinsam für das ausgewählte Journal.

</details>

<details>
<summary><strong>Windows-Anwendung erstellen und aktualisieren</strong></summary>

Führen Sie nach dem Anlegen von `.venv` im Projektverzeichnis folgende Befehle aus:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build_release.py
```

Es entstehen der Ordner `dist/JournalPatients/` und das Archiv `dist/JournalPatients-1.0.9.zip`. Kopieren Sie immer den gesamten Anwendungsordner. Die Version wird in [`app_version.py`](./app_version.py) festgelegt; der Quellcode kann neuer sein als das letzte GitHub Release.

So stellen Sie ein Update im gemeinsamen Journalordner bereit:

```powershell
.\.venv\Scripts\python.exe build_release.py --publish-root "\\server\share\Jornal-oper"
```

Das Skript erstellt ein Archiv und `UPD/latest.json`. Die gepackte Anwendung prüft beim Beenden auf Updates. Erfordert das Datenbankschema eine neuere Version, erfolgt die Prüfung vor dem Öffnen des Hauptfensters. Vor der Installation werden Archivgröße und SHA-256-Prüfsumme geprüft.

</details>

<details>
<summary><strong>Entwicklung und Tests</strong></summary>

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Die Tests prüfen Migrationen, wiederholte Fälle, Auswahllisten, Personalnamen, Dropdown-Menüs und Updates beim Programmstart.

| Datei | Zweck |
|---|---|
| [`modern_app.py`](./modern_app.py) | PySide6-Oberfläche und Journalfunktionen |
| [`database_schema.py`](./database_schema.py) | SQLite-Schema und Migrationen |
| [`update_system.py`](./update_system.py) | Update-Prüfung und Installation |
| [`build_release.py`](./build_release.py) | Erstellung und Bereitstellung im gemeinsamen Ordner |
| [`tests/`](./tests/) | Regressionstests |

Die Regeln für Beiträge stehen in [`CONTRIBUTING.md`](./CONTRIBUTING.md) (auf Russisch). Verwenden Sie in Beispielen und Tests ausschließlich fiktive Daten.

</details>

## Vor der Verwendung

Die Anwendung ersetzt kein medizinisches Informationssystem. Sie verfügt über keine integrierten Benutzerkonten oder Rollen; der Ordnerzugriff wird durch Windows-Berechtigungen geregelt. Stimmen Sie die Verwendung echter Patientendaten mit den IT- und Datenschutzverantwortlichen Ihrer Organisation ab.

Melden Sie Sicherheitslücken gemäß [`SECURITY.md`](./SECURITY.md). Die Quellenangaben für Symbole stehen in [`ATTRIBUTION.md`](./ATTRIBUTION.md). Eine `LICENSE`-Datei fehlt derzeit; Nutzung und Weitergabe sind nicht durch eine Open-Source-Lizenz geregelt.
