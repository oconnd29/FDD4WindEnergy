STYLE = """
QMainWindow, QWidget {
    background: #F4F1EA;
    color: #1B3A4B;
    font-family: "Segoe UI", "Calibri", sans-serif;
    font-size: 13px;
}
QMenuBar {
    background: #1B3A4B;
    color: #F4F1EA;
    padding: 4px;
}
QMenuBar::item:selected { background: #2A9D8F; }
QMenu { background: #FFFFFF; color: #1B3A4B; }
QMenu::item:selected { background: #D8EDE9; }

QLabel#AppTitle {
    font-size: 18px;
    font-weight: 600;
    color: #1B3A4B;
}
QLabel#SectionTitle {
    font-size: 15px;
    font-weight: 600;
    color: #1B3A4B;
}
QLabel#Hint {
    color: #5C6B73;
    font-size: 12px;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background: #FFFFFF;
    border: 1px solid #D5D0C7;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: #2A9D8F;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #2A9D8F;
}

QPushButton {
    background: #FFFFFF;
    border: 1px solid #D5D0C7;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover { border-color: #2A9D8F; }
QPushButton:pressed { background: #E7F4F1; }
QPushButton#Primary {
    background: #2A9D8F;
    color: white;
    border: none;
    font-weight: 600;
}
QPushButton#Primary:hover { background: #238A7E; }
QPushButton#InfoBtn {
    min-width: 26px;
    max-width: 26px;
    min-height: 26px;
    max-height: 26px;
    border-radius: 13px;
    padding: 0;
    font-weight: 700;
    color: #3D5A80;
}

QFrame#Card {
    background: #FFFFFF;
    border: 1px solid #E2DDD4;
    border-radius: 10px;
}
QFrame#NodeCard {
    background: #FFFFFF;
    border: 1px solid #E2DDD4;
    border-radius: 10px;
}
QFrame#NodeCard:hover { border-color: #2A9D8F; }
QFrame#NodeCard[selected="true"] {
    border: 2px solid #2A9D8F;
}
QFrame#ChoiceChip {
    background: #FFFFFF;
    border: 1px solid #D5D0C7;
    border-radius: 8px;
}
QFrame#ChoiceChip[selected="true"] {
    background: #E7F4F1;
    border: 2px solid #2A9D8F;
}

QProgressBar {
    border: none;
    background: #E2DDD4;
    border-radius: 6px;
    text-align: center;
    color: #1B3A4B;
    height: 16px;
}
QProgressBar::chunk {
    background: #2A9D8F;
    border-radius: 6px;
}

QListWidget {
    background: transparent;
    border: none;
}
QListWidget::item {
    padding: 10px 8px;
    border-radius: 8px;
    margin: 2px 4px;
}
QListWidget::item:selected {
    background: #1B3A4B;
    color: #F4F1EA;
}
QListWidget::item:hover:!selected { background: #E7F4F1; }

QScrollArea { border: none; background: transparent; }
QSplitter::handle { background: #E2DDD4; }
QCheckBox { spacing: 8px; }
"""
