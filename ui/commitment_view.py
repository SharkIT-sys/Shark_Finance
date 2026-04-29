import math
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QDialog, QLineEdit,
                             QFormLayout, QMessageBox, QProgressBar, QSizePolicy,
                             QComboBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from dateutil.relativedelta import relativedelta as rdelta
from utils.translator import tr

class CommitmentView(QWidget):
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
        title = QLabel(tr("COMMITMENTS"))
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header_layout.addWidget(title)
        
        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet("border-radius: 12px; border: 1px solid #3498DB; color: #3498DB; font-weight: bold; background-color: transparent; margin-left: 10px;")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header_layout.addWidget(btn_help)
        
        header_layout.addStretch()
        
        # Add Commitment Button
        self.btn_add = QPushButton(tr("NEW_COMMITMENT"))
        self.btn_add.setProperty("class", "action-btn")
        self.btn_add.clicked.connect(self.show_add_dialog)
        header_layout.addWidget(self.btn_add)
        
        layout.addLayout(header_layout)
        
        # Summary Overview
        self.summary_widget = QWidget()
        summary_layout = QHBoxLayout(self.summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        
        self.total_pending_lbl = QLabel()
        self.total_pending_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #E74C3C;")
        
        self.time_eval_lbl = QLabel()
        self.time_eval_lbl.setStyleSheet("font-size: 12px; color: #A0A0A0;")
        self.time_eval_lbl.setWordWrap(True)
        
        summary_layout.addWidget(self.total_pending_lbl)
        summary_layout.addSpacing(20)
        summary_layout.addWidget(self.time_eval_lbl, 1)
        
        layout.addWidget(self.summary_widget)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([tr("NAME"), tr("TOTAL"), tr("PROGRESS"), tr("PENDING"), tr("ESTIMATED_END"), tr("ACTIONS")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 110)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 260)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        
        layout.addWidget(self.table)

    def _estimate_end_date(self, remaining, payments):
        """Estimate end date based on payment history. Returns datetime or None."""
        if remaining <= 0 or not payments:
            return None
        sorted_pays = sorted(payments, key=lambda p: p[3])  # sort by date str
        amounts = [p[2] for p in sorted_pays]
        if len(sorted_pays) == 1:
            avg_monthly = amounts[0]
            ref_date = datetime.strptime(sorted_pays[0][3], "%Y-%m-%d")
        else:
            last_date = datetime.strptime(sorted_pays[-1][3], "%Y-%m-%d")
            first_date = datetime.strptime(sorted_pays[0][3], "%Y-%m-%d")
            months_span = max(1, (last_date.year - first_date.year) * 12 + (last_date.month - first_date.month))
            avg_monthly = sum(amounts) / months_span
            ref_date = last_date
        if avg_monthly <= 0:
            return None
        months_to_go = math.ceil(remaining / avg_monthly)
        return ref_date + rdelta(months=months_to_go)

    def show_help(self):
        msg = tr("HELP_COMMITMENTS")
        QMessageBox.information(self, f'{tr("HELP")}: {tr("COMMITMENTS")}', msg)
        
    def refresh_data(self):
        summary = self.controller.get_commitments_summary()
        self.total_pending_lbl.setText(f"{tr('PENDING_GLOBAL')}: {summary['total_pending']:.2f} €")
        
        if summary['avg_monthly_income'] > 0 and summary['total_pending'] > 0:
            months = summary['months_to_pay_estimation']
            if months != float('inf'):
                self.time_eval_lbl.setText(tr("GLOBAL_REMAINING_EVAL").format(months))
            else:
                self.time_eval_lbl.setText("")
        else:
            self.time_eval_lbl.setText("")
            
        commitments = self.controller.get_commitments_with_progress()
        
        self.table.setRowCount(len(commitments))
        for row, data in enumerate(commitments):
            c = data['commitment']
            self.table.setRowHeight(row, 48)
            
            # Name
            name_item = QTableWidgetItem(c.name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 0, name_item)
            
            # Total
            total_item = QTableWidgetItem(f"{c.total_amount:.2f} €")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, total_item)
            
            # Progress Bar
            progress = QProgressBar()
            progress.setRange(0, 100)
            pct = int(data['progress_pct'])
            progress.setValue(pct)
            progress.setFormat(f"{pct}%")
            progress.setTextVisible(True)
            progress.setStyleSheet("""
                QProgressBar {
                    background-color: #2A2A35;
                    border-radius: 5px;
                    border: none;
                    text-align: center;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    min-height: 22px;
                }
                QProgressBar::chunk {
                    background-color: #3498DB;
                    border-radius: 5px;
                }
            """)
            
            # Wrap progress bar in a centered container
            prog_container = QWidget()
            prog_layout = QHBoxLayout(prog_container)
            prog_layout.setContentsMargins(6, 8, 6, 8)
            prog_layout.addWidget(progress)
            self.table.setCellWidget(row, 2, prog_container)
            
            # Remaining
            rem_item = QTableWidgetItem(f"{data['remaining']:.2f} €")
            rem_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if data['remaining'] <= 0:
                rem_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 3, rem_item)
            
            # Fin estimado
            end_date = self._estimate_end_date(data['remaining'], data['payments'])
            if end_date and data['remaining'] > 0:
                end_item = QTableWidgetItem(end_date.strftime("%d/%m/%Y"))
                end_item.setForeground(Qt.GlobalColor.yellow)
            else:
                end_item = QTableWidgetItem(tr("LIQUIDATED") if data['remaining'] <= 0 else "—")
                if data['remaining'] <= 0:
                    end_item.setForeground(Qt.GlobalColor.green)
            end_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, end_item)

            # Actions — compact buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            btn_edit = QPushButton("✏️ " + tr("EDIT", "Editar"))
            btn_edit.setProperty("role", "table-edit")
            btn_edit.setFixedHeight(32)
            btn_edit.clicked.connect(lambda checked, c_id=c.id, name=c.name, amount=c.total_amount, date=c.date: self.show_edit_dialog(c_id, name, amount, date))
            actions_layout.addWidget(btn_edit)

            if data['remaining'] > 0:
                btn_plan = QPushButton(tr("PAYMENT_PLAN"))
                btn_plan.setProperty("role", "table-link")
                btn_plan.setFixedHeight(32)
                btn_plan.clicked.connect(lambda checked, c_id=c.id, name=c.name, rem=data['remaining']: self.show_payment_plan_dialog(c_id, name, rem))
                actions_layout.addWidget(btn_plan)

                btn_single = QPushButton(tr("SINGLE_PAYMENT"))
                btn_single.setProperty("role", "table-pay")
                btn_single.setFixedHeight(32)
                btn_single.clicked.connect(lambda checked, c_id=c.id, name=c.name, rem=data['remaining']: self.show_single_payment_dialog(c_id, name, rem))
                actions_layout.addWidget(btn_single)

            btn_delete = QPushButton(tr("DELETE"))
            btn_delete.setProperty("role", "table-delete")
            btn_delete.setFixedHeight(32)
            btn_delete.clicked.connect(lambda checked, c_id=c.id: self.delete_commitment(c_id))
            actions_layout.addWidget(btn_delete)

            self.table.setCellWidget(row, 5, actions_widget)

    def show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("NEW_COMMITMENT"))
        dialog.setFixedWidth(380)
        
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        name_input = QLineEdit()
        amount_input = QLineEdit()
        amount_input.setPlaceholderText("0.00")
        
        layout.addRow(f'{tr("NAME")}:', name_input)
        layout.addRow(f'{tr("AMOUNT")}:', amount_input)
        
        btn_save = QPushButton(tr("SAVE_COMMITMENT"))
        btn_save.setProperty("class", "action-btn")
        layout.addRow(btn_save)
        
        def save():
            name = name_input.text().strip()
            amount_str = amount_input.text().strip().replace(',', '.')
            if not name or not amount_str:
                QMessageBox.warning(dialog, tr("ERROR"), tr("FILL_ALL_FIELDS"))
                return
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError
                date = datetime.now().strftime("%Y-%m-%d")
                self.controller.add_commitment(name, amount, date)
                self.refresh_data()
                dialog.accept()
            except ValueError:
                QMessageBox.warning(dialog, tr("ERROR"), tr("INVALID_AMOUNT"))
                
        btn_save.clicked.connect(save)
        dialog.exec()

    def show_edit_dialog(self, c_id, current_name, current_amount, current_date):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("EDIT", "Editar") + " " + tr("COMMITMENT", "Compromiso"))
        dialog.setFixedWidth(380)
        
        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        name_input = QLineEdit()
        name_input.setText(current_name)
        
        amount_input = QLineEdit()
        amount_input.setText(f"{current_amount:.2f}")
        
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.fromString(current_date, "yyyy-MM-dd"))
        
        layout.addRow(f'{tr("NAME")}:', name_input)
        layout.addRow(f'{tr("AMOUNT")}:', amount_input)
        layout.addRow(f'{tr("DATE")}:', date_input)
        
        btn_save = QPushButton(tr("SAVE", "Guardar"))
        btn_save.setProperty("class", "action-btn")
        layout.addRow(btn_save)
        
        def save():
            name = name_input.text().strip()
            amount_str = amount_input.text().strip().replace(',', '.')
            date_str = date_input.date().toString("yyyy-MM-dd")
            if not name or not amount_str:
                QMessageBox.warning(dialog, tr("ERROR"), tr("FILL_ALL_FIELDS"))
                return
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError
                self.controller.update_commitment(c_id, name, amount, date_str)
                self.refresh_data()
                dialog.accept()
                QMessageBox.information(self, tr("SUCCESS", "Éxito"), tr("COMMITMENT_UPDATED", "Compromiso actualizado correctamente."))
            except ValueError:
                QMessageBox.warning(dialog, tr("ERROR"), tr("INVALID_AMOUNT"))
                
        btn_save.clicked.connect(save)
        dialog.exec()

    def show_payment_plan_dialog(self, c_id, commitment_name, remaining):
        """Creates a RECURRING expense linked to this commitment."""
        from PyQt6.QtWidgets import QSpinBox
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{tr('PAYMENT_PLAN')} — {commitment_name}")
        dialog.setFixedWidth(440)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        info = QLabel(f"{tr('PENDING_TOTAL')} <b>{remaining:.2f} €</b>")
        info.setStyleSheet("color: #E74C3C; font-size: 13px;")
        layout.addRow(info)

        desc_lbl = QLabel(tr("PAYMENT_PLAN_DESC"))
        desc_lbl.setStyleSheet("color: #888; font-size: 12px;")
        desc_lbl.setWordWrap(True)
        layout.addRow(desc_lbl)

        name_input = QLineEdit()
        name_input.setText(f"{tr('FEES')} {commitment_name}")
        layout.addRow(f"{tr('CONCEPT')}:", name_input)

        amount_input = QLineEdit()
        amount_input.setPlaceholderText(tr("INSTALLMENT_AMOUNT"))
        layout.addRow(tr("INSTALLMENT_AMOUNT_LABEL"), amount_input)

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
        duration_spin.setSuffix(f" {tr('FEES')}")
        layout.addRow(tr("NUM_INSTALLMENTS"), duration_spin)

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        layout.addRow(tr("START_DATE"), date_input)

        # Live "Fecha última cuota" label
        last_date_lbl = QLabel()
        last_date_lbl.setStyleSheet(
            "color: #3498DB; font-weight: bold; font-size: 13px; padding: 2px 0;"
        )
        layout.addRow(f"\U0001f4cc {tr('LAST_INSTALLMENT_DATE')}", last_date_lbl)

        def auto_calc_duration():
            """Auto-set number of installments based on installment amount and remaining."""
            try:
                cuota = float(amount_input.text().strip().replace(',', '.'))
                if cuota > 0:
                    cuotas = math.ceil(remaining / cuota)
                    # Block signals to avoid feedback loop with update_last_date triggering again
                    duration_spin.blockSignals(True)
                    duration_spin.setValue(min(cuotas, 360))
                    duration_spin.blockSignals(False)
                    update_last_date()  # refresh date after setting duration
            except (ValueError, ZeroDivisionError):
                pass

        def update_last_date():
            start = date_input.date().toPyDate()
            offset_months = interval_spin.value() * (duration_spin.value() - 1)
            last = start + rdelta(months=offset_months)
            last_date_lbl.setText(last.strftime("%d / %m / %Y"))

        amount_input.textChanged.connect(auto_calc_duration)
        interval_spin.valueChanged.connect(update_last_date)
        duration_spin.valueChanged.connect(update_last_date)
        date_input.dateChanged.connect(update_last_date)
        update_last_date()  # populate on open

        btn_save = QPushButton(tr("CREATE_PAYMENT_PLAN"))
        btn_save.setProperty("class", "action-btn")
        layout.addRow(btn_save)

        def save():
            name = name_input.text().strip()
            amount_str = amount_input.text().strip().replace(',', '.')
            cat_id = cat_combo.currentData()
            interval = interval_spin.value()
            duration = duration_spin.value()
            date_str = date_input.date().toString("yyyy-MM-dd")

            if not name or not amount_str:
                QMessageBox.warning(dialog, tr("ERROR"), tr("FILL_ALL_FIELDS"))
                return
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(dialog, tr("ERROR"), tr("INVALID_AMOUNT"))
                return

            total_plan = amount * duration
            if total_plan > remaining:
                QMessageBox.warning(
                    dialog, tr("PLAN_EXCEEDS_PENDING"),
                    tr("PLAN_EXCEEDS_MSG").format(duration, amount, total_plan, remaining)
                )
                return

            # Confirmation with first and last date
            start_dt = datetime.strptime(date_str, "%Y-%m-%d")
            last_dt = start_dt + rdelta(months=interval * (duration - 1))

            self.controller.add_transaction(
                'expense', cat_id, name, amount, date_str,
                'custom', interval, duration
            )
            self.controller.add_commitment_payment(c_id, amount, date_str)

            self.refresh_data()
            dialog.accept()
            QMessageBox.information(
                self, tr("PLAN_CREATED"),
                tr("PLAN_CREATED_MSG").format(duration, amount, start_dt.strftime('%d/%m/%Y'), last_dt.strftime('%d/%m/%Y'))
            )

        btn_save.clicked.connect(save)
        dialog.exec()

    def show_single_payment_dialog(self, c_id, commitment_name, remaining):
        """Creates a one-time expense and registers a single payment against the commitment."""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("SINGLE_CONTRIBUTION_TITLE").format(commitment_name))
        dialog.setFixedWidth(400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        info = QLabel(f"Pendiente: <b>{remaining:.2f} €</b>")
        info.setStyleSheet("color: #E74C3C; font-size: 13px;")
        layout.addRow(info)

        name_input = QLineEdit()
        name_input.setText(f"{tr('SINGLE_PAYMENT')} {commitment_name}")
        layout.addRow(tr("EXPENSE_CONCEPT_LABEL"), name_input)
        
        amount_input = QLineEdit()
        amount_input.setPlaceholderText(tr("MAX_REMAINING").format(remaining))
        layout.addRow(f"{tr('AMOUNT')} (€):", amount_input)

        cat_combo = QComboBox()
        for cat in self.controller.get_categories("expense"):
            cat_combo.addItem(cat.name, cat.id)
        layout.addRow("Categoría:", cat_combo)

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        layout.addRow(tr("DATE"), date_input)
        
        btn_save = QPushButton(f"💶 {tr('REG_CONTRIBUTION')}")
        btn_save.setProperty("class", "action-btn")
        layout.addRow(btn_save)

        def save():
            name = name_input.text().strip()
            amount_str = amount_input.text().strip().replace(',', '.')
            cat_id = cat_combo.currentData()
            date_str = date_input.date().toString("yyyy-MM-dd")

            if not name or not amount_str:
                QMessageBox.warning(dialog, tr("ERROR"), tr("FILL_ALL_FIELDS"))
                return
            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(dialog, tr("ERROR"), tr("INVALID_AMOUNT"))
                return

            if amount > remaining:
                reply = QMessageBox.question(
                    dialog, tr("PLAN_EXCEEDS_PENDING"),
                    tr("EXCEEDS_PENDING_CONFIRM").format(amount, remaining),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            self.controller.add_transaction('expense', cat_id, name, amount, date_str, 'one_time', 1, None)
            self.controller.add_commitment_payment(c_id, amount, date_str)

            self.refresh_data()
            dialog.accept()
            QMessageBox.information(
                self, tr("CONTRIBUTION_REG"),
                tr("CONTRIBUTION_REG_MSG").format(amount, commitment_name)
            )

        btn_save.clicked.connect(save)
        dialog.exec()
        
    def delete_commitment(self, c_id):
        reply = QMessageBox.question(
            self, tr("CONFIRM"), 
            tr("DELETE_COMMITMENT_CONFIRM"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_commitment(c_id)
            self.refresh_data()
