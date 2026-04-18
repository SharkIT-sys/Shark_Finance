import sys
import os
from PyQt6.QtWidgets import QApplication
from database.db_manager import DBManager
from controllers.finance_controller import FinanceController
from ui.login_view import LoginWindow
from ui.main_window import MainWindow
from utils.translator import Translator

class AppOrchestrator:
    def __init__(self, controller):
        self.controller = controller
        self.main_window = None
        self.login_window = None

    def start(self):
        self.login_window = LoginWindow(self.controller, self.on_login_success)
        self.login_window.show()

    def on_login_success(self):
        self.main_window = MainWindow(self.controller)
        self.main_window.show()

def main():
    app = QApplication(sys.argv)
    
    # User Profile Path for Database (Installs to System)
    user_folder = os.path.join(os.path.expanduser("~"), "Shark Contabilidad")
    os.makedirs(user_folder, exist_ok=True)
    
    # Hide the directory on Windows
    if sys.platform == "win32":
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        attrs = ctypes.windll.kernel32.GetFileAttributesW(user_folder)
        if attrs != -1 and not (attrs & FILE_ATTRIBUTE_HIDDEN):
            ctypes.windll.kernel32.SetFileAttributesW(user_folder, attrs | FILE_ATTRIBUTE_HIDDEN)

    db_path = os.path.join(user_folder, "budget_app.db")
    
    # Application paths for resources
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    # Load QSS Style
    qss_path = os.path.join(base_path, "ui", "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            
    # Initialize DB
    db_manager = DBManager(db_path)
    
    # Init Language
    lang = db_manager.get_config('language') or 'es'
    Translator.set_language(lang)
    
    # Auto-Sync before launching to ensure we have the latest DB state
    from utils.sync_manager import SyncManager
    sync_man = SyncManager(db_manager)
    print("Comprobando sincronización con el servidor...")
    success, msg = sync_man.sync_bidirectional()
    print(f"Sync: {msg}")

    # Start Controller
    controller = FinanceController(db_manager)
    
    # Start Orchestrator
    orchestrator = AppOrchestrator(controller)
    orchestrator.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
