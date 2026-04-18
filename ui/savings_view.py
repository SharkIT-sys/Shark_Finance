import math
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QDialog, QLineEdit,
                             QFormLayout, QMessageBox, QProgressBar, QSizePolicy,
                             QComboBox, QDateEdit, QCheckBox)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from dateutil.relativedelta import relativedelta as rdelta
from utils.translator import tr

class SavingsView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(tr("SAVINGS"))
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header_layout.addWidget(title)
        
        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet("border-radius: 12px; border: 1px solid #2ECC71; color: #2ECC71; font-weight: bold; background-color: transparent; margin-left: 10px;")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header_layout.addWidget(btn_help)
        
        header_layout.addStretch()
        
        # Add Savings Button
        self.btn_add = QPushButton(tr("NEW_SAVINGS_GOAL"))
        self.btn_add.setProperty("class", "action-btn")
        self.btn_add.setStyleSheet("background-color: #2ECC71; color: white;") # Green for savings
        self.btn_add.clicked.connect(self.show_add_dialog)
        header_layout.addWidget(self.btn_add)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([tr("NAME"), tr("TARGET"), tr("PROGRESS"), tr("TOTAL_SAVED"), tr("ACTIONS")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 260)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        
        layout.addWidget(self.table)

    def show_help(self):
        msg = tr("HELP_SAVINGS")
        QMessageBox.information(self, f'{tr("HELP")}: {tr("SAVINGS")}', msg)
        
    def refresh_data(self):
        goals = self.controller.get_savings_goals_with_progress()
        
        self.table.setRowCount(len(goals))
        for row, data in enumerate(goals):
            g = data['goal']
            self.table.setRowHeight(row, 48)
            
            # Name
            name_item = QTableWidgetItem(g.name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 0, name_item)
            
            # Target
            target_str = f"{g.target_amount:.2f} €" if g.target_amount > 0 else tr("NO_TARGET")
            target_item = QTableWidgetItem(target_str)
            target_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if g.target_amount == 0:
                target_item.setForeground(Qt.GlobalColor.cyan)
            self.table.setItem(row, 1, target_item)
            
            # Progress
            if g.target_amount > 0:
                progress = QProgressBar()
                progress.setRange(0, 100)
                pct = min(100, int(data['progress_pct']))
                progress.setValue(pct)
                progress.setFormat(f"{pct}%")
                progress.setTextVisible(True)
                progress.setStyleSheet("""
                    QProgressBar {
                        background-color: #2A2A35;
                        border-radius: 5px; border: none; text-align: center; color: white; font-size: 11px; font-weight: bold; min-height: 22px;
                    }
                    QProgressBar::chunk {
                        background-color: #2ECC71; border-radius: 5px;
                    }
                """)
                prog_container = QWidget()
                prog_layout = QHBoxLayout(prog_container)
                prog_layout.setContentsMargins(6, 8, 6, 8)
                prog_layout.addWidget(progress)
                self.table.setCellWidget(row, 2, prog_container)
            else:
                inf_label = QLabel("∞ (Acumulativo)")
                inf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                inf_label.setStyleSheet("color: #2ECC71; font-weight: bold;")
                self.table.setCellWidget(row, 2, inf_label)
            
            # Total Saved
            saved_item = QTableWidgetItem(f"{data['total_saved']:.2f} €")
            saved_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            saved_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 3, saved_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            btn_add = QPushButton(tr("CONTRIBUTE"))
            btn_add.setProperty("role", "table-pay")
            btn_add.setStyleSheet("background-color: #27AE60;")
            btn_add.setFixedHeight(32)
            btn_add.clicked.connect(lambda checked, s_id=g.id, name=g.name: self.show_contribution_dialog(s_id, name))
            actions_layout.addWidget(btn_add)

            btn_plan = QPushButton(tr("SAVINGS_PLAN"))
            btn_plan.setProperty("role", "table-link")
            btn_plan.setFixedHeight(32)
            btn_plan.clicked.connect(lambda checked, s_id=g.id, name=g.name: self.show_savings_plan_dialog(s_id, name))
            actions_layout.addWidget(btn_plan)

            btn_delete = QPushButton(tr("DELETE"))
            btn_delete.setProperty("role", "table-delete")
            btn_delete.setFixedHeight(32)
            btn_delete.clicked.connect(lambda checked, s_id=g.id: self.delete_goal(s_id))
            actions_layout.addWidget(btn_delete)

            self.table.setCellWidget(row, 4, actions_widget)

    def show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("NEW_SAVINGS_GOAL"))
        dialog.setFixedWidth(380)
        
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        name_input = QLineEdit()
        amount_input = QLineEdit()
        amount_input.setPlaceholderText("0.00")
        
        no_ceiling_check = QCheckBox(tr("NO_CEILING"))
        
        def toggle_amount(state):
            amount_input.setEnabled(state == 0) # if checked (state=2), disable input
            if state == 2:
                amount_input.setText("0")
        
        no_ceiling_check.stateChanged.connect(toggle_amount)
        
        layout.addRow(f'{tr("NAME")}:', name_input)
        layout.addRow(f'{tr("TARGET")}:', amount_input)
        layout.addRow("", no_ceiling_check)
        
        btn_save = QPushButton(tr("SAVE_GOAL"))
        btn_save.setProperty("class", "action-btn")
        btn_save.setStyleSheet("background-color: #2ECC71; color: white;")
        layout.addRow(btn_save)
        
        def save():
            name = name_input.text().strip()
            if no_ceiling_check.isChecked():
                amount = 0.0
            else:
                amount_str = amount_input.text().strip().replace(',', '.')
                try:
                    amount = float(amount_str)
                    if amount <= 0: raise ValueError
                except ValueError:
                    QMessageBox.warning(dialog, tr("ERROR"), tr("INVALID_AMOUNT"))
                    return
            
            if not name:
                QMessageBox.warning(dialog, tr("ERROR"), tr("FILL_ALL_FIELDS"))
                return
                
            date = datetime.now().strftime("%Y-%m-%d")
            self.controller.add_savings_goal(name, amount, date)
            self.refresh_data()
            dialog.accept()
                
        btn_save.clicked.connect(save)
        dialog.exec()

    def show_contribution_dialog(self, s_id, goal_name):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{tr('CONTRIBUTE')} — {goal_name}")
        dialog.setFixedWidth(400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        name_input = QLineEdit()
        name_input.setText(f"{tr('CONTRIBUTION')} {goal_name}")
        layout.addRow(tr("CONCEPT"), name_input)
        
        amount_input = QLineEdit()
        amount_input.setPlaceholderText("0.00")
        layout.addRow(f"{tr('AMOUNT')} (€):", amount_input)

        cat_combo = QComboBox()
        # Find or use 'Ahorro' category if it exists, or provide list
        all_cats = self.controller.get_categories("expense")
        savings_cat_id = -1
        for i, cat in enumerate(all_cats):
            cat_combo.addItem(cat.name, cat.id)
            if "ahorro" in cat.name.lower() or "hucha" in cat.name.lower():
                savings_cat_id = i
        
        if savings_cat_id != -1:
            cat_combo.setCurrentIndex(savings_cat_id)
        layout.addRow(tr("CATEGORY"), cat_combo)

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        layout.addRow(tr("DATE"), date_input)
        
        btn_save = QPushButton(f"💰 {tr('REG_CONTRIBUTION')}")
        btn_save.setProperty("class", "action-btn")
        btn_save.setStyleSheet("background-color: #2ECC71; color: white;")
        layout.addRow(btn_save)

        def save():
            name = name_input.text().strip()
            amount_str = amount_input.text().strip().replace(',', '.')
            cat_id = cat_combo.currentData()
            date_str = date_input.date().toString("yyyy-MM-dd")

            if not name or not amount_str:
                return
            try:
                amount = float(amount_str)
                if amount <= 0: raise ValueError
            except: return

            # Record expense
            self.controller.add_transaction('expense', cat_id, name, amount, date_str, 'one_time', 1, None)
            # Record contribution
            self.controller.add_savings_contribution(s_id, amount, date_str)

            self.refresh_data()
            dialog.accept()

        btn_save.clicked.connect(save)
        dialog.exec()

    def show_savings_plan_dialog(self, s_id, goal_name):
        from PyQt6.QtWidgets import QSpinBox
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{tr('SAVINGS_PLAN')} — {goal_name}")
        dialog.setFixedWidth(440)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        name_input = QLineEdit()
        name_input.setText(f"{tr('SAVINGS_PLAN')} {goal_name}")
        layout.addRow(f"{tr('CONCEPT')}:", name_input)

        amount_input = QLineEdit()
        amount_input.setPlaceholderText("0.00")
        layout.addRow(tr("AMOUNT_PER_PERIOD"), amount_input)

        cat_combo = QComboBox()
        for cat in self.controller.get_categories("expense"):
            cat_combo.addItem(cat.name, cat.id)
        layout.addRow(f"{tr('CATEGORY')}:", cat_combo)

        interval_spin = QSpinBox()
        interval_spin.setRange(1, 24)
        interval_spin.setValue(1)
        interval_spin.setSuffix(f" {tr('MONTHS_INTERVAL')}")
        layout.addRow(tr("REPEAT_EVERY"), interval_spin)

        duration_spin = QSpinBox()
        duration_spin.setRange(1, 360)
        duration_spin.setValue(12)
        duration_spin.setSuffix(f" {tr('TIMES')}")
        layout.addRow(tr("DURATION"), duration_spin)

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        layout.addRow(tr("START_DATE"), date_input)

        btn_save = QPushButton(tr("CREATE_SAVINGS_PLAN"))
        btn_save.setProperty("class", "action-btn")
        btn_save.setStyleSheet("background-color: #2ECC71; color: white;")
        layout.addRow(btn_save)

        def save():
            name = name_input.text().strip()
            amount_str = amount_input.text().strip().replace(',', '.')
            cat_id = cat_combo.currentData()
            interval = interval_spin.value()
            duration = duration_spin.value()
            date_str = date_input.date().toString("yyyy-MM-dd")

            if not name or not amount_str: return
            try:
                amount = float(amount_str)
                if amount <= 0: raise ValueError
            except: return

            self.controller.add_transaction('expense', cat_id, name, amount, date_str, 'custom', interval, duration)
            self.controller.add_savings_contribution(s_id, amount, date_str)

            self.refresh_data()
            dialog.accept()

        btn_save.clicked.connect(save)
        dialog.exec()

    def delete_goal(self, s_id):
        reply = QMessageBox.question(self, tr("CONFIRM"), tr("DELETE_SAVINGS_CONFIRM"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_savings_goal(s_id)
            self.refresh_data()
