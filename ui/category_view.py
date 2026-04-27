from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QHeaderView, QMessageBox, QColorDialog,
                             QDialog, QFormLayout)
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
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 180)
        self.table.hideColumn(0)  # Hide ID
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        layout.addWidget(self.table)

    def load_categories(self):
        categories = self.controller.get_categories()
        self.table.setRowCount(0)
        
        for row_idx, cat in enumerate(categories):
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, 44)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(cat.id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(cat.name))
            
            tipo_es = tr("INCOMES") if cat.type == "income" else tr("EXPENSES")
            self.table.setItem(row_idx, 2, QTableWidgetItem(tipo_es))
            
            # Color label with background
            color_lbl = QLabel("")
            color_lbl.setStyleSheet(f"background-color: {cat.color}; color: white; padding: 5px; border-radius: 4px; font-weight: bold;")
            self.table.setCellWidget(row_idx, 3, color_lbl)
            
            # Action buttons: EDITAR + ELIMINAR
            edit_btn = QPushButton(tr("EDIT"))
            edit_btn.setProperty("role", "table-pay")
            edit_btn.setFixedHeight(30)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, c_id=cat.id: self.show_edit_dialog(c_id))

            del_btn = QPushButton(tr("DELETE"))
            del_btn.setProperty("role", "table-delete")
            del_btn.setFixedHeight(30)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda checked, c_id=cat.id: self.delete_category(c_id))

            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row_idx, 4, btn_container)

    def show_edit_dialog(self, cat_id):
        cat = self.controller.get_category_by_id(cat_id)
        if cat is None:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(tr("EDIT_CATEGORY"))
        dialog.setFixedWidth(400)

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        d_name = QLineEdit(cat.name)

        d_type = QComboBox()
        d_type.addItems([tr("INCOMES"), tr("EXPENSES")])
        d_type.setCurrentIndex(0 if cat.type == "income" else 1)

        edit_color = cat.color
        d_color_btn = QPushButton(f"  {cat.color}")
        d_color_btn.setStyleSheet(
            f"background-color: {cat.color}; color: white; font-weight: bold; "
            f"border-radius: 6px; padding: 8px;"
        )

        def pick_color():
            nonlocal edit_color
            color = QColorDialog.getColor(QColor(edit_color), dialog, tr("CHOOSE_CAT_COLOR"))
            if color.isValid():
                edit_color = color.name().upper()
                lightness = color.lightness()
                text_color = "black" if lightness > 150 else "white"
                d_color_btn.setStyleSheet(
                    f"background-color: {edit_color}; color: {text_color}; "
                    f"font-weight: bold; border-radius: 6px; padding: 8px;"
                )
                d_color_btn.setText(f"  {edit_color}")

        d_color_btn.clicked.connect(pick_color)

        form.addRow(f'{tr("NAME")}:', d_name)
        form.addRow(f'{tr("TYPE")}:', d_type)
        form.addRow(f'{tr("COLOR")}:', d_color_btn)

        save_btn = QPushButton(tr("SAVE_CHANGES"))
        save_btn.setProperty("class", "action-btn")

        outer.addLayout(form)
        outer.addWidget(save_btn)

        def save():
            name = d_name.text().strip()
            if not name:
                QMessageBox.warning(dialog, tr("ERROR"), tr("NAME_REQUIRED"))
                return
            c_type = "income" if d_type.currentIndex() == 0 else "expense"
            self.controller.update_category(cat_id, name, c_type, edit_color)
            self.load_categories()
            dialog.accept()

        save_btn.clicked.connect(save)
        dialog.exec()

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
