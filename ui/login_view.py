import hashlib
import os
import sys
import shutil
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QMessageBox, QFrame, QHBoxLayout, QCheckBox, QFileDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from utils.translator import tr

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        
        # Start menu
        start_path = os.path.join(startup, "Shark Contabilidad.lnk")
        shortcut_start = shell.CreateShortCut(start_path)
        shortcut_start.Targetpath = target
        shortcut_start.WorkingDirectory = os.path.dirname(target)
        shortcut_start.save()
        return True
    except Exception as e:
        print("Shortcut error:", e)
        return False

class LoginWindow(QWidget):
    def __init__(self, controller, on_success_callback):
        super().__init__()
        self.controller = controller
        self.on_success = on_success_callback
        
        self.setWindowTitle(tr("LOGIN_TITLE"))
        self.setMinimumSize(450, 600)
        self.setStyleSheet("background-color: #121212; color: #E0E0E0;")
        
        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "logo.png")
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "ui", "resources", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Check if password is set
        self.stored_hash = self.controller.db.get_config('app_password')
        self.is_setup = self.stored_hash is None
        
        self.failed_attempts = self.controller.db.get_failed_attempts()
        self.in_recovery_mode = self.failed_attempts >= 3 and not self.is_setup
        
        self.init_ui()

    def check_password_strength(self, text):
        if self.is_setup:
            c = 0
            if len(text) >= 8: c += 1
            if any(char.isupper() for char in text): c += 1
            if any(char.islower() for char in text): c += 1
            if any(char in "!@#$%^&*()-_+={}[]|\\:;\"'<>,.?/" for char in text): c += 1
            
            if len(text) == 0:
                self.strength_lbl.setText("")
            elif c <= 1:
                self.strength_lbl.setText(tr("PWD_STRENGTH_WEAK"))
                self.strength_lbl.setStyleSheet("color: #E74C3C; font-size: 11px;")
            elif c <= 3:
                self.strength_lbl.setText(tr("PWD_STRENGTH_GOOD"))
                self.strength_lbl.setStyleSheet("color: #F39C12; font-size: 11px;")
            else:
                self.strength_lbl.setText(tr("PWD_STRENGTH_STRONG"))
                self.strength_lbl.setStyleSheet("color: #2ECC71; font-size: 11px;")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        
        # Container Card
        card = QFrame()
        card.setObjectName("loginCard")
        card.setProperty("class", "card")
        card.setStyleSheet("#loginCard { background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 20px; }")
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        card.setLayout(card_layout)
        
        # Title
        title_text = tr("CREATE_PWD") if self.is_setup else tr("ENTER_PWD")
        self.title_lbl = QLabel(title_text)
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498DB; margin-bottom: 10px;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.title_lbl)
        
        # Password Field
        if not self.in_recovery_mode:
            card_layout.addWidget(QLabel(tr("PASSWORD") if self.is_setup else tr("MASTER_PASSWORD")))
            
        self.pwd_input = QLineEdit()
        if self.in_recovery_mode:
            self.title_lbl.setText(tr("RECOVERY_MODE"))
            q = self.controller.db.get_config('security_question') or "Pregunta de seguridad desconocida"
            self.sec_q_lbl = QLabel(f"{tr('QUESTION')}: {q}")
            self.sec_q_lbl.setStyleSheet("color: #E74C3C; font-weight: bold;")
            card_layout.addWidget(self.sec_q_lbl)
            self.pwd_input.setPlaceholderText(tr("YOUR_SECRET_ANS"))
            self.pwd_input.setProperty("class", "error-input") # Specific style if needed
        else:
            self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
            if self.is_setup:
                self.pwd_input.setPlaceholderText("••••••••")
        
        self.pwd_input.returnPressed.connect(self.submit)
        card_layout.addWidget(self.pwd_input)
        
        if self.is_setup:
            self.strength_lbl = QLabel("")
            self.strength_lbl.setFixedHeight(15) # Prevent jumping
            card_layout.addWidget(self.strength_lbl)
            self.pwd_input.textChanged.connect(self.check_password_strength)
            
            card_layout.addWidget(QLabel(tr("CONFIRM_PASSWORD")))
            self.pwd_confirm = QLineEdit()
            self.pwd_confirm.setEchoMode(QLineEdit.EchoMode.Password)
            self.pwd_confirm.setPlaceholderText("••••••••")
            self.pwd_confirm.returnPressed.connect(self.submit)
            card_layout.addWidget(self.pwd_confirm)
            
            # Security Question Setup
            card_layout.addSpacing(5)
            card_layout.addWidget(QLabel(tr("SEC_Q_TITLE")))
            self.sec_q_input = QLineEdit()
            self.sec_q_input.setPlaceholderText(tr("SEC_Q_PLACEHOLDER"))
            card_layout.addWidget(self.sec_q_input)
            
            self.sec_a_input = QLineEdit()
            self.sec_a_input.setPlaceholderText(tr("SEC_A_PLACEHOLDER"))
            card_layout.addWidget(self.sec_a_input)
            
            # Shortcut option
            self.shortcut_cb = QCheckBox(tr("CREATE_SHORTCUTS"))
            if sys.platform != "win32":
                self.shortcut_cb.hide()
            card_layout.addWidget(self.shortcut_cb)
        
        card_layout.addSpacing(10)

        # Submit Button
        self.submit_btn = QPushButton(tr("SAVE_AND_ENTER") if self.is_setup else (tr("RECOVER_ACCESS") if self.in_recovery_mode else tr("ENTER")))
        self.submit_btn.setProperty("class", "action-btn")
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self.submit)
        card_layout.addWidget(self.submit_btn)
        
        if self.is_setup:
            self.import_btn = QPushButton(tr("RESTORE_BACKUP"))
            self.import_btn.setStyleSheet("background-color: transparent; border: 1px solid #3498DB; color: #3498DB; border-radius: 6px; padding: 8px; font-weight: bold;")
            self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.import_btn.clicked.connect(self.import_database)
            card_layout.addWidget(self.import_btn)
            
        layout.addWidget(card)

    def import_database(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("SELECT_BACKUP"), "", "Bases de Datos (*.db)")
        if path:
            try:
                db_path = self.controller.db.db_path
                shutil.copy2(path, db_path)
                QMessageBox.information(self, tr("IMPORT_SUCCESS"), tr("IMPORT_SUCCESS_MSG"))
                
                # Restart Login Window logic to refresh state
                new_window = LoginWindow(self.controller, self.on_success)
                if hasattr(self, 'parent_window'):
                    self.parent_window = new_window
                new_window.show()
                self.close()
            except Exception as e:
                QMessageBox.critical(self, tr("IMPORT_ERROR"), f"{tr('IMPORT_ERROR_MSG')}\n{str(e)}")

    def trigger_nuke(self):
        QMessageBox.critical(self, tr("CRITICAL_SECURITY"), tr("CRITICAL_SECURITY_MSG"), QMessageBox.StandardButton.Ok)
        sys.exit(0)

    def submit(self):
        pwd = self.pwd_input.text()
        
        if self.in_recovery_mode:
            # Try recovery
            success, raw_pwd, wiped = self.controller.db.recover_master_password(pwd)
            if wiped:
                self.trigger_nuke()
            elif success:
                QMessageBox.information(self, tr("RECOVERED"), tr("RECOVERED_MSG").format(raw_pwd))
                self.controller.db.crypto.initialize_from_password(raw_pwd)
                self.on_success()
                self.close()
            else:
                QMessageBox.warning(self, tr("ERROR"), tr("LOGIN_ERROR_ANS").format(self.controller.db.get_failed_attempts()))
            return

        if self.is_setup:
            pwd_c = self.pwd_confirm.text()
            if pwd != pwd_c:
                QMessageBox.warning(self, tr("ERROR"), tr("PWD_MISMATCH"))
                return
            if len(pwd) < 4:
                QMessageBox.warning(self, tr("ERROR"), tr("PWD_TOO_SHORT"))
                return
            
            sq = self.sec_q_input.text()
            sa = self.sec_a_input.text()
            if not sq or not sa:
                QMessageBox.warning(self, tr("ERROR"), tr("SEC_Q_REQUIRED"))
                return
            
            # Save hash
            self.controller.db.set_config('app_password', hash_password(pwd))
            
            # Save security
            self.controller.db.setup_security_question(sq, sa, pwd)
            
            # Initialize Crypto
            self.controller.db.crypto.initialize_from_password(pwd)
            
            # Create shortcuts if checked
            if getattr(self, 'shortcut_cb', None) and self.shortcut_cb.isChecked():
                create_shortcuts()
            
            # Update state securely
            self.is_setup = False
            self.on_success()
            self.close()
        else:
            # Login check
            pwd_hash = hash_password(pwd)
            if pwd_hash == self.stored_hash:
                # Initialize Crypto
                self.controller.db.crypto.initialize_from_password(pwd)
                self.controller.db.reset_failed_attempts()
                self.on_success()
                self.close()
            else:
                wiped = self.controller.db.increment_failed_attempts()
                if wiped:
                    self.trigger_nuke()
                else:
                    fails = self.controller.db.get_failed_attempts()
                    if fails >= 3:
                        QMessageBox.warning(self, tr("LOCK_ACTIVE"), tr("LOCK_ACTIVE_MSG"))
                        self.pwd_input.clear()
                        # Switch to recovery UI by reinitiating window components or simpler:
                        self.in_recovery_mode = True
                        self.hide()
                        new_window = LoginWindow(self.controller, self.on_success)
                        self.parent_window = new_window
                        new_window.show()
                        self.close()
                    else:
                        QMessageBox.warning(self, tr("ERROR"), tr("PWD_INCORRECT").format(fails))
                        self.pwd_input.clear()

