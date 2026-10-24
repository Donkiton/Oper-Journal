from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea

import modern_app
from database_schema import initialize_schema
from modern_app import DataStore, JournalWindow


REFERENCE_FIELDS = {
    "anesthesia": ("anesthesia_types", "allow_custom_anesthesia"),
    "doctor": ("doctors", "allow_custom_doctor"),
    "nurse": ("nurses", "allow_custom_nurse"),
}


class ReferenceInputSettingsTests(unittest.TestCase):
    def test_missing_or_invalid_permissions_use_safe_defaults(self) -> None:
        defaults = {
            "allow_custom_anesthesia": False,
            "allow_custom_doctor": True,
            "allow_custom_nurse": True,
        }
        for key, default in defaults.items():
            with self.subTest(key=key, source="missing"):
                self.assertIs(DataStore.validated_settings({})[key], default)
            for invalid in (None, 0, 1, "true", "false", [], {}):
                with self.subTest(key=key, invalid=invalid):
                    self.assertIs(DataStore.validated_settings({key: invalid})[key], default)
            for enabled in (False, True):
                with self.subTest(key=key, enabled=enabled):
                    self.assertIs(DataStore.validated_settings({key: enabled})[key], enabled)


class ReferenceInputUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        local_state = self.root / "local"
        for name, value in {
            "LOCAL_STATE_DIR": local_state,
            "LOCAL_CONNECTION_PATH": local_state / "connection.json",
            "LOCAL_LEGACY_SETTINGS_PATH": local_state / "settings.json",
            "LEGACY_CONFIG_PATH": self.root / "legacy-settings.json",
        }.items():
            patcher = patch.object(modern_app, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.store = DataStore.__new__(DataStore)
        self.store.settings = DataStore.validated_settings(
            {
                "anesthesia_types": ["Общая", "Спинальная"],
                "doctors": ["Петров И. П.", "Сидоров А. В."],
                "nurses": ["Иванова Е. П.", "Петрова А. В."],
            },
            self.root,
        )
        self.store.conn = sqlite3.connect(":memory:")
        self.store.conn.row_factory = sqlite3.Row
        self.store.connected_root = self.root
        self.store.error = ""
        self.store.update_required = False
        initialize_schema(self.store.conn)
        self.window = JournalWindow(self.store)
        self.error_patcher = patch.object(self.window, "show_validation_error")
        self.validation_error = self.error_patcher.start()
        self.addCleanup(self.error_patcher.stop)

    def tearDown(self) -> None:
        self.window.close()

    def checkbox(self, field: str):
        reference_key, _ = REFERENCE_FIELDS[field]
        return next(
            card.custom_input_checkbox
            for card in self.window.reference_cards
            if card.key == reference_key
        )

    def fill_required_fields(self, history: str = "test-case") -> None:
        self.window.fields["history"].setText(history)
        self.window.fields["name"].setText("Тестовый пациент")
        self.window.fields["anesthesia"].setCurrentText("Общая")

    def assert_no_cases(self) -> None:
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0], 0)

    def select_case(self, patient_id: int) -> None:
        self.window.load_patients()
        for row in range(self.window.table.rowCount()):
            if self.window.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == patient_id:
                self.window.table.selectRow(row)
                return
        self.fail(f"Случай id={patient_id} не найден")

    def test_defaults_and_checkboxes_change_only_their_own_field(self) -> None:
        expected = {"anesthesia": False, "doctor": True, "nurse": True}
        for field, enabled in expected.items():
            self.assertEqual(self.checkbox(field).isChecked(), enabled)
            self.assertEqual(self.window.fields[field].isEditable(), enabled)
        for field in REFERENCE_FIELDS:
            expected[field] = not expected[field]
            self.checkbox(field).setChecked(expected[field])
            for candidate, enabled in expected.items():
                with self.subTest(changed=field, field=candidate):
                    _, setting = REFERENCE_FIELDS[candidate]
                    self.assertIs(self.store.settings[setting], enabled)
                    self.assertEqual(self.window.fields[candidate].isEditable(), enabled)
                    self.assertEqual(self.checkbox(candidate).isChecked(), enabled)

    def test_settings_controls_fit_at_minimum_window_size(self) -> None:
        if not QFontDatabase.families():
            # Windows offscreen не перечисляет системные шрифты автоматически.
            font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf"
            if not font_path.is_file() or QFontDatabase.addApplicationFont(str(font_path)) < 0:
                self.skipTest("Нет шрифта для достоверной проверки размеров текста")
        self.window.setFont(QFont("Segoe UI", 9))
        self.window.resize(1160, 720)
        self.window.show()
        self.window.show_settings()
        self.application.processEvents()
        page = self.window.settings_page
        self.assertIsInstance(page, QScrollArea)
        self.assertEqual(page.horizontalScrollBar().maximum(), 0)
        for card in self.window.reference_cards:
            with self.subTest(reference=card.key):
                checkbox = card.custom_input_checkbox
                self.assertTrue(card.rect().contains(checkbox.geometry()))
                self.assertGreaterEqual(checkbox.width(), checkbox.sizeHint().width())
                self.assertFalse(card.listbox.geometry().intersects(checkbox.geometry()))
                for button in card.findChildren(QPushButton):
                    self.assertTrue(card.rect().contains(button.geometry()))
                    self.assertFalse(button.geometry().intersects(checkbox.geometry()))

    def test_locked_fields_block_typing_and_paste_but_allow_keyboard_selection(self) -> None:
        clipboard = self.application.clipboard()
        previous_text = clipboard.text()
        try:
            clipboard.setText("Unlisted paste value")
            for field, (source, _) in REFERENCE_FIELDS.items():
                with self.subTest(field=field):
                    self.checkbox(field).setChecked(False)
                    box = self.window.fields[field]
                    box.setCurrentIndex(0)
                    QTest.keyClicks(box, "Unlisted typed value")
                    QTest.keyClick(box, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
                    self.assertIn(box.currentText(), self.store.settings[source])
                    self.assertIsNone(box.lineEdit())
                    box.setCurrentIndex(0)
                    QTest.keyClick(box, Qt.Key.Key_Down)
                    self.assertEqual(box.currentText(), self.store.settings[source][1])
        finally:
            # setMimeData с Python-объектом ломает завершение offscreen Qt на Windows.
            clipboard.setText(previous_text) if previous_text else clipboard.clear()

    def test_disabling_custom_input_discards_unlisted_draft(self) -> None:
        for field, (source, _) in REFERENCE_FIELDS.items():
            with self.subTest(field=field):
                self.checkbox(field).setChecked(True)
                box = self.window.fields[field]
                box.setCurrentText("Произвольное значение")
                self.checkbox(field).setChecked(False)
                self.assertEqual(box.currentText(), "")
                self.assertNotIn("Произвольное значение", self.store.settings[source])
                self.assertEqual(box.findText("Произвольное значение"), -1)

    def test_allowed_custom_values_are_saved_without_expanding_references(self) -> None:
        custom = {
            "anesthesia": "Произвольный наркоз",
            "doctor": "Тестов В. В.",
            "nurse": "Тестова А. А.",
        }
        self.fill_required_fields()
        for field, value in custom.items():
            self.checkbox(field).setChecked(True)
            self.window.fields[field].setCurrentText(value)
        self.window.save_patient()
        saved = self.store.conn.execute("SELECT anesthesia_type, doctor, nurse FROM patients").fetchone()
        self.assertEqual(tuple(saved), tuple(custom.values()))
        self.validation_error.assert_not_called()
        for field, value in custom.items():
            self.assertNotIn(value, self.store.settings[REFERENCE_FIELDS[field][0]])

    def test_save_rejects_injected_unknown_values_for_each_locked_field(self) -> None:
        self.fill_required_fields()
        for field in REFERENCE_FIELDS:
            self.checkbox(field).setChecked(False)
        for field in REFERENCE_FIELDS:
            with self.subTest(field=field):
                data = self.window.form_data()
                data[field] = "Запрещённое значение"
                self.validation_error.reset_mock()
                with patch.object(self.window, "form_data", return_value=data):
                    self.window.save_patient()
                self.validation_error.assert_called_once()
                self.assert_no_cases()

    def test_legacy_values_survive_edit_without_leaking_into_new_cases(self) -> None:
        legacy = ("Старый наркоз", "Старый В. В.", "Старая А. А.")
        cursor = self.store.conn.execute(
            """INSERT INTO patients
               (history_number, full_name, operation_kind, operation_date,
                anesthesia_type, doctor, nurse)
               VALUES ('legacy', 'Старый пациент', 'Плановая', '2026-01-01', ?, ?, ?)""",
            legacy,
        )
        self.store.conn.commit()
        for field in REFERENCE_FIELDS:
            self.checkbox(field).setChecked(False)
        self.select_case(int(cursor.lastrowid))
        self.window.start_edit()
        for field, original in zip(REFERENCE_FIELDS, legacy):
            self.assertEqual(self.window.fields[field].currentText(), original)
        self.window.refresh_references()
        self.window.fields["name"].setText("Изменённое имя")
        self.window.save_patient()
        saved = self.store.conn.execute(
            "SELECT full_name, anesthesia_type, doctor, nurse FROM patients WHERE id=?",
            (cursor.lastrowid,),
        ).fetchone()
        self.assertEqual(tuple(saved), ("Изменённое имя", *legacy))
        self.validation_error.assert_not_called()
        self.assertIsNone(self.window.editing_patient_id)
        for field, original in zip(REFERENCE_FIELDS, legacy):
            box = self.window.fields[field]
            self.assertEqual(box.currentText(), "")
            self.assertEqual(box.findText(original), -1)
            self.assertNotIn(original, self.store.settings[REFERENCE_FIELDS[field][0]])

        self.select_case(int(cursor.lastrowid))
        self.window.start_edit()
        self.window.cancel_edit()
        for field, original in zip(REFERENCE_FIELDS, legacy):
            self.assertEqual(self.window.fields[field].findText(original), -1)

    def test_empty_references_require_anesthesia_but_allow_blank_staff(self) -> None:
        for field, (source, permission) in REFERENCE_FIELDS.items():
            self.store.settings[source] = []
            self.store.settings[permission] = False
        self.window.refresh_references()
        self.fill_required_fields()
        self.window.save_patient()
        self.validation_error.assert_called_once()
        self.assert_no_cases()

        self.store.settings["anesthesia_types"] = ["Общая"]
        self.window.refresh_references()
        self.window.fields["anesthesia"].setCurrentText("Общая")
        self.validation_error.reset_mock()
        self.window.save_patient()
        saved = self.store.conn.execute("SELECT anesthesia_type, doctor, nurse FROM patients").fetchone()
        self.assertEqual(tuple(saved), ("Общая", "", ""))
        self.validation_error.assert_not_called()
        self.assertEqual(self.window.fields["anesthesia"].currentText(), "")

    def test_permissions_persist_in_shared_settings_and_reload(self) -> None:
        expected = {
            "allow_custom_anesthesia": True,
            "allow_custom_doctor": False,
            "allow_custom_nurse": False,
        }
        for field, (_, permission) in REFERENCE_FIELDS.items():
            self.checkbox(field).setChecked(expected[permission])
        saved = json.loads((self.root / "settings.json").read_text(encoding="utf-8"))
        reloaded = DataStore()
        for permission, enabled in expected.items():
            with self.subTest(permission=permission):
                self.assertIs(saved[permission], enabled)
                self.assertIs(reloaded.settings[permission], enabled)

    def test_reconnect_reloads_reference_values_and_permissions(self) -> None:
        self.store.save_settings()
        changed = dict(self.store.settings)
        changed.update(
            anesthesia_types=["Новый вид наркоза"],
            allow_custom_anesthesia=True,
            allow_custom_doctor=False,
            allow_custom_nurse=False,
        )
        (self.root / "settings.json").write_text(json.dumps(changed), encoding="utf-8")
        with patch.object(self.store, "connect", return_value=True):
            self.window.retry_connection()
        self.assertTrue(self.window.fields["anesthesia"].isEditable())
        self.assertTrue(self.checkbox("anesthesia").isChecked())
        self.assertEqual(self.window.fields["anesthesia"].findText("Новый вид наркоза"), 0)
        self.assertEqual(self.window.fields["anesthesia"].findText("Общая"), -1)
        for field in ("doctor", "nurse"):
            self.assertFalse(self.window.fields[field].isEditable())
            self.assertFalse(self.checkbox(field).isChecked())

    def test_switching_database_resets_edit_and_applies_its_settings(self) -> None:
        cursor = self.store.conn.execute(
            """INSERT INTO patients
               (history_number, full_name, operation_kind, operation_date, anesthesia_type)
               VALUES ('old', 'Пациент старой базы', 'Плановая', '2026-01-01', 'Старый наркоз')"""
        )
        self.store.conn.commit()
        self.select_case(int(cursor.lastrowid))
        self.window.start_edit()

        other_root = self.root / "other-journal"
        (other_root / "data").mkdir(parents=True)
        with sqlite3.connect(other_root / "data" / "journal.db") as connection:
            initialize_schema(connection)
            connection.execute(
                """INSERT INTO patients
                   (history_number, full_name, operation_kind, operation_date, anesthesia_type)
                   VALUES ('other', 'Пациент новой базы', 'Плановая', '2026-01-02', 'Новый наркоз')"""
            )
        other_settings = DataStore.validated_settings(
            {
                "anesthesia_types": ["Новый наркоз"],
                "doctors": ["Другой В. В."],
                "nurses": [],
                "allow_custom_anesthesia": True,
                "allow_custom_doctor": False,
                "allow_custom_nurse": False,
            },
            other_root,
        )
        (other_root / "settings.json").write_text(json.dumps(other_settings), encoding="utf-8")
        self.window.path_field.setText(str(other_root))
        self.window.save_database_root()

        self.assertEqual(self.store.database_root, other_root)
        self.assertIsNone(self.window.editing_patient_id)
        for field, (source, permission) in REFERENCE_FIELDS.items():
            with self.subTest(field=field):
                box = self.window.fields[field]
                self.assertEqual(box.currentText(), "")
                self.assertEqual(box.isEditable(), other_settings[permission])
                self.assertEqual(self.checkbox(field).isChecked(), other_settings[permission])
                self.assertEqual(self.store.settings[source], other_settings[source])
        self.assertEqual(self.window.fields["anesthesia"].findText("Старый наркоз"), -1)
        self.assertEqual(self.window.fields["anesthesia"].findText("Новый наркоз"), 0)
        self.validation_error.assert_not_called()

    def test_reconnect_choosing_another_database_keeps_its_settings(self) -> None:
        self.store.save_settings()
        other_root = self.root / "replacement-journal"
        other_root.mkdir()
        other_settings = DataStore.validated_settings(
            {"allow_custom_anesthesia": True, "allow_custom_doctor": False}, other_root
        )
        (other_root / "settings.json").write_text(json.dumps(other_settings), encoding="utf-8")
        original_connect = self.store.connect

        def connect_available_root(value):
            return False if Path(value) == self.root else original_connect(value)

        def choose_other_root():
            self.window.path_field.setText(str(other_root))
            self.window.save_database_root()

        with (
            patch.object(self.store, "connect", side_effect=connect_available_root),
            patch.object(self.window, "choose_database_root", side_effect=choose_other_root),
            patch.object(modern_app, "DatabaseAccessDialog") as dialog,
        ):
            dialog.return_value.exec.return_value = modern_app.DatabaseAccessDialog.CHOOSE_ANOTHER
            self.window.retry_connection()
        self.assertEqual(self.store.database_root, other_root)
        self.assertEqual(self.store.connected_root, other_root)
        self.assertTrue(self.window.fields["anesthesia"].isEditable())
        self.assertFalse(self.window.fields["doctor"].isEditable())

    def test_failed_settings_write_restores_permission_checkbox_and_draft(self) -> None:
        field = "doctor"
        box = self.window.fields[field]
        box.setCurrentText("Несохранённый В. В.")
        with patch.object(self.store, "save_settings", side_effect=OSError("Нет доступа")):
            self.checkbox(field).setChecked(False)
        self.validation_error.assert_called_once()
        self.assertIs(self.store.settings["allow_custom_doctor"], True)
        self.assertTrue(self.checkbox(field).isChecked())
        self.assertTrue(box.isEditable())
        self.assertEqual(box.currentText(), "Несохранённый В. В.")


if __name__ == "__main__":
    unittest.main()
