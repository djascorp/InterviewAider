"""Stylesheet definitions for the Interview Assistant overlay."""

# Color palette matching the UI/UX design
COLORS = {
    "bg": "rgba(10, 10, 12, 0.96)",
    "bg_hex": "#0a0a0c",
    "bg2": "rgba(255,255,255,0.04)",
    "bg3": "rgba(255,255,255,0.07)",
    "border": "rgba(255,255,255,0.09)",
    "border2": "rgba(255,255,255,0.16)",
    "text": "#edeae4",
    "text2": "#7a776f",
    "text3": "#3f3d3a",
    "green": "#a8e063",
    "green_dim": "rgba(168,224,99,0.1)",
    "red": "#ff5f5f",
    "amber": "#f0a030",
}

# Font families
FONTS = {
    "mono": "'IBM Plex Mono', 'Consolas', monospace",
    "sans": "'IBM Plex Sans', 'Segoe UI', sans-serif",
}

# Main overlay widget style
OVERLAY_STYLE = f"""
    QWidget#overlay {{
        background: {COLORS['bg_hex']};
        border: 1px solid {COLORS['border2']};
        border-radius: 14px;
    }}
"""

# Header styles
HEADER_STYLE = f"""
    QWidget#header {{
        background: transparent;
        border-bottom: 1px solid {COLORS['border']};
        border-top-left-radius: 14px;
        border-top-right-radius: 14px;
        min-height: 32px;
        max-height: 32px;
        padding: 0 12px;
    }}
"""

STATUS_DOT_STYLE = f"""
    QLabel#statusDot {{
        background: {COLORS['green']};
        border-radius: 4px;
        min-width: 7px;
        max-width: 7px;
        min-height: 7px;
        max-height: 7px;
    }}
"""

STATUS_DOT_PAUSED_STYLE = f"""
    QLabel#statusDot {{
        background: {COLORS['text3']};
        border-radius: 4px;
        min-width: 7px;
        max-width: 7px;
        min-height: 7px;
        max-height: 7px;
    }}
"""

HEADER_TITLE_STYLE = f"""
    QLabel#headerTitle {{
        color: {COLORS['text2']};
        font-family: {FONTS['mono']};
        font-size: 11px;
        letter-spacing: 0.03em;
    }}
"""

HEADER_BTN_STYLE = f"""
    QPushButton#headerBtn {{
        background: transparent;
        border: none;
        border-radius: 5px;
        color: {COLORS['text3']};
        font-size: 13px;
        min-width: 22px;
        max-width: 22px;
        min-height: 22px;
        max-height: 22px;
        padding: 0;
    }}
    QPushButton#headerBtn:hover {{
        background: {COLORS['bg3']};
        color: {COLORS['text2']};
    }}
"""

NOTIF_BADGE_STYLE = f"""
    QLabel#notifBadge {{
        background: {COLORS['red']};
        border-radius: 4px;
        border: 1.5px solid {COLORS['bg_hex']};
        min-width: 8px;
        max-width: 8px;
        min-height: 8px;
        max-height: 8px;
    }}
"""

# Waveform strip
WAVE_STRIP_STYLE = f"""
    QWidget#waveStrip {{
        background: transparent;
        border-bottom: 1px solid {COLORS['border']};
        min-height: 32px;
        max-height: 32px;
        padding: 0 12px;
    }}
"""

WAVE_BAR_STYLE = f"""
    QLabel#waveBar {{
        background: {COLORS['green']};
        border-radius: 1px;
        min-width: 3px;
        max-width: 3px;
    }}
"""

WAVE_META_STYLE = f"""
    QLabel#waveMeta {{
        color: {COLORS['text3']};
        font-family: {FONTS['mono']};
        font-size: 10px;
    }}
"""

WAVE_META_BOLD_STYLE = f"""
    QLabel#waveMetaBold {{
        color: {COLORS['green']};
        font-family: {FONTS['mono']};
        font-size: 10px;
        font-weight: 500;
    }}
"""

# State: Listening
LISTENING_STYLE = f"""
    QWidget#stateListening {{
        background: transparent;
        padding: 18px 14px;
    }}
"""

LISTEN_RING_STYLE = f"""
    QLabel#listenRing {{
        background: transparent;
        border: 1.5px solid {COLORS['border2']};
        border-radius: 24px;
        min-width: 48px;
        max-width: 48px;
        min-height: 48px;
        max-height: 48px;
    }}
"""

LISTEN_RING_PULSE_STYLE = f"""
    QLabel#listenRingPulse {{
        background: transparent;
        border: 1px solid {COLORS['green']};
        border-radius: 30px;
        min-width: 60px;
        max-width: 60px;
        min-height: 60px;
        max-height: 60px;
    }}
"""

LISTEN_LABEL_STYLE = f"""
    QLabel#listenLabel {{
        color: {COLORS['text']};
        font-size: 12px;
        font-weight: 500;
    }}
"""

LISTEN_SUB_STYLE = f"""
    QLabel#listenSub {{
        color: {COLORS['text3']};
        font-family: {FONTS['mono']};
        font-size: 10px;
    }}
"""

# State: Analyzing
ANALYZING_STYLE = f"""
    QWidget#stateAnalyzing {{
        background: transparent;
        padding: 16px 14px;
    }}
"""

ANALYZING_DOT_STYLE = f"""
    QLabel#analyzingDot {{
        background: {COLORS['green']};
        border-radius: 3px;
        min-width: 5px;
        max-width: 5px;
        min-height: 5px;
        max-height: 5px;
    }}
"""

ANALYZING_LABEL_STYLE = f"""
    QLabel#analyzingLabel {{
        color: {COLORS['text2']};
        font-family: {FONTS['mono']};
        font-size: 11px;
    }}
"""

# State: Answer
QUESTION_STRIP_STYLE = f"""
    QWidget#questionStrip {{
        background: {COLORS['bg2']};
        border-bottom: 1px solid {COLORS['border']};
        padding: 10px 14px;
    }}
"""

QUESTION_TAG_STYLE = f"""
    QLabel#questionTag {{
        color: {COLORS['green']};
        font-family: {FONTS['mono']};
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }}
"""

QUESTION_TEXT_STYLE = f"""
    QLabel#questionText {{
        color: {COLORS['text']};
        font-size: 12px;
        line-height: 1.45;
    }}
"""

ANSWER_BODY_STYLE = f"""
    QScrollArea#answerBody {{
        background: transparent;
        border: none;
        max-height: 260px;
    }}
    QScrollArea#answerBody > QWidget {{
        background: transparent;
    }}
"""

ANSWER_MAIN_STYLE = f"""
    QLabel#answerMain {{
        color: {COLORS['text']};
        font-size: 13px;
        line-height: 1.75;
        font-weight: 300;
    }}
"""

ANSWER_CODE_STYLE = f"""
    QLabel#answerCode {{
        color: {COLORS['green']};
        font-family: {FONTS['mono']};
        font-size: 11px;
        background: {COLORS['bg3']};
        border: 1px solid {COLORS['border2']};
        border-radius: 3px;
        padding: 1px 4px;
    }}
"""

BULLET_STYLE = f"""
    QWidget#bullet {{
        background: {COLORS['bg2']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 6px 9px;
    }}
"""

BULLET_DASH_STYLE = f"""
    QLabel#bulletDash {{
        color: {COLORS['green']};
        font-family: {FONTS['mono']};
        font-size: 11px;
    }}
"""

BULLET_TEXT_STYLE = f"""
    QLabel#bulletText {{
        color: {COLORS['text2']};
        font-size: 11.5px;
        line-height: 1.5;
    }}
"""

# Action bar
ACTION_BAR_STYLE = f"""
    QWidget#actionBar {{
        background: transparent;
        border-top: 1px solid {COLORS['border']};
        min-height: 36px;
        max-height: 36px;
        padding: 0 10px;
    }}
"""

ACTION_BTN_STYLE = f"""
    QPushButton#actBtn {{
        background: transparent;
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        color: {COLORS['text2']};
        font-family: {FONTS['mono']};
        font-size: 10px;
        padding: 5px 10px;
        letter-spacing: 0.03em;
    }}
    QPushButton#actBtn:hover {{
        background: {COLORS['bg3']};
        border-color: {COLORS['border2']};
        color: {COLORS['text']};
    }}
"""

ACTION_BTN_PRIMARY_STYLE = f"""
    QPushButton#actBtnPrimary {{
        background: {COLORS['green']};
        border: none;
        border-radius: 6px;
        color: #0a0a0b;
        font-family: {FONTS['mono']};
        font-size: 10px;
        font-weight: 500;
        padding: 5px 10px;
        letter-spacing: 0.03em;
    }}
    QPushButton#actBtnPrimary:hover {{
        background: #b8ee72;
    }}
"""

LATENCY_STYLE = f"""
    QLabel#latency {{
        color: {COLORS['text3']};
        font-family: {FONTS['mono']};
        font-size: 10px;
    }}
"""

LATENCY_BOLD_STYLE = f"""
    QLabel#latencyBold {{
        color: {COLORS['green']};
        font-family: {FONTS['mono']};
        font-size: 10px;
        font-weight: 500;
    }}
"""

# Collapsed state
COLLAPSED_BODY_STYLE = f"""
    QWidget#collapsedBody {{
        background: transparent;
        padding: 8px 12px;
    }}
"""

COLLAPSED_TEXT_STYLE = f"""
    QLabel#collapsedText {{
        color: {COLORS['text2']};
        font-family: {FONTS['mono']};
        font-size: 11px;
    }}
"""

# Scrollbar
SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border2']};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
"""

# Resize handle hint (bottom-right corner)
RESIZE_HINT_STYLE = f"""
    QLabel#resizeHint {{
        background: transparent;
        min-width: 10px;
        max-width: 10px;
        min-height: 10px;
        max-height: 10px;
        color: {COLORS['text3']};
        font-size: 10px;
    }}
"""

# Smooth transition helper values (for use in QPropertyAnimation)
TRANSITION_DURATION_MS = 300
TRANSITION_FAST_MS = 150
TRANSITION_EASING = "cubic-bezier(0.4, 0, 0.2, 1)"
