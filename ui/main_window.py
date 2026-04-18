import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QStackedWidget, QLabel)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

from ui.dashboard_view import DashboardView
from ui.transaction_view import TransactionView
from ui.category_view import CategoryView
from ui.historic_view import HistoricView
from ui.financial_health_view import FinancialHealthView
from ui.commitment_view import CommitmentView
from ui.savings_view import SavingsView
from ui.manual_view import ManualView
from ui.server_view import ServerView
from utils.translator import tr

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.setWindowTitle("Shark " + tr("ACCOUNTING", "Contabilidad"))
        self.resize(1000, 700)
        
        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "logo.png")
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "ui", "resources", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar.setLayout(sidebar_layout)
        
        # Logo placeholder (can be updated to an image)
        self.logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "resources", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # scale the pixmap to width 200, keep aspect ratio smooth
            self.logo_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo_label.setText("SHARK\n" + tr("ACCOUNTING", "CONTABILIDAD"))
            self.logo_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.logo_label)
        
        sidebar_layout.addSpacing(30)
        
        # Navigation Buttons
        self.btn_dashboard = QPushButton(tr("DASHBOARD"))
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        
        self.btn_incomes = QPushButton(tr("INCOMES"))
        self.btn_incomes.setCheckable(True)
        
        self.btn_expenses = QPushButton(tr("EXPENSES"))
        self.btn_expenses.setCheckable(True)
        
        self.btn_categories = QPushButton(tr("CATEGORY"))
        self.btn_categories.setCheckable(True)
        
        self.btn_historic = QPushButton(tr("HISTORIC"))
        self.btn_historic.setCheckable(True)
        
        self.btn_health = QPushButton(tr("FINANCIAL_HEALTH"))
        self.btn_health.setCheckable(True)
        
        self.btn_commitments = QPushButton(tr("COMMITMENTS"))
        self.btn_commitments.setCheckable(True)
        
        self.btn_savings = QPushButton(tr("SAVINGS"))
        self.btn_savings.setCheckable(True)
        
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_incomes)
        sidebar_layout.addWidget(self.btn_expenses)
        sidebar_layout.addWidget(self.btn_categories)
        sidebar_layout.addWidget(self.btn_historic)
        sidebar_layout.addWidget(self.btn_health)
        sidebar_layout.addWidget(self.btn_commitments)
        sidebar_layout.addWidget(self.btn_savings)
        sidebar_layout.addStretch()
        
        self.btn_manual = QPushButton(f'📖 {tr("HELP")} (Manual)')
        self.btn_manual.setStyleSheet("background-color: transparent; border: none; text-align: left; padding-left: 20px; font-size: 14px; color: #E0E0E0;")
        sidebar_layout.addWidget(self.btn_manual)
        
        self.btn_server = QPushButton(f'🌐 {tr("SERVER_CENTER")}')
        self.btn_server.setStyleSheet("background-color: transparent; border: none; text-align: left; padding-left: 20px; font-size: 14px; color: #F1C40F;")
        sidebar_layout.addWidget(self.btn_server)
        
        # Settings Button
        self.btn_settings = QPushButton(f'⚙ {tr("SETTINGS_ADVANCED")}')
        self.btn_settings.setStyleSheet("background-color: transparent; border: none; text-align: left; padding-left: 20px; font-size: 14px; color: #E0E0E0;")
        sidebar_layout.addWidget(self.btn_settings)

        
        # Connect navigation
        self.btn_dashboard.clicked.connect(lambda: self.switch_view(0))
        self.btn_incomes.clicked.connect(lambda: self.switch_view(1))
        self.btn_expenses.clicked.connect(lambda: self.switch_view(2))
        self.btn_categories.clicked.connect(lambda: self.switch_view(3))
        self.btn_historic.clicked.connect(lambda: self.switch_view(4))
        self.btn_health.clicked.connect(lambda: self.switch_view(5))
        self.btn_commitments.clicked.connect(lambda: self.switch_view(6))
        self.btn_savings.clicked.connect(lambda: self.switch_view(7))
        self.btn_manual.clicked.connect(lambda: self.switch_view(8))
        self.btn_server.clicked.connect(lambda: self.switch_view(9))
        self.btn_settings.clicked.connect(self.show_settings)
        
        main_layout.addWidget(sidebar)
        
        # Stacked Widget for Views
        self.stacked_widget = QStackedWidget()
        
        # Initialize views
        self.dashboard_view = DashboardView(self.controller)
        self.income_view = TransactionView("income", self.controller)
        self.expense_view = TransactionView("expense", self.controller)
        self.category_view = CategoryView(self.controller)
        self.historic_view = HistoricView(self.controller)
        self.health_view = FinancialHealthView(self.controller)
        self.commitments_view = CommitmentView(self.controller)
        self.savings_view = SavingsView(self.controller)
        self.manual_view = ManualView(self.controller)
        self.server_view = ServerView(self.controller)
        
        self.stacked_widget.addWidget(self.dashboard_view)
        self.stacked_widget.addWidget(self.income_view)
        self.stacked_widget.addWidget(self.expense_view)
        self.stacked_widget.addWidget(self.category_view)
        self.stacked_widget.addWidget(self.historic_view)
        self.stacked_widget.addWidget(self.health_view)
        self.stacked_widget.addWidget(self.commitments_view)
        self.stacked_widget.addWidget(self.savings_view)
        self.stacked_widget.addWidget(self.manual_view)
        self.stacked_widget.addWidget(self.server_view)
        
        main_layout.addWidget(self.stacked_widget)
        
        self.switch_view(0)

    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)

        nav_buttons = [
            self.btn_dashboard,
            self.btn_incomes,
            self.btn_expenses,
            self.btn_categories,
            self.btn_historic,
            self.btn_health,
            self.btn_commitments,
            self.btn_savings,
        ]

        for idx, button in enumerate(nav_buttons):
            button.setChecked(idx == index)

        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, "refresh_data"):
            current_widget.refresh_data()
        elif hasattr(current_widget, "load_transactions"):
            current_widget.load_transactions()
        elif hasattr(current_widget, "load_categories"):
            current_widget.load_categories()

    def showEvent(self, event):
        super().showEvent(event)
        self.check_legal_aviso()

    def check_legal_aviso(self):
        if self.controller.db.get_config('legal_accepted') == 'true':
            return
            
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Información importante")
        dialog.setModal(True)
        dialog.resize(400, 300)
        dialog.setStyleSheet("background-color: #1E1E24; color: white;")
        
        layout = QVBoxLayout(dialog)
        
        text = (
            "Esta aplicación se proporciona 'tal cual', sin garantías de ningún tipo.\n"
            "El uso del software es responsabilidad del usuario.\n\n"
            "El código se distribuye bajo licencia MIT.\n"
            "El nombre, marca e identidad visual están protegidos y no pueden usarse sin autorización.\n\n"
            "No se recopilan datos personales ni se envía información a servidores externos."
        )
        
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(lbl)
        
        btn = QPushButton("Aceptar y continuar")
        btn.setStyleSheet("background-color: #3498DB; color: white; border-radius: 5px; padding: 10px; font-weight: bold;")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()
        self.controller.db.set_config('legal_accepted', 'true')

    def show_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.controller, self)
        dialog.exec()

    def closeEvent(self, event):
        from utils.sync_manager import SyncManager
        sync_man = SyncManager(self.controller.db)
        sync_man.sync_bidirectional()
        event.accept()
