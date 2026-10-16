"""Light/dark theming for the MetaDel window — a clean Windows 11 / Fluent look."""

from __future__ import annotations

# Accent colours offered in Settings.
ACCENTS: dict[str, str] = {
    "blue": "#0067c0",
    "teal": "#038387",
    "green": "#0f7b0f",
    "purple": "#8764b8",
    "orange": "#c0560f",
    "red": "#c42b1c",
}

_PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#f3f3f3", "surface": "#ffffff", "surface2": "#fafafa",
        "text": "#1a1a1a", "subtext": "#5a5a5a", "border": "#d6d6d6",
        "hover": "#ededed", "grid": "#ececec", "header": "#f7f7f7",
        "sel": "#e6e6e6", "disabled": "#a0a0a0",
    },
    "dark": {
        "bg": "#1f1f1f", "surface": "#2b2b2b", "surface2": "#262626",
        "text": "#f0f0f0", "subtext": "#b8b8b8", "border": "#3d3d3d",
        "hover": "#383838", "grid": "#333333", "header": "#2b2b2b",
        "sel": "#3a3a3a", "disabled": "#6b6b6b",
    },
}


def _shade(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, min(255, round(c * factor))) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def build_qss(theme: str, accent_key: str, check_icon: str | None = None) -> str:
    p = _PALETTES.get(theme, _PALETTES["light"])
    accent = ACCENTS.get(accent_key, ACCENTS["blue"])
    accent_hover = _shade(accent, 1.12)
    accent_press = _shade(accent, 0.88)
    # Checked checkbox: a coloured tick on a plain box, not a solid fill.
    if check_icon:
        checked_rule = (
            'QCheckBox::indicator:checked { background: ' + p["surface"]
            + '; border-color: ' + accent + '; image: url("' + check_icon + '"); }'
        )
    else:
        checked_rule = (
            'QCheckBox::indicator:checked { background: ' + accent
            + '; border-color: ' + accent + '; }'
        )
    return f"""
    * {{ font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif; font-size: 10pt; }}
    QWidget {{ background-color: {p['bg']}; color: {p['text']}; }}
    QMainWindow, QDialog {{ background-color: {p['bg']}; }}
    QLabel {{ background: transparent; }}
    QToolTip {{ background-color: {p['surface']}; color: {p['text']};
               border: 1px solid {p['border']}; padding: 4px; }}

    QPushButton {{
        background-color: {p['surface']}; color: {p['text']};
        border: 1px solid {p['border']}; border-radius: 6px;
        padding: 6px 14px; min-height: 18px;
    }}
    QPushButton:hover {{ background-color: {p['hover']}; }}
    QPushButton:pressed {{ background-color: {p['sel']}; }}
    QPushButton:disabled {{ color: {p['disabled']}; }}

    QPushButton#primary {{
        background-color: {accent}; color: #ffffff; border: 1px solid {accent};
        font-weight: 600;
    }}
    QPushButton#primary:hover {{ background-color: {accent_hover}; border-color: {accent_hover}; }}
    QPushButton#primary:pressed {{ background-color: {accent_press}; border-color: {accent_press}; }}
    QPushButton#primary:disabled {{ background-color: {p['border']};
        border-color: {p['border']}; color: {p['disabled']}; }}

    QComboBox {{
        background-color: {p['surface']}; border: 1px solid {p['border']};
        border-radius: 6px; padding: 5px 10px; min-height: 18px;
    }}
    QComboBox:hover {{ border-color: {accent}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background-color: {p['surface']}; color: {p['text']};
        border: 1px solid {p['border']};
        selection-background-color: {accent}; selection-color: #ffffff; outline: none;
    }}

    QCheckBox {{ background: transparent; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px; border: 1px solid {p['border']};
        border-radius: 4px; background: {p['surface']};
    }}
    QCheckBox::indicator:hover {{ border-color: {accent}; }}
    {checked_rule}

    QTableWidget {{
        background-color: {p['surface']};
        alternate-background-color: {p['surface2']};
        gridline-color: {p['grid']};
        border: 1px solid {p['border']}; border-radius: 8px; outline: none;
    }}
    QTableWidget::item {{ padding: 4px 6px; }}
    QTableWidget::item:selected {{ background-color: {p['sel']}; color: {p['text']}; }}
    QHeaderView::section {{
        background-color: {p['header']}; color: {p['subtext']};
        border: none; border-bottom: 1px solid {p['border']};
        padding: 7px 8px; font-weight: 600;
    }}
    QTableCornerButton::section {{ background-color: {p['header']}; border: none; }}

    QProgressBar {{
        border: 1px solid {p['border']}; border-radius: 6px;
        background-color: {p['surface']}; text-align: center; max-height: 16px;
        color: #ffffff;
    }}
    QProgressBar::chunk {{ background-color: {accent}; border-radius: 5px; }}

    QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {p['border']}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {p['subtext']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {p['border']}; border-radius: 5px; min-width: 28px; }}

    QMenu {{ background-color: {p['surface']}; border: 1px solid {p['border']}; }}
    QMenu::item:selected {{ background-color: {accent}; color: #ffffff; }}
    """
