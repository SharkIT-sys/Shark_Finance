import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                             QComboBox, QDateEdit, QHeaderView, QFormLayout,
                             QMessageBox, QSpinBox, QDialog, QTabWidget,
                             QGridLayout, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QDate
from utils.translator import tr, Translator


class ExpenseView(QWidget):
    """
    Expense management view split into two tabs:
      - Tab 1: Recurring expenses
      - Tab 2: One-time expenses organised by month
    """

    def __init__(self, controller, main_window=None):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.categories = []
        self.all_expenses = []

        now = datetime.datetime.now()
        self.selected_year = now.year
        self.selected_month = now.month

        self.init_ui()
        self.load_categories()
        self.load_all_expenses()

    # ──────────────────── helpers ────────────────────
    @staticmethod
    def _is_recurring(tx):
        return tx.recurrence_type not in (None, "", "one_time")

    def _notify_dashboard(self):
        if self.main_window and hasattr(self.main_window, 'dashboard_view'):
            self.main_window.dashboard_view.refresh_data()

    # ──────────────────── UI ────────────────────
    def init_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)
        self.setLayout(root)

        # Header
        header = QHBoxLayout()
        title = QLabel(tr("MANAGE_EXPENSES"))
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 6px;")
        header.addWidget(title)

        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet(
            "border-radius: 12px; border: 1px solid #3498DB; color: #3498DB; "
            "font-weight: bold; background-color: transparent; margin-left: 10px;"
        )
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header.addWidget(btn_help)
        header.addStretch()
        root.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs)

        # ── Tab 1: Recurrentes ──
        self.tab_recurring = QWidget()
        self._build_recurring_tab()
        self.tabs.addTab(self.tab_recurring, f"🔄  {tr('RECURRING_EXPENSES')}")

        # ── Tab 2: Puntuales ──
        self.tab_onetime = QWidget()
        self._build_onetime_tab()
        self.tabs.addTab(self.tab_onetime, f"📌  {tr('ONETIME_EXPENSES')}")

    # ───────────── Tab 1: Recurrentes ─────────────
    def _build_recurring_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)
        self.tab_recurring.setLayout(layout)

        # Form
        form_layout = QHBoxLayout()
        left_form = QFormLayout()
        self.rec_name = QLineEdit()
        self.rec_name.setPlaceholderText(tr("DESC_PLACEHOLDER"))
        self.rec_amount = QLineEdit()
        self.rec_amount.setPlaceholderText("0.00")
        self.rec_cat = QComboBox()
        self.rec_date = QDateEdit()
        self.rec_date.setCalendarPopup(True)
        self.rec_date.setDate(QDate.currentDate())

        left_form.addRow(f'{tr("NAME")}:', self.rec_name)
        left_form.addRow(f'{tr("AMOUNT")} (€):', self.rec_amount)
        left_form.addRow(f'{tr("CATEGORY")}:', self.rec_cat)
        left_form.addRow(f'{tr("DATE")}:', self.rec_date)

        right_form = QFormLayout()
        self.rec_interval = QSpinBox()
        self.rec_interval.setRange(1, 120)
        self.rec_interval.setSuffix(f" {tr('MONTHS_INTERVAL')}")

        self.rec_dur_combo = QComboBox()
        self.rec_dur_combo.addItems([tr("INDEFINITE"), tr("CUSTOM_DURATION")])
        self.rec_dur_combo.currentIndexChanged.connect(self._toggle_rec_duration)

        self.rec_dur_spin = QSpinBox()
        self.rec_dur_spin.setRange(1, 1200)
        self.rec_dur_spin.setSuffix(f" {tr('TIMES')}")

        right_form.addRow(f'{tr("REPEAT_EVERY")}', self.rec_interval)
        right_form.addRow(f'{tr("DURATION")}', self.rec_dur_combo)
        right_form.addRow("", self.rec_dur_spin)

        form_layout.addLayout(left_form)
        form_layout.addLayout(right_form)
        layout.addLayout(form_layout)
        self._toggle_rec_duration()

        add_btn = QPushButton(tr("ADD_RECURRING"))
        add_btn.setProperty("class", "action-btn")
        add_btn.clicked.connect(self._add_recurring)
        layout.addWidget(add_btn)

        # Table
        self.rec_table = QTableWidget()
        self.rec_table.setColumnCount(7)
        self.rec_table.setHorizontalHeaderLabels(
            ["ID", tr("CONCEPT"), tr("AMOUNT"), tr("CATEGORY"),
             tr("DATE"), tr("RECURRENCE"), tr("ACTIONS")]
        )
        self.rec_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rec_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.rec_table.setColumnWidth(6, 160)
        self.rec_table.hideColumn(0)
        self.rec_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.rec_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rec_table.verticalHeader().setVisible(False)
        self.rec_table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.rec_table)

    def _toggle_rec_duration(self):
        is_custom = self.rec_dur_combo.currentText() == tr("CUSTOM_DURATION")
        self.rec_dur_spin.setEnabled(is_custom)

    # ───────────── Tab 2: Puntuales ─────────────
    def _build_onetime_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)
        self.tab_onetime.setLayout(layout)

        # Form (simpler – no recurrence fields)
        form_layout = QHBoxLayout()
        left_form = QFormLayout()
        self.ot_name = QLineEdit()
        self.ot_name.setPlaceholderText(tr("DESC_PLACEHOLDER"))
        self.ot_amount = QLineEdit()
        self.ot_amount.setPlaceholderText("0.00")
        self.ot_cat = QComboBox()
        self.ot_date = QDateEdit()
        self.ot_date.setCalendarPopup(True)
        self.ot_date.setDate(QDate.currentDate())

        left_form.addRow(f'{tr("NAME")}:', self.ot_name)
        left_form.addRow(f'{tr("AMOUNT")} (€):', self.ot_amount)
        left_form.addRow(f'{tr("CATEGORY")}:', self.ot_cat)
        left_form.addRow(f'{tr("DATE")}:', self.ot_date)

        form_layout.addLayout(left_form)
        layout.addLayout(form_layout)

        add_btn = QPushButton(tr("ADD_ONETIME"))
        add_btn.setProperty("class", "action-btn")
        add_btn.clicked.connect(self._add_onetime)
        layout.addWidget(add_btn)

        # ── Year selector + Month grid ──
        month_section = QFrame()
        month_section.setStyleSheet(
            "QFrame { background-color: #1E1E24; border-radius: 12px; "
            "border: 1px solid #2C2C35; }"
        )
        ms_layout = QVBoxLayout()
        ms_layout.setContentsMargins(16, 12, 16, 12)
        ms_layout.setSpacing(10)
        month_section.setLayout(ms_layout)

        # Year row
        year_row = QHBoxLayout()
        self.prev_year_btn = QPushButton("◁")
        self.prev_year_btn.setFixedSize(32, 32)
        self.prev_year_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_year_btn.setStyleSheet(
            "QPushButton { background: #2A2A35; border-radius: 6px; color: white; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background: #3498DB; }"
        )
        self.prev_year_btn.clicked.connect(lambda: self._change_year(-1))

        self.year_label = QLabel(str(self.selected_year))
        self.year_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #E0E0E0;")
        self.year_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_year_btn = QPushButton("▷")
        self.next_year_btn.setFixedSize(32, 32)
        self.next_year_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_year_btn.setStyleSheet(
            "QPushButton { background: #2A2A35; border-radius: 6px; color: white; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background: #3498DB; }"
        )
        self.next_year_btn.clicked.connect(lambda: self._change_year(1))

        year_row.addStretch()
        year_row.addWidget(self.prev_year_btn)
        year_row.addWidget(self.year_label)
        year_row.addWidget(self.next_year_btn)
        year_row.addStretch()
        ms_layout.addLayout(year_row)

        # Month grid (4 columns × 3 rows)
        self.month_grid = QGridLayout()
        self.month_grid.setSpacing(6)
        self.month_buttons = []
        for i in range(12):
            month_num = i + 1
            month_name = Translator.get_month_name(month_num)[:3].upper()
            btn = QPushButton(month_name)
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, m=month_num: self._select_month(m))
            self.month_buttons.append(btn)
            self.month_grid.addWidget(btn, i // 4, i % 4)
        ms_layout.addLayout(self.month_grid)
        layout.addWidget(month_section)
        self._refresh_month_buttons()

        # Hint
        self.ot_hint = QLabel(tr("SELECT_MONTH"))
        self.ot_hint.setStyleSheet("color: #A0A0A0; font-size: 12px; margin-top: 4px;")
        layout.addWidget(self.ot_hint)

        # Table
        self.ot_table = QTableWidget()
        self.ot_table.setColumnCount(6)
        self.ot_table.setHorizontalHeaderLabels(
            ["ID", tr("CONCEPT"), tr("AMOUNT"), tr("CATEGORY"),
             tr("DATE"), tr("ACTIONS")]
        )
        self.ot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ot_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.ot_table.setColumnWidth(5, 160)
        self.ot_table.hideColumn(0)
        self.ot_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ot_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ot_table.verticalHeader().setVisible(False)
        self.ot_table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.ot_table)

    # ──────────────────── month selection ────────────────────
    def _change_year(self, delta):
        self.selected_year += delta
        self.year_label.setText(str(self.selected_year))
        self._refresh_month_buttons()
        self._load_onetime_table()

    def _select_month(self, month):
        self.selected_month = month
        self._refresh_month_buttons()
        self._load_onetime_table()

    def _refresh_month_buttons(self):
        now = datetime.datetime.now()
        for i, btn in enumerate(self.month_buttons):
            month_num = i + 1
            is_selected = (month_num == self.selected_month)
            is_current = (month_num == now.month and self.selected_year == now.year)

            if is_selected:
                btn.setStyleSheet(
                    "QPushButton { background: #3498DB; color: white; font-weight: bold; "
                    "border-radius: 8px; font-size: 12px; border: none; }"
                )
            elif is_current:
                btn.setStyleSheet(
                    "QPushButton { background: #2A2A35; color: #3498DB; font-weight: bold; "
                    "border-radius: 8px; font-size: 12px; border: 1px solid #3498DB; }"
                    "QPushButton:hover { background: #353545; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { background: #2A2A35; color: #A0A0A0; font-weight: bold; "
                    "border-radius: 8px; font-size: 12px; border: none; }"
                    "QPushButton:hover { background: #353545; color: white; }"
                )

    # ──────────────────── data loading ────────────────────
    def load_categories(self):
        self.categories = self.controller.get_categories("expense")
        self.rec_cat.clear()
        self.ot_cat.clear()
        for cat in self.categories:
            self.rec_cat.addItem(cat.name, cat.id)
            self.ot_cat.addItem(cat.name, cat.id)

    def load_all_expenses(self):
        self.all_expenses = self.controller.get_transactions("expense")
        self._load_recurring_table()
        self._load_onetime_table()

    def _load_recurring_table(self):
        recurring = [tx for tx in self.all_expenses if self._is_recurring(tx)]
        self._fill_table(self.rec_table, recurring, show_recurrence=True)

    def _load_onetime_table(self):
        onetime = []
        for tx in self.all_expenses:
            if not self._is_recurring(tx):
                try:
                    d = datetime.datetime.strptime(tx.date, "%Y-%m-%d")
                    if d.year == self.selected_year and d.month == self.selected_month:
                        onetime.append(tx)
                except ValueError:
                    pass
        self._fill_table(self.ot_table, onetime, show_recurrence=False)

        # Update hint
        month_name = Translator.get_month_name(self.selected_month)
        if onetime:
            self.ot_hint.setText(
                f"{month_name} {self.selected_year}  —  "
                f"{len(onetime)} {'gasto' if len(onetime) == 1 else 'gastos'}  ·  "
                f"{sum(tx.amount for tx in onetime):.2f} €"
            )
        else:
            self.ot_hint.setText(tr("NO_ONETIME_MONTH"))

    def _fill_table(self, table, transactions, show_recurrence=False):
        table.setRowCount(0)
        col_offset = 0 if show_recurrence else 0

        for row_idx, tx in enumerate(transactions):
            table.insertRow(row_idx)
            table.setRowHeight(row_idx, 44)
            table.setItem(row_idx, 0, QTableWidgetItem(str(tx.id)))
            table.setItem(row_idx, 1, QTableWidgetItem(tx.name))

            amount_item = QTableWidgetItem(f"{tx.amount:.2f} €")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 2, amount_item)

            cat_name = tr("UNKNOWN")
            for c in self.categories:
                if c.id == tx.category_id:
                    cat_name = c.name
                    break
            table.setItem(row_idx, 3, QTableWidgetItem(cat_name))

            date_item = QTableWidgetItem(tx.date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 4, date_item)

            if show_recurrence:
                dur_text = (tr("INDEFINITE") if tx.recurrence_duration is None
                            else f"{tx.recurrence_duration} {tr('TIMES')}")
                rec_text = f"{tx.recurrence_interval} {tr('MONTHS_INTERVAL')}, {dur_text}"
                table.setItem(row_idx, 5, QTableWidgetItem(rec_text))
                action_col = 6
            else:
                action_col = 5

            # Action buttons
            edit_btn = QPushButton(tr("EDIT"))
            edit_btn.setProperty("role", "table-pay")
            edit_btn.setFixedHeight(30)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, t_id=tx.id: self._show_edit_dialog(t_id))

            del_btn = QPushButton(tr("DELETE"))
            del_btn.setProperty("role", "table-delete")
            del_btn.setFixedHeight(30)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda checked, t_id=tx.id: self._delete_transaction(t_id))

            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            table.setCellWidget(row_idx, action_col, btn_container)

    # ──────────────────── add ────────────────────
    def _add_recurring(self):
        name = self.rec_name.text().strip()
        amount_text = self.rec_amount.text().strip()
        cat_id = self.rec_cat.currentData()
        date_str = self.rec_date.date().toString("yyyy-MM-dd")

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

        r_interval = self.rec_interval.value()
        is_custom = self.rec_dur_combo.currentText() == tr("CUSTOM_DURATION")
        r_duration = self.rec_dur_spin.value() if is_custom else None

        self.controller.add_transaction(
            "expense", cat_id, name, amount, date_str,
            "custom", r_interval, r_duration
        )
        self.rec_name.clear()
        self.rec_amount.clear()
        self.load_all_expenses()
        self._notify_dashboard()

    def _add_onetime(self):
        name = self.ot_name.text().strip()
        amount_text = self.ot_amount.text().strip()
        cat_id = self.ot_cat.currentData()
        date_str = self.ot_date.date().toString("yyyy-MM-dd")

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

        self.controller.add_transaction(
            "expense", cat_id, name, amount, date_str,
            "one_time", 1, None
        )
        self.ot_name.clear()
        self.ot_amount.clear()
        self.load_all_expenses()
        self._notify_dashboard()

    # ──────────────────── edit ────────────────────
    def _show_edit_dialog(self, t_id):
        tx = next((t for t in self.all_expenses if t.id == t_id), None)
        if tx is None:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f'{tr("EDIT")} {tr("EXPENSES")}')
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

        is_rec = self._is_recurring(tx)

        d_rec_type = QComboBox()
        d_rec_type.addItems([tr("ONE_TIME"), tr("RECURRING")])
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

        form.addRow(f'{tr("NAME")}:', d_name)
        form.addRow(f'{tr("AMOUNT")} (€):', d_amount)
        form.addRow(f'{tr("CATEGORY")}:', d_cat)
        form.addRow(f'{tr("DATE")}:', d_date)
        form.addRow(f'{tr("TYPE")}:', d_rec_type)
        form.addRow(f'{tr("REPEAT_EVERY")}', d_interval)
        form.addRow(f'{tr("DURATION")}', d_dur_type)
        form.addRow("", d_duration)

        def sync_rec():
            recurring = d_rec_type.currentText() == tr("RECURRING")
            custom = d_dur_type.currentText() == tr("CUSTOM_DURATION")
            d_interval.setEnabled(recurring)
            d_dur_type.setEnabled(recurring)
            d_duration.setEnabled(recurring and custom)

        d_rec_type.currentIndexChanged.connect(sync_rec)
        d_dur_type.currentIndexChanged.connect(sync_rec)
        sync_rec()

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
                amt = float(amount_str)
                if amt <= 0:
                    raise ValueError
            except Exception:
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
            self.load_all_expenses()
            self._notify_dashboard()
            dialog.accept()

        save_btn.clicked.connect(save)
        dialog.exec()

    # ──────────────────── delete ────────────────────
    def _delete_transaction(self, t_id):
        reply = QMessageBox.question(
            self, tr("CONFIRM"), '¿Eliminar este gasto?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_transaction(t_id)
            self.load_all_expenses()
            self._notify_dashboard()

    # ──────────────────── misc ────────────────────
    def show_help(self):
        msg = tr("HELP_TRANSACTIONS")
        QMessageBox.information(self, tr("HELP") + ": " + tr("EXPENSES"), msg)

    def refresh_data(self):
        """Called when navigating to this view."""
        self.load_categories()
        self.load_all_expenses()
