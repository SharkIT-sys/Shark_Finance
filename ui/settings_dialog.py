import hashlib
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                             QMessageBox, QFrame, QFileDialog, QInputDialog, QScrollArea, QWidget, QComboBox)
from PyQt6.QtCore import Qt
from utils.translator import tr
import shutil
import sys
import os
from PyQt6.QtGui import QIcon

def create_shortcuts():
    try:
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        startup = winshell.programs()
        path = os.path.join(desktop, "Shark Contabilidad.lnk")
        target = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath("main.py")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.save()

        start_path = os.path.join(startup, "Shark Contabilidad.lnk")
        shortcut_start = shell.CreateShortCut(start_path)
        shortcut_start.Targetpath = target
        shortcut_start.WorkingDirectory = os.path.dirname(target)
        shortcut_start.save()
        return True
    except Exception as e:
        print("Shortcut error:", e)
        return False

class SettingsDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        
        self.setWindowTitle(tr("SETTINGS_ADVANCED"))
        self.resize(400, 550)
        self.setStyleSheet("background-color: #121212; color: #E0E0E0;")
        
        self.init_ui()

    def _security_question_text(self):
        current_question = self.controller.db.get_config('security_question')
        if current_question:
            return tr("CURRENT_SECURITY_Q").format(current_question)
        return tr("SEC_Q_MISSING")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        container = QWidget()
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(20)
        container.setLayout(c_layout)
        
        # --- Card 1: Password ---
        card_pwd = QFrame()
        card_pwd.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 15px;")
        l_pwd = QVBoxLayout()
        card_pwd.setLayout(l_pwd)
        
        t_pwd = QLabel(tr("CHANGE_MASTER_PWD"))
        t_pwd.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498DB;")
        l_pwd.addWidget(t_pwd)
        
        self.old_pwd_input = QLineEdit()
        self.old_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_pwd_input.setPlaceholderText(tr("CURRENT_PWD"))
        self.old_pwd_input.setStyleSheet("background-color: #2A2A35; border: 1px solid #3A3A45; border-radius: 6px; padding: 8px; color: #FFFFFF;")
        l_pwd.addWidget(self.old_pwd_input)
        
        self.new_pwd_input = QLineEdit()
        self.new_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd_input.setPlaceholderText(tr("NEW_PWD"))
        self.new_pwd_input.setStyleSheet("background-color: #2A2A35; border: 1px solid #3A3A45; border-radius: 6px; padding: 8px; color: #FFFFFF;")
        l_pwd.addWidget(self.new_pwd_input)
        
        self.conf_pwd_input = QLineEdit()
        self.conf_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.conf_pwd_input.setPlaceholderText(tr("CONFIRM_PWD"))
        self.conf_pwd_input.setStyleSheet("background-color: #2A2A35; border: 1px solid #3A3A45; border-radius: 6px; padding: 8px; color: #FFFFFF;")
        l_pwd.addWidget(self.conf_pwd_input)
        
        self.submit_btn = QPushButton(tr("UPDATE_PWD"))
        self.submit_btn.setStyleSheet("background-color: #3498DB; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold;")
        self.submit_btn.clicked.connect(self.submit)
        l_pwd.addWidget(self.submit_btn)
        c_layout.addWidget(card_pwd)

        # --- Card 2: Security Question ---
        card_sec = QFrame()
        card_sec.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 15px;")
        l_sec = QVBoxLayout()
        card_sec.setLayout(l_sec)

        t_sec = QLabel(tr("SECURITY_RECOVERY"))
        t_sec.setStyleSheet("font-size: 16px; font-weight: bold; color: #16A085;")
        l_sec.addWidget(t_sec)

        self.sec_status_lbl = QLabel(self._security_question_text())
        self.sec_status_lbl.setWordWrap(True)
        self.sec_status_lbl.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        l_sec.addWidget(self.sec_status_lbl)

        self.sec_pwd_input = QLineEdit()
        self.sec_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.sec_pwd_input.setPlaceholderText(tr("SECURITY_CURRENT_PWD"))
        self.sec_pwd_input.setStyleSheet("background-color: #2A2A35; border: 1px solid #3A3A45; border-radius: 6px; padding: 8px; color: #FFFFFF;")
        l_sec.addWidget(self.sec_pwd_input)

        self.sec_q_input = QLineEdit()
        self.sec_q_input.setPlaceholderText(tr("SECURITY_Q_LABEL"))
        self.sec_q_input.setText(self.controller.db.get_config('security_question') or "")
        self.sec_q_input.setStyleSheet("background-color: #2A2A35; border: 1px solid #3A3A45; border-radius: 6px; padding: 8px; color: #FFFFFF;")
        l_sec.addWidget(self.sec_q_input)

        self.sec_a_input = QLineEdit()
        self.sec_a_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.sec_a_input.setPlaceholderText(tr("SECURITY_A_LABEL"))
        self.sec_a_input.setStyleSheet("background-color: #2A2A35; border: 1px solid #3A3A45; border-radius: 6px; padding: 8px; color: #FFFFFF;")
        l_sec.addWidget(self.sec_a_input)

        self.sec_btn = QPushButton(tr("UPDATE_SECURITY_Q"))
        self.sec_btn.setStyleSheet("background-color: #16A085; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold;")
        self.sec_btn.clicked.connect(self.submit_security_question)
        l_sec.addWidget(self.sec_btn)
        c_layout.addWidget(card_sec)
        
        # --- Card 3: Export Data ---
        card_exp = QFrame()
        card_exp.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 15px;")
        l_exp = QVBoxLayout()
        card_exp.setLayout(l_exp)
        
        t_exp = QLabel(tr("DATA_PORTABILITY"))
        t_exp.setStyleSheet("font-size: 16px; font-weight: bold; color: #2ECC71;")
        l_exp.addWidget(t_exp)
        
        btn_exp = QPushButton(tr("EXPORT_DB"))
        btn_exp.setStyleSheet("background-color: transparent; border: 1px solid #2ECC71; color: #2ECC71; border-radius: 6px; padding: 8px; font-weight: bold;")
        btn_exp.clicked.connect(self.export_db)
        l_exp.addWidget(btn_exp)
        c_layout.addWidget(card_exp)

        # --- Card Language ---
        card_lang = QFrame()
        card_lang.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 15px;")
        l_lang = QVBoxLayout()
        card_lang.setLayout(l_lang)
        
        t_lang = QLabel(tr("LANGUAGE"))
        t_lang.setStyleSheet("font-size: 16px; font-weight: bold; color: #F1C40F;")
        l_lang.addWidget(t_lang)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItem(tr("LANGUAGE_OPT_ES"), "es")
        self.lang_combo.addItem(tr("LANGUAGE_OPT_EN"), "en")
        
        current_lang = self.controller.db.get_config('language') or 'es'
        if current_lang == 'en':
            self.lang_combo.setCurrentIndex(1)
        else:
            self.lang_combo.setCurrentIndex(0)
            
        self.lang_combo.setStyleSheet("background-color: #2A2A35; padding: 8px; border: 1px solid #3A3A45; border-radius: 6px; color: white;")
        l_lang.addWidget(self.lang_combo)
        
        btn_lang = QPushButton(tr("UPDATE_LANGUAGE"))
        btn_lang.setStyleSheet("background-color: #F39C12; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold;")
        btn_lang.clicked.connect(self.change_language)
        l_lang.addWidget(btn_lang)
        c_layout.addWidget(card_lang)

        # --- Card Shortcuts ---
        card_shortcut = QFrame()
        card_shortcut.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 15px;")
        l_shortcut = QVBoxLayout()
        card_shortcut.setLayout(l_shortcut)

        t_shortcut = QLabel(tr("CREATE_SHORTCUTS", "Crear Acceso Directo"))
        t_shortcut.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498DB;")
        l_shortcut.addWidget(t_shortcut)

        desc_shortcut = QLabel(tr("SHORTCUT_DESC", "Añade un acceso directo en el Escritorio y Menú Inicio"))
        desc_shortcut.setWordWrap(True)
        desc_shortcut.setStyleSheet("color: #A0A0A0; font-size: 12px; margin-bottom: 10px;")
        l_shortcut.addWidget(desc_shortcut)

        btn_shortcut = QPushButton(tr("CREATE_SHORTCUT_BTN", "Crear Acceso Directo"))
        btn_shortcut.setStyleSheet("background-color: #3498DB; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold;")
        btn_shortcut.clicked.connect(self.create_desktop_shortcut)
        l_shortcut.addWidget(btn_shortcut)
        c_layout.addWidget(card_shortcut)

        # --- Card Legal ---
        card_legal = QFrame()
        card_legal.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 15px;")
        l_legal = QVBoxLayout()
        card_legal.setLayout(l_legal)
        
        t_legal = QLabel("Información Legal")
        t_legal.setStyleSheet("font-size: 16px; font-weight: bold; color: #9B59B6;")
        l_legal.addWidget(t_legal)

        btn_about = QPushButton("ℹ️ Sobre la aplicación")
        btn_about.setStyleSheet("background-color: transparent; border: 1px solid #9B59B6; color: #9B59B6; border-radius: 6px; padding: 8px; font-weight: bold; text-align: left;")
        btn_about.clicked.connect(lambda: self.show_legal_file("README.md", "Sobre la aplicación"))
        l_legal.addWidget(btn_about)

        btn_license = QPushButton("⚖️ Licencia")
        btn_license.setStyleSheet("background-color: transparent; border: 1px solid #9B59B6; color: #9B59B6; border-radius: 6px; padding: 8px; font-weight: bold; text-align: left;")
        btn_license.clicked.connect(lambda: self.show_legal_file("LICENSE", "Licencia"))
        l_legal.addWidget(btn_license)

        btn_privacy = QPushButton("🔒 Privacidad")
        btn_privacy.setStyleSheet("background-color: transparent; border: 1px solid #9B59B6; color: #9B59B6; border-radius: 6px; padding: 8px; font-weight: bold; text-align: left;")
        btn_privacy.clicked.connect(lambda: self.show_legal_file("PRIVACY.txt", "Privacidad"))
        l_legal.addWidget(btn_privacy)

        c_layout.addWidget(card_legal)
        
        # --- Card 3: Danger Zone ---
        card_danger = QFrame()
        card_danger.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #E74C3C; padding: 15px;")
        l_danger = QVBoxLayout()
        card_danger.setLayout(l_danger)
        
        t_danger = QLabel(tr("DANGER_ZONE"))
        t_danger.setStyleSheet("font-size: 16px; font-weight: bold; color: #E74C3C;")
        l_danger.addWidget(t_danger)
        
        btn_nuke = QPushButton(tr("NUKE_DATA"))
        btn_nuke.setStyleSheet("background-color: #E74C3C; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold;")
        btn_nuke.clicked.connect(self.nuke_db)
        l_danger.addWidget(btn_nuke)
        c_layout.addWidget(card_danger)

        c_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def change_language(self):
        new_lang = self.lang_combo.currentData()
        self.controller.db.set_config('language', new_lang)
        QMessageBox.information(self, tr("SUCCESS"), tr("UPDATE_LANG_RESTART"))

    def export_db(self):
        path, _ = QFileDialog.getSaveFileName(self, tr("EXPORT_DB_LOCAL"), "budget_app.db", "Bases de Datos (*.db)")
        if path:
            try:
                db_path = self.controller.db.db_path
                shutil.copy2(db_path, path)
                QMessageBox.information(self, tr("SUCCESS"), tr("EXPORT_DB_LOCAL") + " OK") # O un mensaje mas largo si prefieres
            except Exception as e:
                QMessageBox.critical(self, tr("ERROR"), f"{tr('ERROR')} {e}")

    def submit_security_question(self):
        current_pwd = self.sec_pwd_input.text()
        question = self.sec_q_input.text().strip()
        answer = self.sec_a_input.text().strip()

        if not current_pwd:
            QMessageBox.warning(self, tr("ERROR"), tr("ENTER_CURRENT_PWD"))
            return

        if not question or not answer:
            QMessageBox.warning(self, tr("ERROR"), tr("SEC_Q_REQUIRED"))
            return

        self.sec_btn.setEnabled(False)
        self.sec_btn.setText(tr("PROCESSING"))
        self.repaint()

        success, message = self.controller.db.update_security_question(current_pwd, question, answer)
        if success:
            self.sec_status_lbl.setText(self._security_question_text())
            self.sec_pwd_input.clear()
            self.sec_a_input.clear()
            QMessageBox.information(self, tr("SUCCESS"), message)
        else:
            QMessageBox.warning(self, tr("ERROR"), message)

        self.sec_btn.setEnabled(True)
        self.sec_btn.setText(tr("UPDATE_SECURITY_Q"))

    def show_legal_file(self, filename, title):
        import os
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_path, filename)
        
        content = "No se pudo encontrar el archivo de documentación."
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f"Error al leer el archivo: {e}"
                
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(600, 500)
        dialog.setStyleSheet("background-color: #121212; color: #E0E0E0;")
        
        layout = QVBoxLayout(dialog)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #2C2C35; background-color: transparent; }")
        
        container = QWidget()
        c_layout = QVBoxLayout(container)
        
        lbl = QLabel(content)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setStyleSheet("font-family: 'Consolas', 'Monospace'; font-size: 13px; color: #BBBBBB;")
        c_layout.addWidget(lbl)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet("background-color: #3498DB; color: white; border-radius: 5px; padding: 10px; font-weight: bold;")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()

    def nuke_db(self):
        pwd1, ok1 = QInputDialog.getText(self, tr("AUTH_REQUIRED"), tr("AUTH_MSG"), QLineEdit.EchoMode.Password)
        if ok1 and pwd1:
            raw_hash1 = hashlib.sha256(pwd1.encode()).hexdigest()
            if raw_hash1 == self.controller.db.get_config('app_password'):
                pwd2, ok2 = QInputDialog.getText(self, tr("AUTH_REQUIRED"), tr("AUTH_MSG") + " (Por seguridad, introdúcela de nuevo)", QLineEdit.EchoMode.Password)
                if ok2 and pwd2 == pwd1:
                    self.controller.db.wipe_all_data()
                    QMessageBox.information(self, tr("DB_NUKED"), tr("DB_NUKED_MSG"))
                    sys.exit(0)
                else:
                    QMessageBox.warning(self, tr("ERROR"), "Confimación cancelada o contraseña incorrecta.")
            else:
                QMessageBox.warning(self, tr("ERROR"), tr("WRONG_PWD"))

    def submit(self):
        old_pwd = self.old_pwd_input.text()
        new_pwd = self.new_pwd_input.text()
        conf_pwd = self.conf_pwd_input.text()
        
        if not old_pwd:
            QMessageBox.warning(self, tr("ERROR"), tr("ENTER_CURRENT_PWD"))
            return
            
        if len(new_pwd) < 4:
            QMessageBox.warning(self, tr("ERROR"), tr("PWD_LENGTH_MIN"))
            return
            
        if new_pwd != conf_pwd:
            QMessageBox.warning(self, tr("ERROR"), tr("PWD_NO_MATCH"))
            return

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText(tr("PROCESSING"))
        self.repaint() # Force UI update before blocking operation
        
        success, message = self.controller.db.change_password(old_pwd, new_pwd)
        
        if success:
            QMessageBox.information(self, tr("SUCCESS"), message)
            self.accept()
        else:
            QMessageBox.warning(self, tr("ERROR"), message)
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText(tr("UPDATE_PWD"))
            self.old_pwd_input.clear()
            self.old_pwd_input.setFocus()

    def create_desktop_shortcut(self):
        if sys.platform != 'win32':
            QMessageBox.warning(self, tr("ERROR"), "Esta función solo está disponible en Windows.")
            return

        success = create_shortcuts()
        if success:
            QMessageBox.information(self, tr("SUCCESS"), tr("SHORTCUT_CREATED", "Acceso directo creado correctamente en el Escritorio y Menú Inicio."))
        else:
            QMessageBox.warning(self, tr("ERROR"), tr("SHORTCUT_ERROR", "Error al crear el acceso directo."))
