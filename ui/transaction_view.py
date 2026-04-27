import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QDateEdit, QHeaderView, QFormLayout, 
                             QMessageBox, QSpinBox, QDialog)
from PyQt6.QtCore import Qt, QDate
from utils.translator import tr

class TransactionView(QWidget):
    def __init__(self, t_type, controller, main_window=None):
        super().__init__()
        self.t_type = t_type
        self.controller = controller
        self.main_window = main_window
        self.categories = []
        self.transactions = []  # cached for edit dialog lookup
        
        self.init_ui()
        self.load_categories()
        self.load_transactions()

    def _notify_dashboard(self):
        if self.main_window and hasattr(self.main_window, 'dashboard_view'):
            self.main_window.dashboard_view.refresh_data()

    @staticmethod
    def _is_recurring_tx(tx):
        return tx.recurrence_type not in (None, "", "one_time")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        self.setLayout(layout)

        header_layout = QHBoxLayout()
        type_es = tr("INCOMES") if self.t_type == "income" else tr("EXPENSES")
        title = QLabel(f'{tr("MANAGE_INCOMES" if self.t_type == "income" else "MANAGE_EXPENSES")}')
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 6px;")
        header_layout.addWidget(title)

        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet("border-radius: 12px; border: 1px solid #3498DB; color: #3498DB; font-weight: bold; background-color: transparent; margin-left: 10px;")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header_layout.addWidget(btn_help)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Form
        form_layout = QHBoxLayout()
        
        # Left form
        left_form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr("DESC_PLACEHOLDER"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        
        self.cat_combo = QComboBox()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        
        left_form.addRow("Nombre:", self.name_input)
        left_form.addRow("Cantidad (€):", self.amount_input)
        left_form.addRow("Categoría:", self.cat_combo)
        left_form.addRow("Fecha Inicial:", self.date_input)

        # Right form (Recurrence)
        right_form = QFormLayout()
        self.rec_type_combo = QComboBox()
        self.rec_type_combo.addItems([tr("ONE_TIME"), tr("RECURRING")])
        self.rec_type_combo.currentIndexChanged.connect(self.toggle_recurrence_fields)

        self.rec_interval_spin = QSpinBox()
        self.rec_interval_spin.setRange(1, 120)
        self.rec_interval_spin.setSuffix(" mes(es)")
        
        self.rec_duration_combo = QComboBox()
        self.rec_duration_combo.addItems([tr("INDEFINITE"), tr("CUSTOM_DURATION")])
        self.rec_duration_combo.currentIndexChanged.connect(self.toggle_recurrence_fields)
        
        self.rec_duration_spin = QSpinBox()
        self.rec_duration_spin.setRange(1, 1200)
        self.rec_duration_spin.setSuffix(" vez/veces")

        right_form.addRow("Tipo:", self.rec_type_combo)
        right_form.addRow("Cada:", self.rec_interval_spin)
        right_form.addRow("Duración:", self.rec_duration_combo)
        right_form.addRow("Por:", self.rec_duration_spin)

        form_layout.addLayout(left_form)
        form_layout.addLayout(right_form)
        layout.addLayout(form_layout)

        self.toggle_recurrence_fields()

        # Add Button
        self.add_btn = QPushButton(f"Añadir {type_es}")
        self.add_btn.setProperty("class", "action-btn")
        self.add_btn.clicked.connect(self.add_transaction)
        layout.addWidget(self.add_btn)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", tr("CONCEPT"), tr("AMOUNT"), tr("CATEGORY"), tr("DATE"), tr("RECURRENCE"), tr("ACTIONS")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 160)
        self.table.hideColumn(0)  # Hide ID
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.table)

    def show_help(self):
        t_label = tr("INCOMES") if self.t_type == "income" else tr("EXPENSES")
        msg = tr("HELP_TRANSACTIONS")
        QMessageBox.information(self, tr("HELP") + ": " + t_label, msg)

    def toggle_recurrence_fields(self):
        is_recurring = self.rec_type_combo.currentText() == tr("RECURRING")
        is_custom_duration = self.rec_duration_combo.currentText() == tr("CUSTOM_DURATION")

        self.rec_interval_spin.setEnabled(is_recurring)
        self.rec_duration_combo.setEnabled(is_recurring)
        self.rec_duration_spin.setEnabled(is_recurring and is_custom_duration)


    def load_categories(self):
        self.categories = self.controller.get_categories(self.t_type)
        self.cat_combo.clear()
        for cat in self.categories:
            self.cat_combo.addItem(cat.name, cat.id)

    def load_transactions(self):
        self.transactions = self.controller.get_transactions(self.t_type)
        self.table.setRowCount(0)

        for row_idx, tx in enumerate(self.transactions):
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, 44)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(tx.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(tx.name))

            amount_item = QTableWidgetItem(f"{tx.amount:.2f} €")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, amount_item)
            
            # Find category name
            cat_name = tr("UNKNOWN")
            for c in self.categories:
                if c.id == tx.category_id:
                    cat_name = c.name
                    break
                    
            self.table.setItem(row_idx, 3, QTableWidgetItem(cat_name))
            
            date_item = QTableWidgetItem(tx.date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, date_item)
            
            rec_text = tr("ONE_TIME")
            if self._is_recurring_tx(tx):
                dur_text = tr("INDEFINITE") if tx.recurrence_duration is None else f"{tx.recurrence_duration} {tr('TIMES')}"
                rec_text = f"{tr('RECURRING')} ({tx.recurrence_interval} {tr('MONTHS_INTERVAL')}, {dur_text})"
            
            self.table.setItem(row_idx, 5, QTableWidgetItem(rec_text))

            # Action buttons: EDITAR + ELIMINAR
            edit_btn = QPushButton(tr("EDIT"))
            edit_btn.setProperty("role", "table-pay")
            edit_btn.setFixedHeight(30)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, t_id=tx.id: self.show_edit_dialog(t_id))

            del_btn = QPushButton(tr("DELETE"))
            del_btn.setProperty("role", "table-delete")
            del_btn.setFixedHeight(30)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda checked, t_id=tx.id: self.delete_transaction(t_id))

            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row_idx, 6, btn_container)

    def add_transaction(self):
        name = self.name_input.text().strip()
        amount_text = self.amount_input.text().strip()
        cat_id = self.cat_combo.currentData()
        date_str = self.date_input.date().toString("yyyy-MM-dd")

        if not name or not amount_text:
            QMessageBox.warning(self, tr("ERROR"), tr("NAME_AMT_MANDATORY"))
            return
            
        try:
            amount = float(amount_text.replace(',', '.'))
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, tr("ERROR"), tr("INVALID_QTY"))
            return

        is_recurring = self.rec_type_combo.currentText() == tr("RECURRING")
        if not is_recurring:
            r_type = 'one_time'
            r_interval = 1
            r_duration = None
        else:
            r_type = 'custom'
            r_interval = self.rec_interval_spin.value()
            is_custom_duration = self.rec_duration_combo.currentText() == tr("CUSTOM_DURATION")
            r_duration = self.rec_duration_spin.value() if is_custom_duration else None

        self.controller.add_transaction(
            self.t_type, cat_id, name, amount, date_str, 
            r_type, r_interval, r_duration
        )

        self.name_input.clear()
        self.amount_input.clear()
        self.load_transactions()
        self._notify_dashboard()

    def show_edit_dialog(self, t_id):
        tx = next((t for t in self.transactions if t.id == t_id), None)
        if tx is None:
            return

        dialog_title = f'{tr("EDIT")} {tr("INCOMES") if self.t_type == "income" else tr("EXPENSES")}'

        dialog = QDialog(self)
        dialog.setWindowTitle(dialog_title)
        dialog.setFixedWidth(460)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        d_name = QLineEdit(tx.name)
        d_amount = QLineEdit(str(tx.amount))

        d_cat = QComboBox()
        for cat in self.categories:
            d_cat.addItem(cat.name, cat.id)
            if cat.id == tx.category_id:
                d_cat.setCurrentIndex(d_cat.count() - 1)

        d_date = QDateEdit()
        d_date.setCalendarPopup(True)
        try:
            qd = QDate.fromString(tx.date, "yyyy-MM-dd")
            d_date.setDate(qd if qd.isValid() else QDate.currentDate())
        except Exception:
            d_date.setDate(QDate.currentDate())

        d_rec_type = QComboBox()
        d_rec_type.addItems([tr("ONE_TIME"), tr("RECURRING")])
        is_rec = self._is_recurring_tx(tx)
        d_rec_type.setCurrentIndex(1 if is_rec else 0)

        d_interval = QSpinBox()
        d_interval.setRange(1, 120)
        d_interval.setSuffix(f" {tr('MONTHS_INTERVAL')}")
        d_interval.setValue(tx.recurrence_interval or 1)

        d_dur_type = QComboBox()
        d_dur_type.addItems([tr("INDEFINITE"), tr("CUSTOM_DURATION")])
        has_duration = tx.recurrence_duration is not None
        d_dur_type.setCurrentIndex(1 if has_duration else 0)

        d_duration = QSpinBox()
        d_duration.setRange(1, 1200)
        d_duration.setSuffix(f" {tr('TIMES')}")
        d_duration.setValue(tx.recurrence_duration or 1)

        form.addRow(tr("NAME_LABEL", "Nombre:"), d_name)
        form.addRow(tr("AMOUNT_LABEL", "Importe (€):"), d_amount)
        form.addRow(tr("CATEGORY_LABEL", "Categoría:"), d_cat)
        form.addRow(tr("DATE_LABEL", "Fecha:"), d_date)
        form.addRow(tr("TYPE_LABEL", "Tipo:"), d_rec_type)
        form.addRow(tr("EVERY_LABEL", "Cada:"), d_interval)
        form.addRow(tr("DURATION_LABEL", "Duración:"), d_dur_type)
        form.addRow(tr("FOR_LABEL", "Por:"), d_duration)

        def sync_rec_fields():
            recurring = d_rec_type.currentText() == tr("RECURRING")
            custom = d_dur_type.currentText() == tr("CUSTOM_DURATION")
            d_interval.setEnabled(recurring)
            d_dur_type.setEnabled(recurring)
            d_duration.setEnabled(recurring and custom)

        d_rec_type.currentIndexChanged.connect(sync_rec_fields)
        d_dur_type.currentIndexChanged.connect(sync_rec_fields)
        sync_rec_fields()

        save_btn = QPushButton(tr("SAVE_CHANGES"))
        save_btn.setProperty("class", "action-btn")

        outer.addLayout(form)
        outer.addWidget(save_btn)

        def save():
            name = d_name.text().strip()
            amount_str = d_amount.text().strip().replace(',', '.')
            cat_id = d_cat.currentData()
            date_str = d_date.date().toString("yyyy-MM-dd")

            if not name or not amount_str:
                QMessageBox.warning(dialog, tr("ERROR"), tr("NAME_AMT_MANDATORY"))
                return
            try:
                amt = float(d_amount.text().replace(',', '.'))
                if amt <= 0:
                    raise ValueError
            except:
                QMessageBox.warning(dialog, tr("ERROR"), tr("INVALID_QTY"))
                return

            recurring = d_rec_type.currentText() == tr("RECURRING")
            if not recurring:
                r_type, r_interval, r_duration = 'one_time', 1, None
            else:
                r_type = 'custom'
                r_interval = d_interval.value()
                r_duration = d_duration.value() if d_dur_type.currentText() == tr("CUSTOM_DURATION") else None

            self.controller.update_transaction(t_id, cat_id, name, amt, date_str, r_type, r_interval, r_duration)
            self.load_transactions()
            self._notify_dashboard()
            dialog.accept()

        save_btn.clicked.connect(save)
        dialog.exec()

    def delete_transaction(self, t_id):
        type_es = "ingreso" if self.t_type == "income" else "gasto"
        reply = QMessageBox.question(
            self, 'Confirmar', f'¿Eliminar este {type_es}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_transaction(t_id)
            self.load_transactions()
            self._notify_dashboard()
