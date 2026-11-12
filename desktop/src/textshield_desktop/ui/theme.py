"""Dark desktop stylesheet."""

STYLESHEET = """
QWidget {
    color: #dce7ff;
    font-family: "Segoe UI", "Segoe UI Variable", sans-serif;
    font-size: 9pt;
}
QMainWindow, QDialog {
    background-color: #07101d;
}
QFrame#OverlayRoot {
    background-color: #0b1626;
    border: 1px solid #22344d;
    border-radius: 14px;
}
QFrame#Card {
    background-color: #0e1b2c;
    border: 1px solid #1f3249;
    border-radius: 10px;
}
QLabel {
    background: transparent;
}
QLabel#Title {
    font-size: 16pt;
    font-weight: 700;
    color: #f3f7ff;
}
QLabel#Subtitle {
    color: #8ca2c4;
}
QLabel#OverlayTitle {
    font-size: 10pt;
    font-weight: 600;
    color: #eef5ff;
}
QLabel#SectionTitle {
    color: #f3f7ff;
    font-weight: 600;
}
QLabel#Muted {
    color: #8ca2c4;
}
QLabel#ClassificationBadge {
    background-color: #172b43;
    color: #cfe0ff;
    border-radius: 6px;
    padding: 4px 9px;
    font-weight: 700;
    font-size: 9pt;
}
QLabel#ClassificationBadge[classification="SPAM"] {
    background-color: #431d28;
    color: #ffb4c0;
}
QLabel#ClassificationBadge[classification="PHISHING"] {
    background-color: #4a2712;
    color: #ffc48a;
}
QLabel#ClassificationBadge[classification="SUSPICIOUS"] {
    background-color: #3d3514;
    color: #ffe28a;
}
QLabel#ClassificationBadge[classification="HAM"] {
    background-color: #14372b;
    color: #9ff0c8;
}
QLabel#ClassificationBadge[classification="ERROR"] {
    background-color: #431d28;
    color: #ffb4c0;
}
QLabel#RiskBadge {
    color: #a9bfdc;
    font-size: 8pt;
    font-weight: 600;
}
QLabel#RiskBadge[risk="HIGH"] {
    color: #ff9aab;
}
QLabel#RiskBadge[risk="MEDIUM"] {
    color: #ffd27d;
}
QLabel#RiskBadge[risk="LOW"] {
    color: #8fe3bd;
}
QLabel#StatusDot {
    color: #64748b;
    font-size: 12pt;
}
QLabel#StatusDot[online="true"] {
    color: #35d39a;
}
QLabel#StatusText {
    color: #8ca2c4;
    font-size: 8pt;
}
QLabel#ErrorText {
    background-color: #2a1520;
    border: 1px solid #5b2638;
    border-radius: 7px;
    color: #ffb4c0;
    padding: 8px;
}
QLabel#HintText {
    color: #6f87aa;
    font-size: 8pt;
}
QPlainTextEdit, QTextBrowser, QLineEdit {
    background-color: #08111f;
    border: 1px solid #22344d;
    border-radius: 8px;
    color: #e8f0ff;
    selection-background-color: #1c4d66;
    padding: 8px;
}
QPlainTextEdit:focus, QLineEdit:focus {
    border-color: #2fb7d3;
}
QTextBrowser {
    border: none;
    padding: 2px;
}
QPushButton {
    background-color: #16283e;
    border: 1px solid #29415f;
    border-radius: 8px;
    color: #dce7ff;
    padding: 8px 14px;
}
QPushButton:hover {
    background-color: #1d334e;
    border-color: #3a587b;
}
QPushButton:pressed {
    background-color: #122238;
}
QPushButton:disabled {
    color: #637897;
    background-color: #101d2e;
    border-color: #1b2c42;
}
QPushButton#AnalyzeButton {
    background-color: #2fb7d3;
    border: none;
    color: #06121f;
    font-weight: 700;
    padding: 9px 16px;
}
QPushButton#AnalyzeButton:hover {
    background-color: #4cc8e2;
}
QPushButton#AnalyzeButton:disabled {
    background-color: #1d5261;
    color: #7ca4b2;
}
QPushButton#SecondaryButton {
    background-color: transparent;
    border: 1px solid #29415f;
}
QPushButton#LinkButton {
    background: transparent;
    border: none;
    color: #55c7dd;
    padding: 3px 5px;
}
QPushButton#LinkButton:hover {
    color: #8ce5f5;
    text-decoration: underline;
}
QToolButton#IconButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #9eb3d2;
    font-size: 12pt;
    padding: 2px;
}
QToolButton#IconButton:hover {
    background-color: #1b2e45;
    color: #f3f7ff;
}
QToolButton#LauncherButton {
    background-color: #0b1626;
    border: 2px solid #2fb7d3;
    border-radius: 28px;
}
QToolButton#LauncherButton:hover {
    background-color: #12243a;
    border-color: #63d9ed;
}
QCheckBox {
    spacing: 8px;
    color: #c5d5ed;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #3a587b;
    background-color: #08111f;
}
QCheckBox::indicator:checked {
    background-color: #2fb7d3;
    border-color: #2fb7d3;
}
QMenu {
    background-color: #0c1828;
    border: 1px solid #29415f;
    border-radius: 8px;
    padding: 5px;
}
QMenu::item {
    padding: 7px 22px 7px 12px;
    border-radius: 5px;
}
QMenu::item:selected {
    background-color: #1b334d;
}
QMenu::separator {
    height: 1px;
    background-color: #22344d;
    margin: 4px 7px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #29415f;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QDialogButtonBox QPushButton {
    min-width: 78px;
}
QToolTip {
    background-color: #0c1828;
    color: #dce7ff;
    border: 1px solid #29415f;
    padding: 4px;
}
"""
