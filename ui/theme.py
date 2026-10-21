class Theme:
    # Color Palette
    BG_DARK = "#0D0F12"
    BG_CARD = "#161920"
    BG_CARD_HOVER = "#1E222B"
    BG_SIDEBAR = "#11141A"
    
    BORDER = "#252B37"
    BORDER_LIGHT = "#353D4E"
    
    PRIMARY = "#00D2FF"      # Cyan accent
    PRIMARY_HOVER = "#33DCFF"
    PRIMARY_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0080FF, stop:1 #00D2FF)"
    
    ACCENT_GREEN = "#00E676"  # Charging / battery high
    ACCENT_ORANGE = "#FF9100" # Medium battery
    ACCENT_RED = "#FF5252"    # Low battery / warning
    
    TEXT_MAIN = "#F8FAFC"
    TEXT_MUTED = "#94A3B8"
    TEXT_DIM = "#64748B"

    STYLESHEET = f"""
    QMainWindow, QWidget#CentralWidget {{
        background-color: {BG_DARK};
        color: {TEXT_MAIN};
        font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    }}

    QWidget#Sidebar {{
        background-color: {BG_SIDEBAR};
        border-right: 1px solid {BORDER};
    }}

    QFrame.Card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 16px;
    }}
    QFrame.Card:hover {{
        border: 1px solid {BORDER_LIGHT};
    }}

    QLabel {{
        color: {TEXT_MAIN};
    }}

    QLabel.Title {{
        font-size: 20px;
        font-weight: 700;
        color: {TEXT_MAIN};
    }}

    QLabel.Subtitle {{
        font-size: 13px;
        color: {TEXT_MUTED};
    }}

    QLabel.MetricValue {{
        font-size: 24px;
        font-weight: 700;
        color: {PRIMARY};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
        color: {TEXT_MAIN};
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {BG_CARD_HOVER};
        border-color: {BORDER_LIGHT};
    }}
    QPushButton:pressed {{
        background-color: {BORDER};
    }}
    QPushButton:disabled {{
        color: {TEXT_DIM};
        background-color: #121418;
        border-color: #1A1D24;
    }}

    QPushButton.Primary {{
        background: {PRIMARY_GRADIENT};
        color: #050B14;
        border: none;
        font-weight: 700;
    }}
    QPushButton.Primary:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1A8DFF, stop:1 #33DCFF);
    }}
    QPushButton.Primary:pressed {{
        background: #0080FF;
    }}

    QPushButton.Danger {{
        background-color: rgba(255, 82, 82, 0.15);
        border: 1px solid rgba(255, 82, 82, 0.4);
        color: {ACCENT_RED};
    }}
    QPushButton.Danger:hover {{
        background-color: rgba(255, 82, 82, 0.25);
    }}

    /* Nav Buttons in Sidebar */
    QPushButton.NavBtn {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        color: {TEXT_MUTED};
        text-align: left;
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton.NavBtn:hover {{
        background-color: rgba(255, 255, 255, 0.05);
        color: {TEXT_MAIN};
    }}
    QPushButton.NavBtn[active="true"] {{
        background-color: rgba(0, 210, 255, 0.12);
        color: {PRIMARY};
        border-left: 3px solid {PRIMARY};
    }}

    /* Slider Styling */
    QSlider::groove:horizontal {{
        height: 6px;
        background: {BORDER};
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: {PRIMARY_GRADIENT};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {TEXT_MAIN};
        border: 2px solid {PRIMARY};
        width: 16px;
        margin-top: -5px;
        margin-bottom: -5px;
        border-radius: 8px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {PRIMARY};
        border: 2px solid #FFF;
    }}

    /* Vertical Slider for EQ */
    QSlider::groove:vertical {{
        width: 6px;
        background: {BORDER};
        border-radius: 3px;
    }}
    QSlider::sub-page:vertical {{
        background: {BORDER};
        border-radius: 3px;
    }}
    QSlider::add-page:vertical {{
        background: {PRIMARY_GRADIENT};
        border-radius: 3px;
    }}
    QSlider::handle:vertical {{
        background: {TEXT_MAIN};
        border: 2px solid {PRIMARY};
        height: 16px;
        margin-left: -5px;
        margin-right: -5px;
        border-radius: 8px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {BORDER};
        border-radius: 4px;
        text-align: center;
        color: {TEXT_MAIN};
        font-size: 11px;
        font-weight: bold;
    }}
    QProgressBar::chunk {{
        background: {PRIMARY_GRADIENT};
        border-radius: 4px;
    }}

    /* CheckBox / Toggle Switch simulation */
    QCheckBox {{
        color: {TEXT_MAIN};
        spacing: 8px;
        font-size: 13px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {BORDER_LIGHT};
        border-radius: 4px;
        background-color: {BG_CARD};
    }}
    QCheckBox::indicator:checked {{
        background-color: {PRIMARY};
        border-color: {PRIMARY};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: {BG_DARK};
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER_LIGHT};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
