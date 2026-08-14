# -*- coding: utf-8 -*-
"""
Taller — Inventario · App de escritorio (versión editorial PyQt6)

Rediseño minimalista editorial con Qt6.
- Dos temas: Light (Papel & grafito) y Dark (Noche editorial) con toggle.
- Tipografía serif Georgia para títulos y datos destacados, Arial para metadata,
  Consolas para eyebrows y etiquetas en mayúsculas.
- Bordes hairline (1px), sombras reales (QGraphicsDropShadowEffect),
  micro-animaciones con QPropertyAnimation, separaciones tipográficas.
"""

import sys
import requests
import threading
import time
import webbrowser
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget,
    QFrame, QScrollArea, QTextEdit, QMessageBox, QGraphicsDropShadowEffect,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor

from config import PUBLIC_URL, ADMIN_KEY

# ── Paletas editoriales ─────────────────────────────────────────────────────
# Cada tema es un dict con todas las variables de color que usa la app.
# Para agregar un tema nuevo, copiar uno existente y cambiar los valores.

THEMES = {
    "light": {
        "name":          "light",
        "label":         "LIGHT",
        "paper":         "#FAFAF7",
        "paper_warm":    "#F4F1EA",
        "paper_deep":    "#EFEBE2",
        "ink":           "#2C2C2C",
        "ink_soft":      "#4A4A48",
        "ink_mute":      "#8A8A86",
        "ink_faint":     "#B8B6AE",
        "ink_blue":      "#1E3A5F",
        "ink_blue_2":    "#2A4F7C",
        "oxblood":       "#8C2F2F",
        "oxblood_deep":  "#6E2424",
        "moss":          "#3F5B3A",
        "hairline":      "#DCDAD2",
        "hairline_2":    "#E8E6DE",
        # color del texto sobre fondo oscuro (botón primario, etc.)
        "on_ink":        "#FAFAF7",
        # color del texto sobre acentos (azul tinta, oxblood, moss)
        "on_accent":     "#FAFAF7",
        # sombra base (RGBA)
        "shadow":        "rgba(44, 44, 44, 0.18)",
        "shadow_strong": "rgba(44, 44, 44, 0.35)",
    },
    "dark": {
        "name":          "dark",
        "label":         "DARK",
        "paper":         "#0E0E0E",
        "paper_warm":    "#1A1A1A",
        "paper_deep":    "#242424",
        "ink":           "#EDEAE3",
        "ink_soft":      "#C8C5BE",
        "ink_mute":      "#7A7A75",
        "ink_faint":     "#4A4A48",
        "ink_blue":      "#C9A961",
        "ink_blue_2":    "#B5954A",
        "oxblood":       "#D65555",
        "oxblood_deep":  "#B33838",
        "moss":          "#7AAB6F",
        "hairline":      "#2A2A2A",
        "hairline_2":    "#1F1F1F",
        "on_ink":        "#0E0E0E",
        "on_accent":     "#0E0E0E",
        "shadow":        "rgba(0, 0, 0, 0.45)",
        "shadow_strong": "rgba(0, 0, 0, 0.7)",
    },
}

# Tema activo (se cambia con self._apply_theme)
_theme = THEMES["light"]

HEADERS = {"X-Admin-Key": ADMIN_KEY}

# ── Tipografías ─────────────────────────────────────────────────────────────
F_SERIF = "Georgia"
F_SANS  = "Arial"
F_MONO  = "Consolas"


def font_serif(size, weight=QFont.Weight.Normal, italic=False):
    f = QFont(F_SERIF, size)
    f.setWeight(weight)
    f.setItalic(italic)
    return f


def font_sans(size, weight=QFont.Weight.Normal):
    f = QFont(F_SANS, size)
    f.setWeight(weight)
    return f


def font_mono(size, weight=QFont.Weight.Normal):
    f = QFont(F_MONO, size)
    f.setWeight(weight)
    return f


def build_qss(t: dict) -> str:
    """Genera el QSS completo para un tema dado."""
    return f"""
* {{
    font-family: "{F_SANS}", sans-serif;
    color: {t['ink']};
    outline: none;
}}

QMainWindow, QWidget {{
    background-color: {t['paper']};
}}

QLabel {{
    background: transparent;
    color: {t['ink']};
}}

QLabel#eyebrow {{
    font-family: "{F_MONO}", monospace;
    font-size: 9px;
    color: {t['ink_mute']};
    font-weight: 600;
    letter-spacing: 2px;
}}

QLabel#brand {{
    font-family: "{F_SERIF}", serif;
    font-size: 26px;
    color: {t['ink']};
    font-weight: 500;
}}

QLabel#vol {{
    font-family: "{F_MONO}", monospace;
    font-size: 9px;
    color: {t['ink_mute']};
    font-weight: 600;
    letter-spacing: 2px;
}}

QLabel#date {{
    font-family: "{F_SERIF}", serif;
    font-size: 12px;
    color: {t['ink_soft']};
    font-style: italic;
}}

QLabel#h1 {{
    font-family: "{F_SERIF}", serif;
    font-size: 22px;
    color: {t['ink']};
    font-weight: 500;
}}

QLabel#caption {{
    font-family: "{F_SERIF}", serif;
    font-size: 12px;
    color: {t['ink_mute']};
    font-style: italic;
}}

QLabel#section-num {{
    font-family: "{F_SERIF}", serif;
    font-size: 56px;
    color: {t['hairline']};
    font-weight: 300;
}}

QLabel#field-label {{
    font-family: "{F_MONO}", monospace;
    font-size: 9px;
    color: {t['ink_mute']};
    font-weight: 600;
    letter-spacing: 1.5px;
}}

QLabel#table-header {{
    font-family: "{F_MONO}", monospace;
    font-size: 9px;
    color: {t['ink_mute']};
    font-weight: 600;
    letter-spacing: 1.5px;
}}

QLabel#worker-num {{
    font-family: "{F_SERIF}", serif;
    font-size: 22px;
    color: {t['ink_faint']};
    font-weight: 400;
}}

QLabel#worker-name {{
    font-family: "{F_SERIF}", serif;
    font-size: 16px;
    color: {t['ink']};
    font-weight: 500;
}}

QLabel#empty {{
    font-family: "{F_SERIF}", serif;
    font-size: 14px;
    color: {t['ink_faint']};
    font-style: italic;
}}

QLabel#url-value {{
    font-family: "{F_SERIF}", serif;
    font-size: 15px;
    color: {t['ink']};
    font-weight: 500;
}}

QFrame#hairline {{
    background-color: {t['hairline']};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

QFrame#ink-hairline {{
    background-color: {t['ink']};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

QFrame#card {{
    background-color: {t['paper']};
    border: 1px solid {t['hairline']};
}}

QFrame#card-warm {{
    background-color: {t['paper_warm']};
    border: 1px solid {t['hairline']};
}}

QFrame#worker-row {{
    background-color: {t['paper']};
    border: none;
    border-bottom: 1px solid {t['hairline_2']};
}}

QFrame#toast {{
    background-color: {t['paper']};
    border: 1px solid {t['ink_blue']};
}}

QFrame#toast-error {{
    background-color: {t['paper']};
    border: 1px solid {t['oxblood']};
}}

/* ── Inputs ── */
QLineEdit {{
    background: transparent;
    border: none;
    border-bottom: 1px solid {t['hairline']};
    padding: 10px 4px 10px 4px;
    font-size: 15px;
    color: {t['ink']};
    font-family: "{F_SERIF}", serif;
    selection-background-color: {t['paper_deep']};
    selection-color: {t['ink_blue']};
    min-height: 24px;
}}
QLineEdit:focus {{
    border-bottom: 1px solid {t['ink_blue']};
}}
QLineEdit::placeholder {{
    color: {t['ink_faint']};
    font-style: italic;
}}

QComboBox {{
    background: transparent;
    border: none;
    border-bottom: 1px solid {t['hairline']};
    padding: 10px 4px 10px 4px;
    font-size: 15px;
    color: {t['ink']};
    font-family: "{F_SERIF}", serif;
    min-height: 24px;
    min-width: 160px;
}}
QComboBox:focus {{
    border-bottom: 1px solid {t['ink_blue']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
    background: transparent;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {t['ink_mute']};
    margin-right: 8px;
    width: 0;
    height: 0;
}}
QComboBox QAbstractItemView {{
    background: {t['paper']};
    border: 1px solid {t['hairline']};
    selection-background-color: {t['paper_warm']};
    selection-color: {t['ink_blue']};
    outline: none;
    padding: 6px;
    font-family: "{F_SERIF}", serif;
    font-size: 14px;
    min-width: 180px;
}}

/* ── Buttons (3 variantes) ── */
QPushButton {{
    background-color: transparent;
    color: {t['ink']};
    border: 1px solid {t['hairline']};
    padding: 12px 22px;
    font-family: "{F_MONO}", monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.2px;
}}
QPushButton:hover {{
    background-color: {t['paper_warm']};
    border-color: {t['ink']};
    color: {t['ink']};
}}
QPushButton:pressed {{
    background-color: {t['paper_deep']};
    color: {t['ink']};
}}

QPushButton#primary {{
    background-color: {t['ink']};
    color: {t['on_ink']};
    border: 1px solid {t['ink']};
}}
QPushButton#primary:hover {{
    background-color: {t['ink_blue']};
    border-color: {t['ink_blue']};
    color: {t['on_accent']};
}}
QPushButton#primary:pressed {{
    background-color: {t['ink_blue_2']};
    color: {t['on_accent']};
}}

QPushButton#danger {{
    background-color: transparent;
    color: {t['oxblood']};
    border: 1px solid {t['oxblood']};
}}
QPushButton#danger:hover {{
    background-color: {t['oxblood']};
    color: {t['on_accent']};
    border-color: {t['oxblood']};
}}
QPushButton#danger:pressed {{
    background-color: {t['oxblood_deep']};
    color: {t['on_accent']};
}}

QPushButton#tab {{
    background: transparent;
    border: none;
    color: {t['ink_faint']};
    padding: 14px 0;
    font-family: "{F_MONO}", monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-align: left;
}}
QPushButton#tab:hover {{
    color: {t['ink_soft']};
    background: transparent;
    border: none;
}}
QPushButton#tab[active="true"] {{
    color: {t['ink']};
    background: transparent;
    border: none;
}}

/* ── Theme toggle ── */
QPushButton#theme-toggle {{
    background: transparent;
    border: 1px solid {t['hairline']};
    color: {t['ink']};
    padding: 8px 14px;
    font-family: "{F_MONO}", monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.5px;
    min-width: 80px;
}}
QPushButton#theme-toggle:hover {{
    background: {t['paper_warm']};
    border-color: {t['ink']};
    color: {t['ink']};
}}

/* ── Tables ── */
QTableWidget {{
    background: {t['paper']};
    border: none;
    gridline-color: transparent;
    color: {t['ink']};
    font-size: 14px;
    font-family: "{F_SERIF}", serif;
    selection-background-color: {t['paper_warm']};
    selection-color: {t['ink_blue']};
    outline: none;
    show-decoration-selected: false;
}}
QTableWidget::item {{
    padding: 12px 10px;
    border: none;
    border-bottom: 1px solid {t['hairline_2']};
    background: {t['paper']};
}}
QTableWidget::item:hover {{
    background: {t['paper_warm']};
}}
QTableWidget::item:selected {{
    background: {t['paper_warm']};
    color: {t['ink_blue']};
}}
QHeaderView::section {{
    background: {t['paper']};
    color: {t['ink_mute']};
    font-family: "{F_MONO}", monospace;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    padding: 10px 10px;
    border: none;
    border-bottom: 1px solid {t['hairline']};
}}
QTableCornerButton::section {{
    background: {t['paper']};
    border: none;
}}

/* ── Textarea ── */
QTextEdit {{
    background: {t['paper_warm']};
    border: 1px solid {t['hairline']};
    color: {t['ink']};
    font-size: 14px;
    padding: 16px;
    font-family: "{F_SERIF}", serif;
    selection-background-color: {t['paper_deep']};
    selection-color: {t['ink_blue']};
}}
QTextEdit:focus {{
    border: 1px solid {t['ink_blue']};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {t['hairline']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['ink_faint']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {t['hairline']};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {t['ink_faint']};
}}
"""


# ── Helpers ─────────────────────────────────────────────────────────────────
def make_shadow(blur=24, y=8, color=QColor(44, 44, 44, 45)):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur)
    s.setOffset(0, y)
    s.setColor(color)
    return s


def hairline(parent_layout, color=None):
    """Agrega un separador hairline de 1px al layout."""
    line = QFrame()
    line.setObjectName("hairline")
    if color and color != _theme["hairline"]:
        line.setStyleSheet(f"background-color: {color}; border: none; max-height: 1px; min-height: 1px;")
    line.setFixedHeight(1)
    parent_layout.addWidget(line)
    return line


class TabButton(QPushButton):
    """Botón de pestaña con estado activo basado en propiedad QSS."""

    def __init__(self, num, label, parent=None):
        super().__init__(parent)
        self.num = num
        self.label_text = label
        self.setText(f"{num}    {label.upper()}")
        self.setObjectName("tab")
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(False)
        self.setMinimumHeight(44)

    def set_active(self, active: bool):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class Toast(QFrame):
    """Notificación flotante con sombra suave, auto-cierre."""

    def __init__(self, parent, message, error=False):
        super().__init__(parent)
        self.setObjectName("toast-error" if error else "toast")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool |
                            Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        t = _theme
        # sombra
        shadow_color = QColor(0, 0, 0, 100) if t["name"] == "dark" else QColor(44, 44, 44, 60)
        self.setGraphicsEffect(make_shadow(blur=32, y=10, color=shadow_color))

        # layout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 16)
        lay.setSpacing(4)

        eyebrow = QLabel("NUEVO MOVIMIENTO" if not error else "ERROR")
        eyebrow.setObjectName("eyebrow")
        eyebrow.setStyleSheet(f"color: {t['oxblood'] if error else t['ink_blue']};")
        lay.addWidget(eyebrow)

        msg = QLabel(message)
        msg.setFont(font_serif(13, italic=True))
        msg.setWordWrap(True)
        msg.setMaximumWidth(380)
        lay.addWidget(msg)

        self.resize(420, 80)

    def pop_at(self, parent_widget):
        parent_rect = parent_widget.rect()
        global_pos = parent_widget.mapToGlobal(QPoint(0, 0))
        target_x = global_pos.x() + parent_rect.width() - self.width() - 32
        target_y = global_pos.y() + parent_rect.height() - self.height() - 32

        start_x = target_x + 40
        self.move(start_x, target_y)
        self.show()

        self.anim = QPropertyAnimation(self, b"pos", self)
        self.anim.setDuration(380)
        self.anim.setStartValue(QPoint(start_x, target_y))
        self.anim.setEndValue(QPoint(target_x, target_y))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

        QTimer.singleShot(6000, self.close_with_fade)

    def close_with_fade(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity", self)
        self.anim.setDuration(300)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.close)
        self.anim.start()


class TallerApp(QMainWindow):
    new_movements_signal = pyqtSignal(list)

    def __init__(self, theme_name="light"):
        global _theme
        _theme = THEMES[theme_name]
        self.theme_name = theme_name

        super().__init__()
        self.setWindowTitle("Taller · Inventario")
        self.resize(1200, 800)
        self.setMinimumSize(1024, 680)

        self._last_movement_id = 0
        self._active_tab_idx = -1

        self.new_movements_signal.connect(self._handle_new_movements)

        central = QWidget()
        central.setStyleSheet("")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(0)

        self._build_masthead(root)
        self._build_nav(root)

        # Stack de contenido
        self.stack = QStackedWidget()
        root.addWidget(self.stack, stretch=1)

        self._build_inventory_tab()
        self._build_workers_tab()
        self._build_movements_tab()
        self._build_server_tab()

        self._switch_tab(0)
        self.refresh_all()
        self._start_polling()

    # ── TEMA ─────────────────────────────────────────────────────────────────
    def _toggle_theme(self):
        new_name = "dark" if self.theme_name == "light" else "light"
        # Rebuild completo para que todos los widgets inline se actualicen
        self._rebuild_with_theme(new_name)

    def _rebuild_with_theme(self, theme_name):
        """Reconstruye toda la UI con un tema nuevo. Más simple que parchear widgets inline."""
        global _theme
        _theme = THEMES[theme_name]
        self.theme_name = theme_name

        # Tomar referencia al central widget viejo y reemplazarlo
        old_central = self.centralWidget()

        # Crear nuevo central
        new_central = QWidget()
        new_central.setStyleSheet(f"background-color: {_theme['paper']};")
        self.setCentralWidget(new_central)

        root = QVBoxLayout(new_central)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(0)

        # Reset estado
        self._active_tab_idx = -1
        self.tab_buttons = []
        self.stack = None

        self._build_masthead(root)
        self._build_nav(root)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, stretch=1)

        self._build_inventory_tab()
        self._build_workers_tab()
        self._build_movements_tab()
        self._build_server_tab()

        # Eliminar el central viejo y todos sus hijos
        old_central.setParent(None)
        old_central.deleteLater()

        # Aplicar QSS global + palette
        app = QApplication.instance()
        app.setStyleSheet(build_qss(_theme))
        pal = app.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(_theme["paper"]))
        pal.setColor(QPalette.ColorRole.Base, QColor(_theme["paper"]))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(_theme["paper_warm"]))
        pal.setColor(QPalette.ColorRole.Text, QColor(_theme["ink"]))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(_theme["ink"]))
        pal.setColor(QPalette.ColorRole.Button, QColor(_theme["paper"]))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(_theme["ink"]))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(_theme["paper_warm"]))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(_theme["ink_blue"]))
        app.setPalette(pal)

        # Forzar re-aplicación del estilo a todos los widgets
        # (necesario porque el QSS se aplica después de crear los widgets)
        for w in app.allWidgets():
            w.style().unpolish(w)
            w.style().polish(w)

        # Texto del botón toggle (que se acaba de recrear en _build_masthead)
        if hasattr(self, "theme_toggle_btn"):
            new_label = "DARK" if theme_name == "light" else "LIGHT"
            self.theme_toggle_btn.setText(f"◐  {new_label}")

        # Switch al tab 0 y refrescar datos
        self._switch_tab(0)
        self.refresh_all()

    def _apply_theme(self, theme_name):
        """Alias legacy — usa rebuild."""
        self._rebuild_with_theme(theme_name)

    # ── MASTHEAD ────────────────────────────────────────────────────────────
    def _build_masthead(self, parent_layout):
        m = QFrame()
        m.setStyleSheet("")
        lay = QHBoxLayout(m)
        lay.setContentsMargins(0, 0, 0, 12)
        lay.setSpacing(0)

        # Columna izquierda
        left = QVBoxLayout()
        left.setSpacing(2)
        eyebrow = QLabel("TALLER · INVENTARIO")
        eyebrow.setObjectName("eyebrow")
        left.addWidget(eyebrow)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(6)
        b1 = QLabel("Registro")
        b1.setObjectName("brand")
        brand_row.addWidget(b1)
        b2 = QLabel("editorial")
        b2.setObjectName("brand")
        b2.setStyleSheet(
            f"color: {_theme['ink_blue']}; font-style: italic; font-weight: 400; "
            f"font-family: '{F_SERIF}'; font-size: 26px; background: transparent;"
        )
        brand_row.addWidget(b2)
        brand_row.addStretch()
        left.addLayout(brand_row)

        # Columna derecha
        right = QVBoxLayout()
        right.setSpacing(6)
        right.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Fila superior: vol + theme toggle
        top_right = QHBoxLayout()
        top_right.setSpacing(12)
        top_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        vol = QLabel("VOL. I · EDICIÓN CONTINUA")
        vol.setObjectName("vol")
        top_right.addWidget(vol)

        self.theme_toggle_btn = QPushButton("◐  DARK")
        self.theme_toggle_btn.setObjectName("theme-toggle")
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)
        top_right.addWidget(self.theme_toggle_btn)
        right.addLayout(top_right)

        # Fila inferior: fecha
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
                 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        now = datetime.now()
        today = f"{now.day} de {meses[now.month-1]} · {now.year}"
        date = QLabel(today)
        date.setObjectName("date")
        date.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(date)

        lay.addLayout(left, stretch=1)
        lay.addLayout(right, stretch=0)

        parent_layout.addWidget(m)
        hairline(parent_layout, color=_theme["ink"])

    # ── NAVEGACIÓN ──────────────────────────────────────────────────────────
    def _build_nav(self, parent_layout):
        nav = QFrame()
        nav.setStyleSheet("")
        nav.setFixedHeight(48)
        lay = QHBoxLayout(nav)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(28)

        tabs = [
            ("01", "Inventario"),
            ("02", "Trabajadores"),
            ("03", "Movimientos"),
            ("04", "Servidor · QR"),
        ]
        self.tab_buttons = []
        for i, (num, label) in enumerate(tabs):
            btn = TabButton(num, label)
            btn.clicked.connect(lambda checked=False, idx=i: self._switch_tab(idx))
            lay.addWidget(btn, stretch=0)
            self.tab_buttons.append(btn)
        lay.addStretch()

        parent_layout.addWidget(nav)

        self.nav_underline = QFrame()
        self.nav_underline.setObjectName("hairline")
        self.nav_underline.setFixedHeight(1)
        parent_layout.addWidget(self.nav_underline)

    def _switch_tab(self, idx):
        if self._active_tab_idx == idx:
            return
        self._active_tab_idx = idx

        for i, btn in enumerate(self.tab_buttons):
            btn.set_active(i == idx)

        self.stack.setCurrentIndex(idx)

        if idx == 0: self.refresh_inventory()
        elif idx == 1: self.refresh_workers()
        elif idx == 2: self.refresh_movements()
        elif idx == 3: self.refresh_notifications()

        # fade-in sutil
        w = self.stack.currentWidget()
        if w:
            self._fade_anim = QPropertyAnimation(w, b"windowOpacity", w)
            self._fade_anim.setDuration(220)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._fade_anim.start()

    # ── Helpers visuales ────────────────────────────────────────────────────
    def _section_header(self, num, title_parts, subtitle):
        head = QFrame()
        head.setStyleSheet("")
        lay = QHBoxLayout(head)
        lay.setContentsMargins(0, 20, 0, 16)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        num_label = QLabel(num)
        num_label.setObjectName("section-num")
        num_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(num_label, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        for i, part in enumerate(title_parts):
            t = QLabel(part)
            t.setObjectName("h1")
            if i > 0:
                t.setStyleSheet(
                    f"color: {_theme['ink_blue']}; font-style: italic; font-weight: 400; "
                    f"font-family: '{F_SERIF}'; font-size: 22px; background: transparent;"
                )
            title_row.addWidget(t)
        txt.addLayout(title_row)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("caption")
            txt.addWidget(sub)

        lay.addLayout(txt, stretch=1)
        return head

    def _field_label(self, text):
        lbl = QLabel(text.upper())
        lbl.setObjectName("field-label")
        return lbl

    def _editorial_entry(self, placeholder=""):
        e = QLineEdit()
        e.setPlaceholderText(placeholder)
        e.setMinimumHeight(44)  # ANTES 34 — ahora más alto
        e.setMinimumWidth(140)  # ancho mínimo cómodo
        return e

    def _primary_button(self, text, callback):
        b = QPushButton(text.upper())
        b.setObjectName("primary")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setMinimumHeight(40)
        # Forzar el estilo inline — QSS a veces no aplica background en botones
        # dentro de QStackedWidget después de un rebuild de tema.
        t = _theme
        b.setStyleSheet(f"""
            QPushButton#primary {{
                background-color: {t['ink']};
                color: {t['on_ink']};
                border: 1px solid {t['ink']};
                padding: 12px 22px;
                font-family: '{F_MONO}', monospace;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.2px;
            }}
            QPushButton#primary:hover {{
                background-color: {t['ink_blue']};
                border-color: {t['ink_blue']};
                color: {t['on_accent']};
            }}
            QPushButton#primary:pressed {{
                background-color: {t['ink_blue_2']};
                color: {t['on_accent']};
            }}
        """)
        b.clicked.connect(callback)
        return b

    def _secondary_button(self, text, callback):
        b = QPushButton(text.upper())
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setMinimumHeight(40)
        t = _theme
        b.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {t['ink']};
                border: 1px solid {t['hairline']};
                padding: 12px 22px;
                font-family: '{F_MONO}', monospace;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.2px;
            }}
            QPushButton:hover {{
                background-color: {t['paper_warm']};
                border-color: {t['ink']};
                color: {t['ink']};
            }}
            QPushButton:pressed {{
                background-color: {t['paper_deep']};
                color: {t['ink']};
            }}
        """)
        b.clicked.connect(callback)
        return b

    def _danger_button(self, text, callback):
        b = QPushButton(text.upper())
        b.setObjectName("danger")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setMinimumHeight(40)
        t = _theme
        b.setStyleSheet(f"""
            QPushButton#danger {{
                background-color: transparent;
                color: {t['oxblood']};
                border: 1px solid {t['oxblood']};
                padding: 12px 22px;
                font-family: '{F_MONO}', monospace;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1.2px;
            }}
            QPushButton#danger:hover {{
                background-color: {t['oxblood']};
                color: {t['on_accent']};
                border-color: {t['oxblood']};
            }}
            QPushButton#danger:pressed {{
                background-color: {t['oxblood_deep']};
                color: {t['on_accent']};
            }}
        """)
        b.clicked.connect(callback)
        return b

    # ── PESTAÑA INVENTARIO ─────────────────────────────────────────────────
    def _build_inventory_tab(self):
        page = QWidget()
        page.setStyleSheet("")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._section_header("01", ["Inventario del taller"], "Herramientas y materiales disponibles para retiro."))

        # Form
        form = QFrame()
        form.setStyleSheet("")
        form_lay = QGridLayout(form)
        form_lay.setContentsMargins(0, 0, 0, 16)
        form_lay.setHorizontalSpacing(24)
        form_lay.setVerticalSpacing(6)

        # Row 0 — labels
        form_lay.addWidget(self._field_label("Nombre"), 0, 0)
        form_lay.addWidget(self._field_label("Categoría"), 0, 1)
        form_lay.addWidget(self._field_label("Cantidad"), 0, 2)
        form_lay.addWidget(self._field_label("Unidad"), 0, 3)

        # Row 1 — inputs (más anchos)
        self.in_name = self._editorial_entry("Taladro Bosch GSB 13")
        self.in_name.setMinimumWidth(220)
        self.in_category = QComboBox()
        self.in_category.addItems(["herramienta", "material"])
        self.in_category.setMinimumHeight(44)
        self.in_category.setMinimumWidth(180)
        self.in_qty = self._editorial_entry("0")
        self.in_qty.setMinimumWidth(100)
        self.in_qty.setMaximumWidth(140)
        self.in_unit = self._editorial_entry("u.")
        self.in_unit.setMinimumWidth(100)
        self.in_unit.setMaximumWidth(140)

        form_lay.addWidget(self.in_name, 1, 0)
        form_lay.addWidget(self.in_category, 1, 1)
        form_lay.addWidget(self.in_qty, 1, 2)
        form_lay.addWidget(self.in_unit, 1, 3)

        # Row 2 — labels
        form_lay.addWidget(self._field_label("Ubicación"), 2, 0)
        form_lay.addWidget(self._field_label("Stock mín."), 2, 1)

        # Row 3 — inputs
        self.in_location = self._editorial_entry("Estante A-3")
        self.in_location.setMinimumWidth(220)
        self.in_min = self._editorial_entry("0")
        self.in_min.setMinimumWidth(100)
        self.in_min.setMaximumWidth(140)
        form_lay.addWidget(self.in_location, 3, 0)
        form_lay.addWidget(self.in_min, 3, 1)

        # Botón agregar (al final de la fila 3)
        add_btn = self._primary_button("+  Agregar ítem", self.add_item)
        form_lay.addWidget(add_btn, 3, 3, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        form_lay.setColumnStretch(4, 1)

        lay.addWidget(form)
        hairline(lay)

        # Header de tabla
        th = QFrame()
        th.setStyleSheet("")
        th_lay = QHBoxLayout(th)
        th_lay.setContentsMargins(0, 12, 0, 4)
        th_lay.setSpacing(12)
        h_lbl = QLabel("LISTADO")
        h_lbl.setObjectName("table-header")
        th_lay.addWidget(h_lbl)
        h_sub = QLabel("Ordenado alfabéticamente")
        h_sub.setObjectName("caption")
        th_lay.addWidget(h_sub)
        th_lay.addStretch()
        lay.addWidget(th)

        # Tabla
        self.tree = QTableWidget()
        self.tree.setColumnCount(7)
        self.tree.setHorizontalHeaderLabels(["ID", "Nombre", "Categoría", "Cantidad", "Unidad", "Ubicación", "Stock mín."])
        self.tree.verticalHeader().setVisible(False)
        self.tree.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tree.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tree.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tree.setShowGrid(False)
        self.tree.horizontalHeader().setStretchLastSection(False)
        self.tree.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        widths = [50, 0, 130, 90, 90, 0, 90]
        for i, w in enumerate(widths):
            if w > 0:
                self.tree.horizontalHeader().resizeSection(i, w)
                self.tree.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Fixed if i not in (1, 5) else QHeaderView.ResizeMode.Stretch
                )
        self.tree.verticalHeader().setDefaultSectionSize(40)
        lay.addWidget(self.tree, stretch=1)

        # Botones inferiores
        bot = QFrame()
        bot.setStyleSheet("")
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(0, 12, 0, 0)
        bot_lay.setSpacing(8)
        bot_lay.addWidget(self._danger_button("Eliminar seleccionado", self.delete_item_selected))
        bot_lay.addWidget(self._secondary_button("↻  Actualizar lista", self.refresh_inventory))
        bot_lay.addStretch()
        lay.addWidget(bot)

        self.stack.addWidget(page)

    # ── PESTAÑA TRABAJADORES ───────────────────────────────────────────────
    def _build_workers_tab(self):
        page = QWidget()
        page.setStyleSheet("")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._section_header("02", ["Trabajadores"], "Personas autorizadas a retirar y devolver materiales."))

        # Form
        form = QFrame()
        form.setStyleSheet("")
        form_lay = QHBoxLayout(form)
        form_lay.setContentsMargins(0, 0, 0, 16)
        form_lay.setSpacing(16)

        form_lay.addWidget(self._field_label("Nombre del trabajador"), stretch=0)
        self.in_worker = self._editorial_entry("Ej: Juan Pérez")
        self.in_worker.setMinimumWidth(300)
        form_lay.addWidget(self.in_worker, stretch=0)
        form_lay.addWidget(self._primary_button("+  Agregar", self.add_worker), stretch=0, alignment=Qt.AlignmentFlag.AlignLeft)
        form_lay.addStretch()

        lay.addWidget(form)
        hairline(lay)

        # Header
        th = QFrame()
        th.setStyleSheet("")
        th_lay = QHBoxLayout(th)
        th_lay.setContentsMargins(0, 12, 0, 4)
        th_lay.setSpacing(12)
        h_lbl = QLabel("NÓMINA")
        h_lbl.setObjectName("table-header")
        th_lay.addWidget(h_lbl)
        h_sub = QLabel("Ordenada alfabéticamente")
        h_sub.setObjectName("caption")
        th_lay.addWidget(h_sub)
        th_lay.addStretch()
        lay.addWidget(th)

        # Lista scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {_theme['paper']}; border: none; }}")

        self.workers_container = QWidget()
        self.workers_container.setStyleSheet("")
        self.workers_layout = QVBoxLayout(self.workers_container)
        self.workers_layout.setContentsMargins(0, 0, 0, 0)
        self.workers_layout.setSpacing(0)
        self.workers_layout.addStretch()
        scroll.setWidget(self.workers_container)
        lay.addWidget(scroll, stretch=1)

        # Botones inferiores
        bot = QFrame()
        bot.setStyleSheet("")
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(0, 12, 0, 0)
        bot_lay.setSpacing(8)
        self.in_del_worker = self._editorial_entry("Nombre exacto a eliminar")
        self.in_del_worker.setMinimumWidth(300)
        bot_lay.addWidget(self.in_del_worker)
        bot_lay.addWidget(self._danger_button("Eliminar", self.delete_worker))
        bot_lay.addWidget(self._secondary_button("↻  Actualizar", self.refresh_workers))
        bot_lay.addStretch()
        lay.addWidget(bot)

        self.stack.addWidget(page)

    # ── PESTAÑA MOVIMIENTOS ────────────────────────────────────────────────
    def _build_movements_tab(self):
        page = QWidget()
        page.setStyleSheet("")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._section_header("03", ["Movimientos"], "Historial de retiros y devoluciones registrados."))

        self.tree_mov = QTableWidget()
        self.tree_mov.setColumnCount(6)
        self.tree_mov.setHorizontalHeaderLabels(["ID", "Ítem", "Trabajador", "Acción", "Cantidad", "Fecha · Hora"])
        self.tree_mov.verticalHeader().setVisible(False)
        self.tree_mov.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tree_mov.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tree_mov.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tree_mov.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tree_mov.setShowGrid(False)
        self.tree_mov.horizontalHeader().setStretchLastSection(False)
        self.tree_mov.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree_mov.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree_mov.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        widths = [50, 0, 0, 110, 90, 0]
        for i, w in enumerate(widths):
            if w > 0:
                self.tree_mov.horizontalHeader().resizeSection(i, w)
        self.tree_mov.verticalHeader().setDefaultSectionSize(38)
        lay.addWidget(self.tree_mov, stretch=1)

        bot = QFrame()
        bot.setStyleSheet("")
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(0, 12, 0, 0)
        bot_lay.setSpacing(8)
        bot_lay.addWidget(self._secondary_button("↻  Actualizar", self.refresh_movements))
        bot_lay.addStretch()
        lay.addWidget(bot)

        self.stack.addWidget(page)

    # ── PESTAÑA SERVIDOR / QR ──────────────────────────────────────────────
    def _build_server_tab(self):
        page = QWidget()
        page.setStyleSheet("")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._section_header("04", ["Servidor · QR"], "Acceso público y código QR del taller."))

        srv_card = QFrame()
        srv_card.setObjectName("card")
        srv_card_lay = QVBoxLayout(srv_card)
        srv_card_lay.setContentsMargins(24, 20, 24, 20)
        srv_card_lay.setSpacing(4)

        lbl1 = QLabel("URL PÚBLICA")
        lbl1.setObjectName("field-label")
        srv_card_lay.addWidget(lbl1)

        url_val = QLabel(PUBLIC_URL)
        url_val.setObjectName("url-value")
        srv_card_lay.addWidget(url_val)

        srv_card_lay.addSpacing(8)

        desc = QLabel("Este es el único QR que necesitás: imprimilo y pegalo en el taller.\n"
                      "Al escanearlo, el trabajador elige su nombre, el material y la cantidad.")
        desc.setObjectName("caption")
        desc.setWordWrap(True)
        srv_card_lay.addWidget(desc)

        srv_card_lay.addSpacing(12)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addWidget(self._secondary_button("↗  Abrir en navegador", lambda: webbrowser.open(PUBLIC_URL)))
        btns.addWidget(self._primary_button("⤓  Descargar QR general", self.download_qr))
        btns.addStretch()
        srv_card_lay.addLayout(btns)

        srv_card.setGraphicsEffect(make_shadow(blur=18, y=4, color=QColor(44, 44, 44, 18)))
        lay.addWidget(srv_card)

        # Header de notificaciones
        not_head = QFrame()
        not_head.setStyleSheet("")
        not_lay = QHBoxLayout(not_head)
        not_lay.setContentsMargins(0, 20, 0, 4)
        not_lay.setSpacing(12)
        h_lbl = QLabel("NOTIFICACIONES WHATSAPP PENDIENTES")
        h_lbl.setObjectName("table-header")
        not_lay.addWidget(h_lbl)
        h_sub = QLabel("Mensajes aún no enviados")
        h_sub.setObjectName("caption")
        not_lay.addWidget(h_sub)
        not_lay.addStretch()
        lay.addWidget(not_head)

        not_card = QFrame()
        not_card.setObjectName("card-warm")
        not_card_lay = QVBoxLayout(not_card)
        not_card_lay.setContentsMargins(0, 0, 0, 0)
        not_card_lay.setSpacing(0)

        self.notif_box = QTextEdit()
        self.notif_box.setReadOnly(True)
        not_card_lay.addWidget(self.notif_box)

        lay.addWidget(not_card, stretch=1)

        bot = QFrame()
        bot.setStyleSheet("")
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(0, 12, 0, 0)
        bot_lay.setSpacing(8)
        bot_lay.addWidget(self._secondary_button("↻  Actualizar", self.refresh_notifications))
        bot_lay.addWidget(self._primary_button("↻  Reintentar envío WhatsApp", self.retry_whatsapp))
        bot_lay.addStretch()
        lay.addWidget(bot)

        self.stack.addWidget(page)

    # ── Helpers de red ─────────────────────────────────────────────────────
    def api_get(self, path, params=None):
        try:
            r = requests.get(f"{PUBLIC_URL}{path}", headers=HEADERS, params=params, timeout=10)
            if r.status_code == 401:
                self._show_toast("Clave admin incorrecta — revisá config.py", error=True)
                return None
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[api_get] {path}: {e}")
            return None

    def api_post(self, path, data=None):
        try:
            r = requests.post(f"{PUBLIC_URL}{path}", headers=HEADERS, json=data, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            self._show_toast(f"Error de conexión: {e}", error=True)
            return None

    def api_delete(self, path, data=None):
        try:
            r = requests.delete(f"{PUBLIC_URL}{path}", headers=HEADERS, json=data, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            self._show_toast(f"Error de conexión: {e}", error=True)
            return None

    # ── NOTIFICACIONES AUTOMÁTICAS (polling cada 15 s) ─────────────────────
    def _start_polling(self):
        t = threading.Thread(target=self._poll_loop, daemon=True)
        t.start()

    def _poll_loop(self):
        while True:
            time.sleep(15)
            try:
                data = self.api_get("/api/movements/latest", params={"since": self._last_movement_id})
                if data:
                    self.new_movements_signal.emit(data)
            except Exception:
                pass

    def _handle_new_movements(self, movements):
        if not movements:
            return
        for m in movements:
            self._last_movement_id = max(self._last_movement_id, m["id"])
            verbo = "retiró" if m["action"] == "retiro" else "devolvió"
            msg = f"{m['worker_name']} {verbo} {m['quantity']} {m['unit']} de «{m['item_name']}»"
            self._show_toast(msg)
        if self._active_tab_idx == 2:
            self.refresh_movements()

    def _show_toast(self, message, error=False):
        toast = Toast(self, message, error=error)
        toast.pop_at(self)

    # ── INVENTARIO acciones ────────────────────────────────────────────────
    def add_item(self):
        try:
            name = self.in_name.text().strip()
            if not name: raise ValueError("Falta nombre")
            qty = float(self.in_qty.text())
            unit = self.in_unit.text().strip() or "u."
            loc = self.in_location.text().strip()
            mins = float(self.in_min.text() or 0)
        except Exception as e:
            self._show_toast(str(e), error=True)
            return
        res = self.api_post("/api/items", {
            "name": name, "category": self.in_category.currentText(),
            "quantity": qty, "unit": unit, "location": loc, "min_stock": mins
        })
        if res:
            self.in_name.clear()
            self.in_qty.clear()
            self.in_unit.clear()
            self.in_location.clear()
            self.in_min.clear()
            self.refresh_inventory()
            self._show_toast(f"«{name}» agregado al inventario.")

    def refresh_inventory(self):
        items = self.api_get("/api/items")
        if items is None: return
        self.tree.setRowCount(0)
        for r, i in enumerate(items):
            self.tree.insertRow(r)
            vals = [
                str(i["id"]), i["name"], i["category"], str(i["quantity"]),
                i["unit"], i["location"] or "—", str(i["min_stock"])
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 0:
                    item.setForeground(QColor(_theme["ink_mute"]))
                    f = QFont(F_MONO); f.setPointSize(9); item.setFont(f)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif c == 1:
                    f = QFont(F_SERIF); f.setPointSize(12); item.setFont(f)
                elif c == 2:
                    f = QFont(F_SERIF); f.setPointSize(11); f.setItalic(True); item.setFont(f)
                    item.setForeground(QColor(_theme["ink_mute"]))
                elif c in (3, 4):
                    f = QFont(F_SERIF); f.setPointSize(11); f.setItalic(True); item.setFont(f)
                    item.setForeground(QColor(_theme["ink_blue"]))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif c == 5:
                    f = QFont(F_SERIF); f.setPointSize(11); item.setFont(f)
                    item.setForeground(QColor(_theme["ink_soft"]))
                elif c == 6:
                    f = QFont(F_MONO); f.setPointSize(10); item.setFont(f)
                    item.setForeground(QColor(_theme["ink_mute"]))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tree.setItem(r, c, item)

    def delete_item_selected(self):
        sel = self.tree.selectionModel().selectedRows()
        if not sel:
            self._show_toast("Seleccioná un ítem de la lista.", error=True)
            return
        row = sel[0].row()
        iid = self.tree.item(row, 0).text()
        nombre = self.tree.item(row, 1).text()
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar «{nombre}» del inventario?") == QMessageBox.StandardButton.Yes:
            self.api_delete(f"/api/items/{iid}")
            self.refresh_inventory()
            self._show_toast(f"«{nombre}» eliminado.")

    # ── TRABAJADORES acciones ──────────────────────────────────────────────
    def add_worker(self):
        name = self.in_worker.text().strip()
        if not name:
            self._show_toast("Escribí el nombre del trabajador.", error=True)
            return
        res = self.api_post("/api/workers", {"name": name})
        if res:
            self.in_worker.clear()
            self.refresh_workers()
            self._show_toast(f"«{name}» agregado a la nómina.")

    def delete_worker(self):
        name = self.in_del_worker.text().strip()
        if not name: return
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar a «{name}» de la nómina?") == QMessageBox.StandardButton.Yes:
            self.api_delete("/api/workers", {"name": name})
            self.in_del_worker.clear()
            self.refresh_workers()
            self._show_toast(f"«{name}» eliminado.")

    def refresh_workers(self):
        while self.workers_layout.count() > 1:
            item = self.workers_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        data = self.api_get("/api/workers")
        if data is None: return

        if not data:
            empty = QLabel("No hay trabajadores cargados todavía.\nEl administrador debe agregarlos desde acá.")
            empty.setObjectName("empty")
            empty.setStyleSheet("padding: 24px 0;")
            self.workers_layout.insertWidget(self.workers_layout.count() - 1, empty)
            return

        for i, w in enumerate(data, start=1):
            row = QFrame()
            row.setObjectName("worker-row")
            row.setStyleSheet(
                f"QFrame#worker-row {{ background-color: {_theme['paper']}; "
                f"border: none; border-bottom: 1px solid {_theme['hairline_2']}; }}"
            )
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 14, 0, 14)
            row_lay.setSpacing(20)

            num = QLabel(f"{i:02d}")
            num.setObjectName("worker-num")
            num.setFixedWidth(50)
            row_lay.addWidget(num, alignment=Qt.AlignmentFlag.AlignLeft)

            name = QLabel(w)
            name.setObjectName("worker-name")
            row_lay.addWidget(name, stretch=1)

            self.workers_layout.insertWidget(self.workers_layout.count() - 1, row)

    # ── MOVIMIENTOS acciones ───────────────────────────────────────────────
    def refresh_movements(self):
        movs = self.api_get("/api/movements")
        if movs is None: return
        self.tree_mov.setRowCount(0)
        for r, m in enumerate(movs):
            self.tree_mov.insertRow(r)
            vals = [
                str(m["id"]), m["item_name"], m["worker_name"],
                m["action"], str(m["quantity"]), m["timestamp"]
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 0:
                    item.setForeground(QColor(_theme["ink_mute"]))
                    f = QFont(F_MONO); f.setPointSize(9); item.setFont(f)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif c == 1:
                    f = QFont(F_SERIF); f.setPointSize(12); item.setFont(f)
                elif c == 2:
                    f = QFont(F_SERIF); f.setPointSize(11); f.setItalic(True); item.setFont(f)
                    item.setForeground(QColor(_theme["ink_soft"]))
                elif c == 3:
                    if m["action"] == "retiro":
                        item.setForeground(QColor(_theme["oxblood"]))
                    else:
                        item.setForeground(QColor(_theme["moss"]))
                    f = QFont(F_MONO); f.setPointSize(9); f.setWeight(QFont.Weight.Bold); item.setFont(f)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif c == 4:
                    f = QFont(F_SERIF); f.setPointSize(11); f.setItalic(True); item.setFont(f)
                    item.setForeground(QColor(_theme["ink_blue"]))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif c == 5:
                    f = QFont(F_MONO); f.setPointSize(9); item.setFont(f)
                    item.setForeground(QColor(_theme["ink_mute"]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tree_mov.setItem(r, c, item)

        if movs:
            self._last_movement_id = max(self._last_movement_id, movs[0]["id"])

    # ── SERVIDOR / QR acciones ─────────────────────────────────────────────
    def download_qr(self):
        try:
            r = requests.get(f"{PUBLIC_URL}/qr", timeout=10)
            r.raise_for_status()
            with open("qr_general_taller.png", "wb") as f:
                f.write(r.content)
            self._show_toast("QR guardado como qr_general_taller.png")
        except Exception as e:
            self._show_toast(str(e), error=True)

    def refresh_notifications(self):
        notifs = self.api_get("/api/notifications")
        if notifs is None: return
        self.notif_box.clear()

        if not notifs:
            cursor = self.notif_box.textCursor()
            fmt = cursor.charFormat()
            fmt.setFont(font_serif(14, italic=True))
            fmt.setForeground(QColor(_theme["ink_mute"]))
            cursor.setCharFormat(fmt)
            cursor.insertText("No hay notificaciones pendientes. Todo en orden.")
            return

        for n in notifs:
            cursor = self.notif_box.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)

            fmt_ts = cursor.charFormat()
            fmt_ts.setFont(font_mono(9, weight=QFont.Weight.Bold))
            fmt_ts.setForeground(QColor(_theme["ink_mute"]))
            cursor.setCharFormat(fmt_ts)
            cursor.insertText(f"[{n['timestamp']}]\n")

            fmt_msg = cursor.charFormat()
            fmt_msg.setFont(font_serif(13))
            fmt_msg.setForeground(QColor(_theme["ink"]))
            cursor.setCharFormat(fmt_msg)
            cursor.insertText(f"{n['message']}\n\n")

    def retry_whatsapp(self):
        res = self.api_post("/api/notifications/retry")
        if res:
            self._show_toast(f"Enviadas: {res['sent']} de {res['total']}")
            self.refresh_notifications()

    # ── GENERAL ────────────────────────────────────────────────────────────
    def refresh_all(self):
        self.refresh_inventory()
        self.refresh_workers()
        self.refresh_movements()
        self.refresh_notifications()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss(_theme))

    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window, QColor(_theme["paper"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(_theme["paper"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(_theme["paper_warm"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(_theme["ink"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(_theme["ink"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(_theme["paper"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(_theme["ink"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(_theme["paper_warm"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(_theme["ink_blue"]))
    app.setPalette(pal)

    app.setFont(font_sans(11))

    win = TallerApp(theme_name="light")
    win.show()

    # Forzar re-aplicación del estilo después de crear todos los widgets
    for w in app.allWidgets():
        w.style().unpolish(w)
        w.style().polish(w)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
