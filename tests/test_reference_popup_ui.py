from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QFont, QFontDatabase, QHelpEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem, QToolTip, QVBoxLayout, QWidget

from modern_app import QSS, ReferenceComboBox


class ReferencePopupUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        if not QFontDatabase.families():
            font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf"
            if not font.is_file() or QFontDatabase.addApplicationFont(str(font)) < 0:
                raise unittest.SkipTest("Нет шрифта для проверки выпадающего списка")

    def setUp(self) -> None:
        self.host = QWidget()
        self.host.setStyleSheet(QSS)
        self.host.setFont(QFont("Segoe UI", 10))
        self.host.resize(355, 180)
        self.host.move(100, 100)
        layout = QVBoxLayout(self.host)
        self.box = ReferenceComboBox()
        self.box.setInsertPolicy(ReferenceComboBox.InsertPolicy.NoInsert)
        self.box.addItems(["Эпидуральная анестезия (ЭА)", "ТВВА + ИВЛ"])
        layout.addWidget(self.box)
        layout.addStretch()
        self.host.show()
        self.application.processEvents()
        self.addCleanup(self.host.close)
        self.addCleanup(self.box.hidePopup)

    def test_short_popup_has_same_size_and_no_blank_bands_in_both_input_modes(self) -> None:
        sizes = []
        for editable in (False, True, False):
            with self.subTest(editable=editable):
                self.box.setEditable(editable)
                self.box.showPopup()
                self.application.processEvents()
                view = self.box.view()
                self.assertEqual(view.width(), self.box.width())
                self.assertEqual(view.verticalScrollBar().maximum(), 0)
                self.assertEqual(view.viewport().height(), sum(view.sizeHintForRow(i) for i in range(self.box.count())))
                panel_top = view.mapToGlobal(QPoint())
                field_bottom = self.box.mapToGlobal(QPoint(0, self.box.height()))
                self.assertEqual(panel_top.x(), field_bottom.x())
                self.assertEqual(panel_top.y() - field_bottom.y(), 4)
                image = view.grab().toImage()
                # Между рамкой и строками остаётся только единый серый фон панели.
                self.assertEqual(image.pixelColor(image.width() // 2, 3).name(), "#efefef")
                self.assertEqual(image.pixelColor(image.width() // 2, image.height() - 4).name(), "#efefef")
                sizes.append(view.size())
                self.box.hidePopup()
        self.assertEqual(sizes[0], sizes[1])
        self.assertEqual(sizes[0], sizes[2])

    def test_mouse_selection_and_keyboard_accept_cancel_keep_native_behavior(self) -> None:
        for editable in (False, True):
            with self.subTest(editable=editable):
                self.box.setEditable(editable)
                self.box.setCurrentIndex(0)
                self.box.showPopup()
                self.application.processEvents()
                view = self.box.view()
                second = view.model().index(1, 0)
                QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=view.visualRect(second).center())
                self.application.processEvents()
                self.assertEqual(self.box.currentIndex(), 1)
                self.assertFalse(view.window().isVisible())

                self.box.showPopup()
                QTest.keyClick(view, Qt.Key.Key_Up)
                QTest.keyClick(view, Qt.Key.Key_Escape)
                self.assertEqual(self.box.currentIndex(), 1)
                self.assertFalse(view.window().isVisible())

                self.box.showPopup()
                QTest.keyClick(view, Qt.Key.Key_Up)
                QTest.keyClick(view, Qt.Key.Key_Return)
                self.assertEqual(self.box.currentIndex(), 0)
                self.assertFalse(view.window().isVisible())

    def test_long_list_scrolls_and_opens_above_near_screen_bottom(self) -> None:
        self.box.clear()
        self.box.addItems([f"Значение {i}" for i in range(40)])
        self.box.setCurrentIndex(35)
        screen = self.host.screen().availableGeometry()
        self.host.move(screen.left() + 100, screen.bottom() - self.host.height())
        self.application.processEvents()
        self.box.showPopup()
        self.application.processEvents()
        view = self.box.view()
        popup = view.window()
        self.assertTrue(screen.contains(popup.geometry()))
        self.assertEqual(view.mapToGlobal(QPoint(0, view.height())).y(), self.box.mapToGlobal(QPoint()).y() - 4)
        self.assertGreater(view.verticalScrollBar().maximum(), 0)
        self.assertTrue(view.viewport().rect().contains(view.visualRect(view.currentIndex())))
        QTest.keyClick(view, Qt.Key.Key_End)
        QTest.keyClick(view, Qt.Key.Key_Return)
        self.assertEqual(self.box.currentIndex(), 39)

    def test_hiding_during_animation_allows_clean_reopen(self) -> None:
        effect = Qt.UIEffect.UI_AnimateCombo
        previous = QApplication.isEffectEnabled(effect)
        self.addCleanup(QApplication.setEffectEnabled, effect, previous)
        # Offscreen Qt принудительно отключает UI effects из-за глубины экрана.
        with patch.object(QApplication, "isEffectEnabled", return_value=True):
            self.box.showPopup()
            self.box.hidePopup()
            self.assertEqual(self.box.view().window().windowOpacity(), 1)
            self.box.showPopup()
            QTest.qWait(180)
        popup = self.box.view().window()
        self.assertTrue(popup.isVisible())
        self.assertEqual(popup.windowOpacity(), 1)
        self.assertEqual(self.box.currentIndex(), 0)

    def test_long_names_have_full_tooltip_and_historical_hint_is_preserved(self) -> None:
        text = "Длинное название вида анестезии, которое целиком не помещается в строку списка"
        self.box.setItemText(0, text)
        self.box.showPopup()
        self.application.processEvents()
        view = self.box.view()
        index = view.model().index(0, 0)
        option = QStyleOptionViewItem()
        view.initViewItemOption(option)
        option.rect = view.visualRect(index)
        point = option.rect.center()
        event = QHelpEvent(QEvent.Type.ToolTip, point, view.viewport().mapToGlobal(point))
        delegate = self.box.itemDelegate()
        self.addCleanup(QToolTip.hideText)
        self.assertTrue(delegate.helpEvent(event, view, option, index))
        self.assertEqual(QToolTip.text(), text)
        hint = "Сохранённое значение этой записи; отсутствует в справочнике."
        self.box.setItemData(0, hint, Qt.ItemDataRole.ToolTipRole)
        self.assertTrue(delegate.helpEvent(event, view, option, index))
        self.assertEqual(QToolTip.text(), hint)


if __name__ == "__main__":
    unittest.main()
