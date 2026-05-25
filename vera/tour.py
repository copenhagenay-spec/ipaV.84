"""Spotlight tutorial overlay for first-time VERA users."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Qt, QRect, QPoint, QTimer, QObject, QEvent
from PySide6.QtGui import QPainter, QColor, QPainterPath

_STEPS = [
    {
        "title": "Welcome to VERA",
        "body": "Let's walk you through the basics so you're up and running in under a minute.",
        "target": None,
        "tab": None,
    },
    {
        "title": "Push-to-Talk Key",
        "body": "Click Record and press any key, mouse button, or controller button to set your PTT key. This is how you activate VERA.",
        "target": "ptt_edit",
        "tab": 1,
    },
    {
        "title": "Listening Mode",
        "body": "Hold-to-talk keeps VERA active while held down. Toggle switches it on and off. Wake word is fully hands-free.",
        "target": "seg_container",
        "tab": 1,
    },
    {
        "title": "You're all set!",
        "body": 'Try saying "show help" or "what can I say" to see everything VERA can do.',
        "target": None,
        "tab": 0,
    },
]


class _ResizeWatcher(QObject):
    def __init__(self, overlay: "_SpotlightOverlay"):
        super().__init__(overlay.parent())
        self._overlay = overlay

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            self._overlay.setGeometry(obj.rect())
            QTimer.singleShot(0, self._overlay._position_bubble)
        return False


class _SpotlightOverlay(QWidget):
    _PAD = 14
    _BUBBLE_W = 300

    def __init__(self, parent: QWidget, widgets: dict, nav_select):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._widgets = widgets
        self._nav_select = nav_select
        self._target_widget: QWidget | None = None
        self._step = 0
        self._on_complete = None
        self._watcher: _ResizeWatcher | None = None

        self._bubble = QFrame(self)
        self._bubble.setFixedWidth(self._BUBBLE_W)
        self._bubble.setStyleSheet("""
            QFrame {
                background-color: #1c1c1c;
                border: 1px solid #383838;
                border-radius: 12px;
            }
        """)

        vl = QVBoxLayout(self._bubble)
        vl.setContentsMargins(20, 18, 20, 14)
        vl.setSpacing(6)

        self._title_lbl = QLabel()
        self._title_lbl.setStyleSheet(
            "color: #ffffff; font-size: 14px; font-weight: bold;"
            " background: transparent; border: none;"
        )
        self._title_lbl.setWordWrap(True)

        self._body_lbl = QLabel()
        self._body_lbl.setStyleSheet(
            "color: #aaaaaa; font-size: 12px; background: transparent; border: none;"
        )
        self._body_lbl.setWordWrap(True)
        self._body_lbl.setFixedWidth(self._BUBBLE_W - 40)

        self._step_lbl = QLabel()
        self._step_lbl.setStyleSheet(
            "color: #555555; font-size: 10px; background: transparent; border: none;"
        )

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 6, 0, 0)
        btn_row.setSpacing(8)

        self._skip_btn = QPushButton("Skip tour")
        self._skip_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #555555;
                border: none; font-size: 11px; padding: 4px 0px;
            }
            QPushButton:hover { color: #888888; }
        """)
        self._skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skip_btn.clicked.connect(self._finish)

        self._next_btn = QPushButton("Next →")
        self._next_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; color: #ffffff;
                border: none; border-radius: 6px;
                font-size: 12px; font-weight: bold;
                padding: 7px 20px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._advance)

        btn_row.addWidget(self._skip_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._next_btn)

        vl.addWidget(self._title_lbl)
        vl.addWidget(self._body_lbl)
        vl.addWidget(self._step_lbl)
        vl.addLayout(btn_row)

    # ------------------------------------------------------------------

    def start(self, on_complete):
        self._on_complete = on_complete
        self._step = 0
        self._watcher = _ResizeWatcher(self)
        self.parent().installEventFilter(self._watcher)
        self._show_step()
        self.show()
        self.raise_()

    def _show_step(self):
        step = _STEPS[self._step]
        self._title_lbl.setText(step["title"])
        self._body_lbl.setText(step["body"])
        self._step_lbl.setText(f"{self._step + 1} of {len(_STEPS)}")

        is_last = self._step == len(_STEPS) - 1
        self._next_btn.setText("Done" if is_last else "Next →")
        self._skip_btn.setVisible(not is_last)

        if step["tab"] is not None and self._nav_select:
            self._nav_select(step["tab"])

        target_name = step.get("target")
        self._target_widget = self._widgets.get(target_name) if target_name else None

        self.update()
        QTimer.singleShot(60, self._position_bubble)

    def _get_spotlight_rect(self) -> QRect | None:
        tw = self._target_widget
        if tw is None or not tw.isVisible():
            return None
        pos = tw.mapTo(self.parent(), QPoint(0, 0))
        p = self._PAD
        return QRect(pos.x() - p, pos.y() - p, tw.width() + 2 * p, tw.height() + 2 * p)

    def _position_bubble(self):
        self._bubble.adjustSize()
        bw = self._bubble.width()
        bh = self._bubble.height()
        ow, oh = self.width(), self.height()
        spot = self._get_spotlight_rect()

        if spot is None:
            x = (ow - bw) // 2
            y = (oh - bh) // 2
        else:
            gap = 18
            x = spot.left() + (spot.width() - bw) // 2
            x = max(12, min(x, ow - bw - 12))
            y = spot.bottom() + gap
            if y + bh > oh - 12:
                y = spot.top() - bh - gap
            if y < 12:
                y = (oh - bh) // 2

        self._bubble.move(x, y)
        self.update()

    def _advance(self):
        if self._step >= len(_STEPS) - 1:
            self._finish()
        else:
            self._step += 1
            self._show_step()

    def _finish(self):
        if self._watcher and self.parent():
            self.parent().removeEventFilter(self._watcher)
        self.hide()
        self.deleteLater()
        if self._on_complete:
            self._on_complete()

    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        full = QPainterPath()
        full.addRect(0, 0, self.width(), self.height())

        spot = self._get_spotlight_rect()
        if spot is not None:
            cutout = QPainterPath()
            cutout.addRoundedRect(
                float(spot.x()), float(spot.y()),
                float(spot.width()), float(spot.height()),
                10.0, 10.0,
            )
            full = full.subtracted(cutout)

        painter.fillPath(full, QColor(0, 0, 0, 175))

        if spot is not None:
            from PySide6.QtGui import QPen
            pen = QPen(QColor(37, 99, 235, 210), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(spot, 10, 10)

        painter.end()

    def mousePressEvent(self, event):
        event.accept()


# ---------------------------------------------------------------------------

def run_tour(window: QWidget, widgets: dict, nav_select, on_complete):
    overlay = _SpotlightOverlay(window, widgets, nav_select)
    overlay.start(on_complete)
