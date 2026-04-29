import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QComboBox, QGridLayout, QMessageBox,
                             QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt
from utils.translator import tr, Translator

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class DashboardView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        now = datetime.datetime.now()
        self.current_year = now.year
        self.current_month = now.month
        
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header (Month Selector)
        header_layout = QHBoxLayout()
        title = QLabel(tr("DASHBOARD"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet("border-radius: 12px; border: 1px solid #3498DB; color: #3498DB; font-weight: bold; background-color: transparent; margin-left: 10px;")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header_layout.addWidget(btn_help)
        
        header_layout.addStretch()
        
        self.prev_month_btn = QPushButton("<")
        self.prev_month_btn.clicked.connect(self.go_prev_month)
        self.next_month_btn = QPushButton(">")
        self.next_month_btn.clicked.connect(self.go_next_month)
        
        self.month_label = QLabel(self.get_month_str())
        self.month_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 0 10px;")
        
        header_layout.addWidget(self.prev_month_btn)
        header_layout.addWidget(self.month_label)
        header_layout.addWidget(self.next_month_btn)
        
        layout.addLayout(header_layout)
        
        # Summary Cards
        cards_layout = QHBoxLayout()
        
        self.income_val = QLabel("0.00 €")
        self.income_val.setProperty("class", "card-value positive-value")
        self.expense_val = QLabel("0.00 €")
        self.expense_val.setProperty("class", "card-value negative-value")
        self.balance_val = QLabel("0.00 €")
        self.balance_val.setProperty("class", "card-value")
        
        self.card_inc = self.create_card(tr("TOTAL_INCOME", "Total Ingresos"), self.income_val)
        self.card_inc.setObjectName("card-income")
        self.card_exp = self.create_card(tr("TOTAL_EXPENSE", "Total Gastos"), self.expense_val)
        self.card_exp.setObjectName("card-expense")
        self.card_bal = self.create_card(tr("TOTAL_BALANCE", "Balance Total"), self.balance_val)
        self.card_bal.setObjectName("card-balance")
        
        cards_layout.addWidget(self.card_inc)
        cards_layout.addWidget(self.card_exp)
        cards_layout.addWidget(self.card_bal)
        
        layout.addLayout(cards_layout)
        
        # Horizontal Bar Chart Layout (Expense vs Income %)
        self.bar_fig = Figure(figsize=(8, 1.4), facecolor='#1E1E24')
        self.bar_fig.patch.set_facecolor('#1E1E24')
        self.bar_canvas = FigureCanvas(self.bar_fig)
        self.bar_canvas.setStyleSheet("background-color: transparent;")
        self.bar_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.bar_canvas.setMinimumHeight(120)
        self.bar_canvas.setMaximumHeight(160)
        self.bar_ax = self.bar_fig.add_subplot(111)
        self.bar_ax.set_facecolor('#1E1E24')
        layout.addWidget(self.bar_canvas)
        
        # Charts Layout
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)

        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        
        # Pie Chart (Categories)
        self.pie_fig = Figure(figsize=(6,5), facecolor='#1E1E24')
        self.pie_fig.patch.set_facecolor('#1E1E24')
        self.pie_canvas = FigureCanvas(self.pie_fig)
        self.pie_canvas.setStyleSheet("background-color: transparent;")
        self.pie_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pie_canvas.setMinimumHeight(250)
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_ax.set_facecolor('#1E1E24')
        left_column.addWidget(self.pie_canvas)

        self.quick_expenses_card = QFrame()
        self.quick_expenses_card.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35;")
        quick_layout = QVBoxLayout()
        quick_layout.setContentsMargins(14, 14, 14, 14)
        quick_layout.setSpacing(10)
        self.quick_expenses_card.setLayout(quick_layout)

        quick_title = QLabel(tr("EXPENSES_QUICK_VIEW"))
        quick_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #E0E0E0;")
        quick_layout.addWidget(quick_title)

        self.quick_expenses_scroll = QScrollArea()
        self.quick_expenses_scroll.setWidgetResizable(True)
        self.quick_expenses_scroll.setMinimumHeight(260)
        self.quick_expenses_scroll.setMaximumHeight(320)
        self.quick_expenses_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.quick_expenses_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.quick_expenses_container = QWidget()
        self.quick_expenses_layout = QVBoxLayout()
        self.quick_expenses_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_expenses_layout.setSpacing(6)
        self.quick_expenses_container.setLayout(self.quick_expenses_layout)
        self.quick_expenses_scroll.setWidget(self.quick_expenses_container)

        quick_layout.addWidget(self.quick_expenses_scroll)

        self.quick_expenses_container.setFixedWidth(280)

        left_column.addWidget(self.quick_expenses_card)

        left_widget = QWidget()
        left_widget.setLayout(left_column)
        charts_layout.addWidget(left_widget, 1)
        
        # Line Chart (Trend)
        trend_container = QWidget()
        trend_layout = QVBoxLayout(trend_container)
        trend_layout.setContentsMargins(0, 0, 0, 0)
        trend_layout.setSpacing(5)
        
        trend_header = QHBoxLayout()
        self.trend_type_combo = QComboBox()
        self.trend_type_combo.addItems(["Líneas", "Barras"])
        self.trend_type_combo.setStyleSheet("background-color: #2C2C35; color: white; border-radius: 4px; padding: 2px 8px;")
        self.trend_type_combo.currentTextChanged.connect(self.update_line_chart)
        trend_header.addStretch()
        trend_header.addWidget(self.trend_type_combo)
        trend_layout.addLayout(trend_header)

        self.line_fig = Figure(figsize=(6,4), facecolor='#1E1E24')
        self.line_fig.patch.set_facecolor('#1E1E24')
        self.line_canvas = FigureCanvas(self.line_fig)
        self.line_canvas.setStyleSheet("background-color: transparent;")
        self.line_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.line_canvas.setMinimumHeight(250)
        self.line_ax = self.line_fig.add_subplot(111)
        self.line_ax.set_facecolor('#1E1E24')
        
        trend_layout.addWidget(self.line_canvas)
        charts_layout.addWidget(trend_container, 1)
        
        layout.addLayout(charts_layout)

    def create_card(self, title_text, value_label):
        card = QFrame()
        card.setProperty("class", "card")
        l = QVBoxLayout()
        l.setSpacing(2)
        l.setContentsMargins(10, 10, 10, 10)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel(title_text)
        title.setProperty("class", "card-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l.addWidget(title)
        l.addWidget(value_label)
        card.setLayout(l)
        return card

    def show_help(self):
        msg = tr("HELP_DASHBOARD")
        QMessageBox.information(self, tr("HELP", "Ayuda") + ": " + tr("DASHBOARD"), msg)

    def get_month_str(self):
        return f"{Translator.get_month_name(self.current_month)} {self.current_year}"

    def go_prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.month_label.setText(self.get_month_str())
        self.refresh_data()

    def go_next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.month_label.setText(self.get_month_str())
        self.refresh_data()

    def refresh_data(self):
        summary = self.controller.get_dashboard_summary(self.current_year, self.current_month)
        
        self.income_val.setText(f"{summary['total_income']:.2f} €")
        self.expense_val.setText(f"{summary['total_expense']:.2f} €")
        
        bal_text = f"{summary['balance']:.2f} €"
        self.balance_val.setText(bal_text)
        if summary['balance'] >= 0:
            self.balance_val.setStyleSheet("color: #2ECC71;") # Green
        else:
            self.balance_val.setStyleSheet("color: #E74C3C;") # Red

        self.update_pie_chart(summary)
        self.update_expense_quick_view(summary)
        self.update_line_chart()
        self.update_bar_chart(summary)

    def _clear_quick_expenses(self):
        while self.quick_expenses_layout.count():
            item = self.quick_expenses_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_expense_quick_view(self, summary):
        self._clear_quick_expenses()

        expenses_breakdown = summary['expenses_breakdown']
        total_expense = summary['total_expense']

        if not expenses_breakdown:
            empty_lbl = QLabel(tr("NO_EXPENSES_MONTH"))
            empty_lbl.setWordWrap(True)
            empty_lbl.setStyleSheet("color: #A0A0A0; padding: 8px 4px;")
            self.quick_expenses_layout.addWidget(empty_lbl)
            self.quick_expenses_layout.addStretch()
            return

        # Group by category keeping items
        cat_data = {}
        for item in expenses_breakdown:
            cat_name = item.get('category_name') or tr("UNKNOWN")
            if cat_name not in cat_data:
                cat_data[cat_name] = {'total': 0.0, 'items': []}
            cat_data[cat_name]['total'] += item['amount']
            cat_data[cat_name]['items'].append(item)

        # Sort by amount descending
        sorted_cats = sorted(cat_data.items(), key=lambda x: x[1]['total'], reverse=True)

        for cat_name, data in sorted_cats:
            cat_amount = data['total']
            items = data['items']
            pct = (cat_amount / total_expense) * 100 if total_expense > 0 else 0

            # Main container for the category
            cat_widget = QWidget()
            cat_layout = QVBoxLayout()
            cat_layout.setContentsMargins(0, 0, 0, 0)
            cat_layout.setSpacing(0)
            cat_widget.setLayout(cat_layout)

            # Category Header Row (always visible)
            row = QFrame()
            row.setStyleSheet(
                "QFrame { background-color: #25252E; border: 1px solid #2C2C35; "
                "border-radius: 8px; }"
            )
            row_layout = QVBoxLayout()
            row_layout.setContentsMargins(10, 8, 10, 8)
            row_layout.setSpacing(4)
            row.setLayout(row_layout)

            # Top line: category name (clickable) + amount
            top_row = QHBoxLayout()
            top_row.setSpacing(4)

            name_btn = QPushButton(f"▶ {cat_name}")
            name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            name_btn.setStyleSheet(
                "QPushButton { color: #E0E0E0; font-weight: bold; font-size: 12px; "
                "text-align: left; border: none; background: transparent; padding: 0; }"
                "QPushButton:hover { color: #3498DB; }"
            )

            amount_lbl = QLabel(f"{cat_amount:.2f} \u20ac")
            amount_lbl.setStyleSheet(
                "color: #CF6679; font-weight: bold; font-size: 12px; "
                "border: none; background: transparent;"
            )
            amount_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            top_row.addWidget(name_btn, 1)
            top_row.addWidget(amount_lbl)
            row_layout.addLayout(top_row)

            # Bottom line: progress bar + percentage
            bottom_row = QHBoxLayout()
            bottom_row.setSpacing(6)

            from PyQt6.QtWidgets import QProgressBar
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(pct))
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(
                "QProgressBar { background-color: #1A1A22; border-radius: 3px; border: none; }"
                "QProgressBar::chunk { background-color: #8A8A9A; border-radius: 3px; }"
            )

            pct_lbl = QLabel(f"{pct:.1f}%")
            pct_lbl.setStyleSheet(
                "color: #707080; font-size: 10px; border: none; background: transparent;"
            )
            pct_lbl.setFixedWidth(40)
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            bottom_row.addWidget(bar, 1)
            bottom_row.addWidget(pct_lbl)
            row_layout.addLayout(bottom_row)

            cat_layout.addWidget(row)

            # Details container (hidden by default)
            details_container = QFrame()
            details_container.setStyleSheet(
                "QFrame { background-color: #1A1A22; border-left: 2px solid #2C2C35; "
                "border-right: 1px solid #2C2C35; border-bottom: 1px solid #2C2C35; "
                "border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; "
                "margin-top: -4px; margin-left: 4px; margin-right: 4px; }"
            )
            details_layout = QVBoxLayout()
            details_layout.setContentsMargins(10, 8, 10, 8)
            details_layout.setSpacing(4)
            details_container.setLayout(details_layout)
            details_container.setVisible(False)

            for item in items:
                item_row = QHBoxLayout()
                
                item_name = QLabel(f"• {item['name']}")
                item_name.setStyleSheet("color: #A0A0A0; font-size: 11px; border: none; background: transparent;")
                item_name.setWordWrap(True)
                
                item_amount = QLabel(f"{item['amount']:.2f} \u20ac")
                item_amount.setStyleSheet("color: #CF6679; font-size: 11px; border: none; background: transparent;")
                item_amount.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
                
                item_row.addWidget(item_name, 1)
                item_row.addWidget(item_amount)
                details_layout.addLayout(item_row)

            cat_layout.addWidget(details_container)
            
            # Toggle function
            def toggle_details(checked=False, btn=name_btn, container=details_container, name=cat_name):
                is_visible = container.isVisible()
                container.setVisible(not is_visible)
                btn.setText(f"▼ {name}" if not is_visible else f"▶ {name}")

            name_btn.clicked.connect(toggle_details)

            self.quick_expenses_layout.addWidget(cat_widget)

        self.quick_expenses_layout.addStretch()

    def update_pie_chart(self, summary):
        self.pie_ax.clear()
        
        expenses_breakdown = summary['expenses_breakdown']
        
        if not expenses_breakdown:
            self.pie_ax.text(0.5, 0.5, tr("NO_DATA", "Sin datos"), horizontalalignment='center', verticalalignment='center', color='white')
            self.pie_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        else:
            # Group by category
            cat_totals = {}
            cat_colors = {}
            cat_items = {}
            for item in expenses_breakdown:
                cat_name = item.get('category_name') or tr("UNKNOWN")
                if cat_name not in cat_totals:
                    cat_totals[cat_name] = 0.0
                    cat_colors[cat_name] = item.get('color', '#3498DB')
                    cat_items[cat_name] = []
                cat_totals[cat_name] += item['amount']
                cat_items[cat_name].append(item)
                
            labels = list(cat_totals.keys())
            sizes = list(cat_totals.values())
            colors = [cat_colors[lbl] for lbl in labels]
            
            total = sum(sizes) if sum(sizes) > 0 else 1
            labels_with_pct = [f"{lbl}\n({(sz/total)*100:.1f}%)" for lbl, sz in zip(labels, sizes)]
            
            # Create pie chart with larger radius
            wedges, texts = self.pie_ax.pie(
                sizes, labels=labels_with_pct, colors=colors,
                startangle=90, radius=1.0, textprops=dict(color="w", fontsize=9, weight='bold')
            )
            self.pie_ax.axis('equal') 
            
            # Setup tooltip annotation
            annot = self.pie_ax.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                                         bbox=dict(boxstyle="round4,pad=0.5", fc="#25252E", ec="#3498DB", lw=1.5, alpha=0.95),
                                         color="white", fontsize=9, zorder=100)
            annot.set_visible(False)
            
            def hover(event):
                vis = annot.get_visible()
                if event.inaxes == self.pie_ax:
                    for i, wedge in enumerate(wedges):
                        cont, ind = wedge.contains(event)
                        if cont:
                            cat_name = labels[i]
                            items = cat_items[cat_name]
                            items.sort(key=lambda x: x['amount'], reverse=True)
                            
                            text = f"--- {cat_name} ---\n"
                            for it in items:
                                text += f"• {it['name']}: {it['amount']:.2f} \u20ac\n"
                            
                            annot.xy = (event.xdata, event.ydata)
                            annot.set_text(text.strip())
                            annot.set_visible(True)
                            self.pie_canvas.draw_idle()
                            return
                if vis:
                    annot.set_visible(False)
                    self.pie_canvas.draw_idle()

            if hasattr(self, '_pie_hover_cid'):
                self.pie_canvas.mpl_disconnect(self._pie_hover_cid)
            self._pie_hover_cid = self.pie_canvas.mpl_connect("motion_notify_event", hover)
            
        self.pie_fig.tight_layout()
        self.pie_canvas.draw()

    def update_line_chart(self, *_):
        self.line_ax.clear()
        
        trend_data = self.controller.get_trend_data(self.current_year, self.current_month, 6)
        
        labels = trend_data['labels']
        incomes = trend_data['incomes']
        expenses = trend_data['expenses']
        balances = [i - e for i, e in zip(incomes, expenses)]
        
        x = np.arange(len(labels))
        
        chart_type = getattr(self, 'trend_type_combo', None)
        chart_val = chart_type.currentText() if chart_type else "Líneas"

        if chart_val == "Líneas":
            self.line_ax.plot(x, incomes, color='#2ECC71', marker='o', label=tr("INCOMES", "Ingresos"), linewidth=2)
            self.line_ax.plot(x, expenses, color='#E74C3C', marker='o', label=tr("EXPENSES", "Gastos"), linewidth=2)
            self.line_ax.plot(x, balances, color='#3498DB', marker='o', label=tr("FREE_MONEY", "Dinero Libre"), linewidth=2)
        elif chart_val == "Barras":
            width = 0.25
            self.line_ax.bar(x - width, incomes, width, label=tr("INCOMES", "Ingresos"), color='#2ECC71')
            self.line_ax.bar(x, expenses, width, label=tr("EXPENSES", "Gastos"), color='#E74C3C')
            self.line_ax.bar(x + width, balances, width, label=tr("FREE_MONEY", "Dinero Libre"), color='#3498DB')
        
        self.line_ax.set_xticks(x)
        
        # Replace labels format "Nov 25" -> Translated abbreviated "Nov 25"
        trans_labels = []
        for lab in labels:
            try:
                dt = datetime.datetime.strptime(lab, "%b %y")
                mon_abbrev = Translator.get_month_name(dt.month)[:3]
                trans_labels.append(f"{mon_abbrev} {dt.strftime('%y')}")
            except:
                trans_labels.append(lab)
                
        self.line_ax.set_xticklabels(trans_labels, color='#A0A0A0')
        self.line_ax.tick_params(axis='y', colors='#A0A0A0')
        
        # Remove borders
        self.line_ax.spines['top'].set_visible(False)
        self.line_ax.spines['right'].set_visible(False)
        self.line_ax.spines['left'].set_color('#2C2C35')
        self.line_ax.spines['bottom'].set_color('#2C2C35')
        self.line_ax.set_facecolor('#1E1E24')
        
        self.line_ax.legend(facecolor='#1E1E24', edgecolor='#2C2C35', labelcolor='white')
        self.line_canvas.draw()

    def update_bar_chart(self, summary):
        self.bar_ax.clear()
        
        total_income = summary['total_income']
        total_expense = summary['total_expense']
        free_money = summary['balance'] if summary['balance'] > 0 else 0
        
        if total_income == 0 and total_expense == 0:
             self.bar_ax.text(0.5, 0.5, tr("NO_ACT_MONTH", "Sin actividad este mes"), ha='center', va='center', color='white')
             self.bar_ax.axis('off')
             self.bar_canvas.draw()
             return

        max_val = max(total_income, total_expense) if max(total_income, total_expense) > 0 else 1
        
        expense_pct = (total_expense / max_val) * 100
        free_pct = (free_money / max_val) * 100
        
        # Plot stacked bar
        # Gastos first (Red)
        self.bar_ax.barh([0], [total_expense], color='#E74C3C', height=0.7, label=f'{tr("EXPENSES")} ({expense_pct:.1f}%)')
        # Dinero libre second (Blue)
        if free_money > 0:
            self.bar_ax.barh([0], [free_money], left=[total_expense], color='#3498DB', height=0.7, label=f'{tr("FREE_MONEY")} ({free_pct:.1f}%)')
            
        self.bar_ax.axis('off')
        self.bar_ax.set_ylim(-1.2, 1.2)
        
        # Title/Text instead of legend might look better, but let's use a nice title
        self.bar_ax.set_title(tr("PROPORTION_TITLE", "Proporción Gastos vs Dinero Libre del Mes"), color='#A0A0A0', fontsize=12, pad=15)
        self.bar_ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2, facecolor='#1E1E24', edgecolor='#2C2C35', labelcolor='white', frameon=False, fontsize=11)
        self.bar_fig.tight_layout()
        self.bar_canvas.draw()
