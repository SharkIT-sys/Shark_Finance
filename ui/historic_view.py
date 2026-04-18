from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSizePolicy, QMessageBox, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from utils.translator import tr, Translator

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime


class HistoricView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)
        self.setLayout(outer)

        header_layout = QHBoxLayout()
        title = QLabel(tr("HISTORIC"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)

        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet("border-radius: 12px; border: 1px solid #3498DB; color: #3498DB; font-weight: bold; background-color: transparent; margin-left: 10px;")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header_layout.addWidget(btn_help)
        header_layout.addStretch()
        
        outer.addLayout(header_layout)

        # --- Tab widget ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2C2C35;
                border-radius: 8px;
                background-color: #1E1E24;
            }
            QTabBar::tab {
                background-color: #2A2A35;
                color: #A0A0A0;
                padding: 8px 20px;
                border-radius: 6px 6px 0 0;
                margin-right: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #353545;
                color: white;
            }
        """)
        outer.addWidget(self.tabs)

        self._build_total_tab()
        self._build_anual_tab()

    # ------------------------------------------------------------------ #
    #  TAB: TOTAL                                                          #
    # ------------------------------------------------------------------ #
    def _build_total_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Summary cards
        cards_layout = QHBoxLayout()
        self.total_income_val  = QLabel("0.00 €")
        self.total_expense_val = QLabel("0.00 €")
        self.total_balance_val = QLabel("0.00 €")
        self.total_income_val.setProperty("class",  "card-value positive-value")
        self.total_expense_val.setProperty("class", "card-value negative-value")
        self.total_balance_val.setProperty("class", "card-value")

        cards_layout.addWidget(self._make_card(tr("TOTAL_INCOME"),  self.total_income_val))
        cards_layout.addWidget(self._make_card(tr("TOTAL_EXPENSE"),    self.total_expense_val))
        cards_layout.addWidget(self._make_card(tr("TOTAL_BALANCE"), self.total_balance_val))
        layout.addLayout(cards_layout)

        # Line chart
        self.total_fig = Figure(figsize=(8, 4.5), facecolor='#1E1E24')
        self.total_fig.patch.set_facecolor('#1E1E24')
        self.total_canvas = FigureCanvas(self.total_fig)
        self.total_canvas.setStyleSheet("background-color: transparent;")
        self.total_ax = self.total_fig.add_subplot(111)
        self.total_ax.set_facecolor('#1E1E24')
        layout.addWidget(self.total_canvas)

        self.tabs.addTab(tab, tr("TAB_TOTAL"))

    # ------------------------------------------------------------------ #
    #  TAB: ANUAL                                                          #
    # ------------------------------------------------------------------ #
    def _build_anual_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Year summary table
        self.year_table = QTableWidget()
        self.year_table.setColumnCount(4)
        self.year_table.setHorizontalHeaderLabels([tr("YEAR"), tr("INCOMES"), tr("EXPENSES"), tr("AVAILABLE")])
        self.year_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.year_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.year_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.year_table.verticalHeader().setVisible(False)
        self.year_table.verticalHeader().setDefaultSectionSize(48)
        self.year_table.setMaximumHeight(280)
        layout.addWidget(self.year_table)

        # Bar chart comparing years
        self.year_fig = Figure(figsize=(8, 4), facecolor='#1E1E24')
        self.year_fig.patch.set_facecolor('#1E1E24')
        self.year_canvas = FigureCanvas(self.year_fig)
        self.year_canvas.setStyleSheet("background-color: transparent;")
        self.year_ax = self.year_fig.add_subplot(111)
        self.year_ax.set_facecolor('#1E1E24')
        layout.addWidget(self.year_canvas)

        self.tabs.addTab(tab, tr("TAB_ANNUAL"))

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #
    def _make_card(self, title_text, value_label):
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout()
        t = QLabel(title_text)
        t.setProperty("class", "card-title")
        l.addWidget(t)
        l.addWidget(value_label)
        card.setLayout(l)
        return card

    def show_help(self):
        msg = tr("HELP_HISTORIC")
        QMessageBox.information(self, tr("HELP") + ": " + tr("HISTORIC"), msg)

    def _get_year_data(self, full_data):
        """Group full history data (monthly) by calendar year."""
        year_map = {}   # {year: {incomes: [], expenses: []}}
        for label, inc, exp in zip(full_data['labels'], full_data['incomes'], full_data['expenses']):
            # label format: "Jan 25", "Feb 26" etc.
            try:
                dt = datetime.strptime(label, "%b %y")
                year = dt.year
            except ValueError:
                continue
            if year not in year_map:
                year_map[year] = {'incomes': [], 'expenses': []}
            year_map[year]['incomes'].append(inc)
            year_map[year]['expenses'].append(exp)

        result = []
        for year in sorted(year_map.keys()):
            total_inc = sum(year_map[year]['incomes'])
            total_exp = sum(year_map[year]['expenses'])
            result.append({
                'year': year,
                'income': total_inc,
                'expense': total_exp,
                'balance': total_inc - total_exp,
            })
        return result

    # ------------------------------------------------------------------ #
    #  REFRESH                                                             #
    # ------------------------------------------------------------------ #
    def refresh_data(self):
        data = self.controller.get_full_history_data()
        self._refresh_total_tab(data)
        self._refresh_anual_tab(data)

    def _refresh_total_tab(self, data):
        labels   = data['labels']
        incomes  = data['incomes']
        expenses = data['expenses']
        balances = data['balances']

        sum_inc = sum(incomes)  if incomes  else 0
        sum_exp = sum(expenses) if expenses else 0
        sum_bal = sum(balances) if balances else 0

        self.total_income_val.setText(f"{sum_inc:.2f} €")
        self.total_expense_val.setText(f"{sum_exp:.2f} €")
        self.total_balance_val.setText(f"{sum_bal:.2f} €")
        self.total_balance_val.setStyleSheet(
            "color: #2ECC71;" if sum_bal >= 0 else "color: #E74C3C;"
        )

        self.total_ax.clear()
        if labels:
            x = np.arange(len(labels))
            self.total_ax.plot(x, incomes,  color='#2ECC71', marker='o', label=tr('INCOMES'),      linewidth=2)
            self.total_ax.plot(x, expenses, color='#E74C3C', marker='o', label=tr('EXPENSES'),         linewidth=2)
            self.total_ax.plot(x, balances, color='#3498DB', marker='o', label=tr('FREE_MONEY'),   linewidth=2)

            n = max(1, len(labels) // 12)
            self.total_ax.set_xticks(x[::n])
            # Replace labels
            trans_labels = []
            for lab in [labels[i] for i in range(0, len(labels), n)]:
                try:
                    dt = datetime.strptime(lab, "%b %y")
                    mon_abbrev = Translator.get_month_name(dt.month)[:3]
                    trans_labels.append(f"{mon_abbrev} {dt.strftime('%y')}")
                except:
                    trans_labels.append(lab)
                    
            self.total_ax.set_xticklabels(
                trans_labels,
                color='#A0A0A0', rotation=45, ha='right'
            )
            self.total_ax.tick_params(axis='y', colors='#A0A0A0')
            self.total_ax.spines['top'].set_visible(False)
            self.total_ax.spines['right'].set_visible(False)
            self.total_ax.spines['left'].set_color('#2C2C35')
            self.total_ax.spines['bottom'].set_color('#2C2C35')
        else:
            self.total_ax.text(0.5, 0.5, tr('NO_HISTORIC_DATA'),
                               ha='center', va='center', color='white',
                               transform=self.total_ax.transAxes)

        self.total_ax.legend(facecolor='#1E1E24', edgecolor='#2C2C35', labelcolor='white')
        self.total_fig.tight_layout()
        self.total_canvas.draw()

    def _refresh_anual_tab(self, data):
        year_data = self._get_year_data(data)

        # --- Table ---
        self.year_table.setRowCount(0)
        for row_idx, yd in enumerate(year_data):
            self.year_table.insertRow(row_idx)
            self.year_table.setRowHeight(row_idx, 48)

            # Year
            year_item = QTableWidgetItem(str(yd['year']))
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            year_item.setForeground(QColor("#E0E0E0"))
            font = year_item.font()
            font.setBold(True)
            font.setPointSize(12)
            year_item.setFont(font)
            self.year_table.setItem(row_idx, 0, year_item)

            # Income
            inc_item = QTableWidgetItem(f"{yd['income']:,.2f} €")
            inc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            inc_item.setForeground(QColor("#2ECC71"))
            self.year_table.setItem(row_idx, 1, inc_item)

            # Expenses
            exp_item = QTableWidgetItem(f"{yd['expense']:,.2f} €")
            exp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            exp_item.setForeground(QColor("#E74C3C"))
            self.year_table.setItem(row_idx, 2, exp_item)

            # Balance
            bal = yd['balance']
            bal_item = QTableWidgetItem(f"{bal:,.2f} €")
            bal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bal_item.setForeground(QColor("#2ECC71") if bal >= 0 else QColor("#E74C3C"))
            self.year_table.setItem(row_idx, 3, bal_item)

        # --- Bar chart ---
        self.year_ax.clear()

        if year_data:
            years    = [str(yd['year']) for yd in year_data]
            incomes  = [yd['income']  for yd in year_data]
            expenses = [yd['expense'] for yd in year_data]
            balances = [yd['balance'] for yd in year_data]

            x     = np.arange(len(years))
            width = 0.25

            bars_inc = self.year_ax.bar(x - width, incomes,  width, label=tr('INCOMES'),      color='#2ECC71', alpha=0.85)
            bars_exp = self.year_ax.bar(x,          expenses, width, label=tr('EXPENSES'),         color='#E74C3C', alpha=0.85)
            bars_bal = self.year_ax.bar(x + width,  balances, width, label=tr('AVAILABLE'),     color='#3498DB', alpha=0.85)

            # Value labels on bars
            for bars in (bars_inc, bars_exp, bars_bal):
                for bar in bars:
                    h = bar.get_height()
                    if abs(h) > 0:
                        self.year_ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            h + (max(incomes + expenses) * 0.01),
                            f"{h:,.0f}€",
                            ha='center', va='bottom',
                            color='#E0E0E0', fontsize=8
                        )

            self.year_ax.set_xticks(x)
            self.year_ax.set_xticklabels(years, color='#E0E0E0', fontsize=12, fontweight='bold')
            self.year_ax.tick_params(axis='y', colors='#A0A0A0')
            self.year_ax.spines['top'].set_visible(False)
            self.year_ax.spines['right'].set_visible(False)
            self.year_ax.spines['left'].set_color('#2C2C35')
            self.year_ax.spines['bottom'].set_color('#2C2C35')
            self.year_ax.set_title(tr("ANNUAL_SUMMARY"), color='#A0A0A0', fontsize=12, pad=10)
            self.year_ax.legend(facecolor='#1E1E24', edgecolor='#2C2C35', labelcolor='white')
        else:
            self.year_ax.text(0.5, 0.5, tr("NO_ANNUAL_DATA"),
                              ha='center', va='center', color='white',
                              transform=self.year_ax.transAxes)

        self.year_fig.tight_layout()
        self.year_canvas.draw()
