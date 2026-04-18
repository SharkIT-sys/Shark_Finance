from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame
from PyQt6.QtCore import Qt
from utils.translator import tr

class ManualView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(40, 40, 40, 40)
        c_layout.setSpacing(20)
        container.setLayout(c_layout)

        title = QLabel(f'📖 {tr("HELP")} Shark')
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF; margin-bottom: 20px;")
        c_layout.addWidget(title)

        sections = [
            (tr("MANUAL_Q1_T"), tr("MANUAL_Q1_A")),
            (tr("MANUAL_Q2_T"), tr("MANUAL_Q2_A")),
            (tr("MANUAL_Q3_T"), tr("MANUAL_Q3_A")),
            (tr("MANUAL_Q4_T"), tr("MANUAL_Q4_A")),
            (tr("MANUAL_Q5_T"), tr("MANUAL_Q5_A")),
            (tr("MANUAL_Q6_T"), tr("MANUAL_Q6_A")),
            (tr("MANUAL_Q7_T"), tr("MANUAL_Q7_A")),
            (tr("MANUAL_Q8_T"), tr("MANUAL_Q8_A")),
            (tr("MANUAL_Q9_T"), tr("MANUAL_Q9_A")),
            (tr("MANUAL_Q10_T"), tr("MANUAL_Q10_A")),
            (tr("MANUAL_Q11_T"), tr("MANUAL_Q11_A")),
            (tr("MANUAL_Q12_T"), tr("MANUAL_Q12_A")),
            (tr("MANUAL_Q13_T"), tr("MANUAL_Q13_A"))
        ]

        for sec_title, sec_desc in sections:
            card = QFrame()
            card.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 20px;")
            card_layout = QVBoxLayout()
            
            lbl_title = QLabel(sec_title)
            lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498DB; margin-bottom: 5px;")
            card_layout.addWidget(lbl_title)
            
            lbl_desc = QLabel(sec_desc)
            lbl_desc.setStyleSheet("font-size: 14px; color: #E0E0E0;")
            lbl_desc.setWordWrap(True)
            card_layout.addWidget(lbl_desc)
            
            card.setLayout(card_layout)
            c_layout.addWidget(card)

        c_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
