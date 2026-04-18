from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QHeaderView, QMessageBox, QColorDialog)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from utils.translator import tr

class CategoryView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected_color = "#3498DB"  # Default Color
        self.init_ui()
        self.load_categories()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        header_layout = QHBoxLayout()
        title = QLabel(tr("MANAGE_CATEGORIES"))
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        header_layout.addWidget(title)
        
        btn_help = QPushButton("?")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet("border-radius: 12px; border: 1px solid #3498DB; color: #3498DB; font-weight: bold; background-color: transparent; margin-left: 10px;")
        btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_help.clicked.connect(self.show_help)
        header_layout.addWidget(btn_help)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Form to add category
        form_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr("NAME"))
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["income", "expense"])
        self.type_combo.setItemText(0, tr("INCOMES"))
        self.type_combo.setItemText(1, tr("EXPENSES"))
        
        self.color_btn = QPushButton(f' {tr("CHOOSE_COLOR")}')
        self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; color: white; font-weight: bold; border-radius: 6px;")
        self.color_btn.clicked.connect(self.choose_color)
        
        self.add_btn = QPushButton(tr("ADD_CATEGORY"))
        self.add_btn.setProperty("class", "action-btn")
        self.add_btn.clicked.connect(self.add_category)
        
        form_layout.addWidget(QLabel(f'{tr("NAME")}:'))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel(f'{tr("TYPE")}:'))
        form_layout.addWidget(self.type_combo)
        form_layout.addWidget(QLabel(f'{tr("COLOR")}:'))
        form_layout.addWidget(self.color_btn)
        form_layout.addWidget(self.add_btn)
        
        layout.addLayout(form_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", tr("NAME"), tr("TYPE"), tr("COLOR"), tr("ACTIONS")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.hideColumn(0)  # Hide ID
        layout.addWidget(self.table)

    def load_categories(self):
        categories = self.controller.get_categories()
        self.table.setRowCount(0)
        
        for row_idx, cat in enumerate(categories):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(cat.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(cat.name))
            
            tipo_es = tr("INCOMES") if cat.type == "income" else tr("EXPENSES")
            self.table.setItem(row_idx, 2, QTableWidgetItem(tipo_es))
            
            # Color label with background
            color_lbl = QLabel("")
            color_lbl.setStyleSheet(f"background-color: {cat.color}; color: white; padding: 5px; border-radius: 4px; font-weight: bold;")
            self.table.setCellWidget(row_idx, 3, color_lbl)
            
            # Delete button
            del_btn = QPushButton(tr("DELETE").upper())
            del_btn.setStyleSheet("QPushButton { background-color: transparent; color: #E74C3C; border: none; font-weight: bold; } QPushButton:hover { color: #FF7675; background-color: transparent; }")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda checked, c_id=cat.id: self.delete_category(c_id))
            self.table.setCellWidget(row_idx, 4, del_btn)

    def choose_color(self):
        initial_color = QColor(self.selected_color)
        color = QColorDialog.getColor(initial_color, self, tr("CHOOSE_CAT_COLOR"))
        
        if color.isValid():
            self.selected_color = color.name().upper()
            
            # Decide text color based on background lightness
            lightness = color.lightness()
            text_color = "black" if lightness > 150 else "white"
            
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; color: {text_color}; font-weight: bold; border-radius: 6px;")
            self.color_btn.setText("")

    def show_help(self):
        msg = tr("HELP_CATEGORIES")
        QMessageBox.information(self, tr("HELP") + ": " + tr("MANAGE_CATEGORIES"), msg)

    def add_category(self):
        name = self.name_input.text().strip()
        c_type = "income" if self.type_combo.currentIndex() == 0 else "expense"
        color = self.selected_color

        if not name:
            QMessageBox.warning(self, tr("ERROR"), tr("NAME_REQUIRED"))
            return

        self.controller.add_category(name, c_type, color)
        self.name_input.clear()
        self.load_categories()

    def delete_category(self, cat_id):
        reply = QMessageBox.question(self, tr("CONFIRM"), tr("DELETE_CAT_MSG"), 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_category(cat_id)
            self.load_categories()
