from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QMessageBox, QPushButton)
from PyQt6.QtCore import Qt
from utils.translator import tr

class FinancialHealthView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(tr("FINANCIAL_HEALTH"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet("border-radius: 12px; border: 1px solid #3498DB; color: #3498DB; font-weight: bold; background-color: transparent; margin-left: 10px;")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header_layout.addWidget(btn_help)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Main Grid for metrics
        grid = QGridLayout()
        grid.setSpacing(20)
        
        self.score_card = self.create_card(tr("GLOBAL_SCORE"), "")
        self.score_val = self.score_card.findChild(QLabel, "val")
        self.score_val.setStyleSheet("font-size: 32px; font-weight: bold;")
        
        self.savings_card = self.create_card(tr("SAVINGS_RATE"), "")
        self.savings_val = self.savings_card.findChild(QLabel, "val")
        
        self.avg_card = self.create_card(tr("MONTHLY_AVGS"), "")
        self.avg_val = self.avg_card.findChild(QLabel, "val")
        self.avg_val.setStyleSheet("font-size: 16px;")
        
        self.rule_card = self.create_card(tr("RULE_503020"), "")
        self.rule_val = self.rule_card.findChild(QLabel, "val")
        self.rule_val.setStyleSheet("font-size: 14px;")
        
        grid.addWidget(self.score_card, 0, 0)
        grid.addWidget(self.savings_card, 0, 1)
        grid.addWidget(self.avg_card, 1, 0)
        grid.addWidget(self.rule_card, 1, 1)
        
        layout.addLayout(grid)
        layout.addStretch()

    def create_card(self, title_text, value_text):
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout()
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel(title_text)
        title.setProperty("class", "card-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        val = QLabel(value_text)
        val.setObjectName("val") # to find it later
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l.addWidget(title)
        l.addWidget(val)
        card.setLayout(l)
        return card

    def show_help(self):
        msg = tr("HELP_HEALTH")
        QMessageBox.information(self, tr("HELP") + ": " + tr("FINANCIAL_HEALTH"), msg)

    def refresh_data(self):
        metrics = self.controller.get_financial_health_metrics()
        
        # Update Score
        score = metrics['score']
        self.score_val.setText(f"{score}/100")
        if score >= 80:
            self.score_val.setStyleSheet("font-size: 36px; font-weight: bold; color: #2ECC71;")
        elif score >= 50:
            self.score_val.setStyleSheet("font-size: 36px; font-weight: bold; color: #F1C40F;")
        else:
            self.score_val.setStyleSheet("font-size: 36px; font-weight: bold; color: #E74C3C;")
            
        # Update Savings Rate
        savings_rate = metrics['savings_rate']
        self.savings_val.setText(f"{savings_rate:.1f}%")
        if savings_rate >= 20:
             self.savings_val.setStyleSheet("font-size: 28px; font-weight: bold; color: #2ECC71;")
        elif savings_rate > 0:
             self.savings_val.setStyleSheet("font-size: 28px; font-weight: bold; color: #F1C40F;")
        else:
             self.savings_val.setStyleSheet("font-size: 28px; font-weight: bold; color: #E74C3C;")
             
        # Update Averages
        avg_text = (f"{tr('INCOMES')}: {metrics['avg_monthly_income']:.1f} € / mes\n"
                    f"{tr('EXPENSES')}: {metrics['avg_monthly_expense']:.1f} € / mes")
        self.avg_val.setText(avg_text)
        
        # Update 50/30/20 Rule
        rule_text = (f"{tr('NEEDS_PCT')}: {metrics['needs_pct']:.1f}%\n"
                     f"{tr('WANTS_PCT')}: {metrics['wants_pct']:.1f}%\n"
                     f"{tr('SAVINGS_PCT')}: {savings_rate:.1f}%")
        self.rule_val.setText(rule_text)
