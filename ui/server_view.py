import socket
import threading
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QLabel, 
                             QPushButton, QHBoxLayout, QMessageBox, QFileDialog, QFrame,
                             QInputDialog, QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
import io
try:
    import qrcode
except ImportError:
    qrcode = None

from utils.translator import tr
from utils.pack_server import export_server_kit

class ServerView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.server_thread = None
        self.server_running = False
        self.init_ui()

    def get_local_ip(self):
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        c_layout = QVBoxLayout()
        c_layout.setContentsMargins(40, 40, 40, 40)
        c_layout.setSpacing(20)
        container.setLayout(c_layout)

        title = QLabel(f'🌐 {tr("SERVER_CENTER")}')
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF; margin-bottom: 20px;")
        c_layout.addWidget(title)
        
        desc = QLabel(tr("SERVER_DESC"))
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 14px; color: #E0E0E0; margin-bottom: 20px;")
        c_layout.addWidget(desc)

        # 1. MODO WIFI LOCAL (Background Flask)
        card1 = QFrame()
        card1.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 20px;")
        l1 = QVBoxLayout()
        card1.setLayout(l1)
        
        t1 = QLabel(tr("LOCAL_WIFI"))
        t1.setStyleSheet("font-size: 18px; font-weight: bold; color: #F1C40F;")
        l1.addWidget(t1)
        
        d1 = QLabel(tr("LAN_DESC"))
        d1.setWordWrap(True)
        d1.setStyleSheet("font-size: 14px; color: #E0E0E0; margin-bottom: 10px;")
        l1.addWidget(d1)
        
        self.lbl_ip = QLabel(tr("IP_ADDRESS_LABEL"))
        self.lbl_ip.setStyleSheet("color: #FFFFFF; font-weight: bold; font-family: monospace; background-color: #2A2A35; padding: 8px; border-radius: 6px;")
        l1.addWidget(self.lbl_ip)
        
        # QR Code Container
        self.qr_container = QWidget()
        self.qr_layout = QVBoxLayout(self.qr_container)
        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_qr.setMinimumSize(200, 200)
        self.qr_layout.addWidget(self.lbl_qr)
        self.qr_container.hide() # Hidden until server starts
        l1.addWidget(self.qr_container)
        
        self.btn_toggle_server = QPushButton(tr("START_SERVER"))
        self.btn_toggle_server.setStyleSheet("background-color: #27AE60; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold; margin-top: 10px;")
        self.btn_toggle_server.clicked.connect(self.toggle_local_server)
        l1.addWidget(self.btn_toggle_server)
        c_layout.addWidget(card1)

        # 2. MODO EXPORTAR ZIP
        card2 = QFrame()
        card2.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 20px;")
        l2 = QVBoxLayout()
        card2.setLayout(l2)
        
        t2 = QLabel(tr("EXPORT_KIT"))
        t2.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498DB;")
        l2.addWidget(t2)
        
        d2 = QLabel(tr("EXPORT_KIT_DESC"))
        d2.setWordWrap(True)
        d2.setStyleSheet("font-size: 14px; color: #E0E0E0; margin-bottom: 10px;")
        l2.addWidget(d2)
        
        btn_export = QPushButton(tr("EXPORT_KIT_BTN"))
        btn_export.setStyleSheet("background-color: #2980B9; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold;")
        btn_export.clicked.connect(self.export_kit)
        l2.addWidget(btn_export)
        c_layout.addWidget(card2)

        # 3. MODO INSTALADOR SSH
        card3 = QFrame()
        card3.setStyleSheet("background-color: #1E1E24; border-radius: 12px; border: 1px solid #2C2C35; padding: 20px;")
        l3 = QVBoxLayout()
        card3.setLayout(l3)
        
        t3 = QLabel(tr("REMOTE_INSTALLER"))
        t3.setStyleSheet("font-size: 18px; font-weight: bold; color: #9B59B6;")
        l3.addWidget(t3)
        
        d3 = QLabel(tr("REMOTE_INSTALLER_DESC"))
        d3.setWordWrap(True)
        d3.setStyleSheet("font-size: 14px; color: #E0E0E0; margin-bottom: 10px;")
        l3.addWidget(d3)
        
        btn_ssh = QPushButton(tr("DEPLOY_REMOTE_BTN"))
        btn_ssh.setStyleSheet("background-color: #8E44AD; color: white; border: none; border-radius: 6px; padding: 10px; font-weight: bold;")
        btn_ssh.clicked.connect(self.ssh_deploy)
        l3.addWidget(btn_ssh)
        
        self.btn_sync = QPushButton("Sincronizar Ahora (Nube)")
        self.btn_sync.setStyleSheet("background-color: transparent; color: #8E44AD; border: 1px solid #8E44AD; border-radius: 6px; padding: 10px; font-weight: bold;")
        self.btn_sync.clicked.connect(self.manual_sync)
        if not self.controller.db.get_config('sync_enabled') == '1':
            self.btn_sync.hide()
        l3.addWidget(self.btn_sync)
        
        c_layout.addWidget(card3)

        c_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def toggle_local_server(self):
        if not self.server_running:
            from web_app.app import app
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            
            def run_flask():
                app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
                
            self.server_thread = threading.Thread(target=run_flask, daemon=True)
            self.server_thread.start()
            self.server_running = True
            
            ip = self.get_local_ip()
            url = f"http://{ip}:5000"
            self.lbl_ip.setText(tr("IP_ADDRESS_ACTIVE").format(ip))
            self.lbl_ip.setStyleSheet("color: #2ECC71; font-weight: bold; font-family: monospace; background-color: #2A2A35; padding: 8px; border-radius: 6px;")
            
            # Generate QR
            self.show_qr(url)
            
            self.btn_toggle_server.setText(tr("SERVER_ONLINE"))
            self.btn_toggle_server.setStyleSheet("background-color: #2C3E50; color: #27AE60; border: 1px solid #27AE60; border-radius: 6px; padding: 10px; font-weight: bold; margin-top: 10px;")
            self.btn_toggle_server.setEnabled(False) # No podemos pararlo facil sin ensuciar memoria
            QMessageBox.information(self, tr("SERVER_ACTIVE_TITLE"), tr("SERVER_ACTIVE_MSG").format(ip))
            
    def show_qr(self, url):
        if not qrcode:
            return
            
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Generate QR Image (Pillow) - Theme matching (Dark)
        # Using white for data and transparent/dark for back
        img = qr.make_image(fill_color="white", back_color="#1E1E24")
        
        # Convert PIL image to QPixmap
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage.fromData(buf.getvalue())
        pixmap = QPixmap.fromImage(qimg)
        
        # Scale to decent size
        scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.lbl_qr.setPixmap(scaled_pixmap)
        self.qr_container.show()
        
    def export_kit(self):
        path, _ = QFileDialog.getSaveFileName(self, tr("EXPORT_KIT_BTN"), "Shark_Server_Kit.zip", "Archivos ZIP (*.zip)")
        if path:
            success, msg = export_server_kit(path)
            if success:
                QMessageBox.information(self, tr("EXPORTED_TITLE"), tr("EXPORTED_MSG"))
            else:
                QMessageBox.critical(self, tr("ERROR"), f"{tr('ERROR')} {msg}")

    def ssh_deploy(self):
        try:
            import subprocess
            import os
            import sys
            import uuid
            
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            script_path = os.path.join(base_path, "deploy.ps1")
            if not os.path.exists(script_path):
                QMessageBox.warning(self, tr("ERROR"), tr("SCRIPT_NOT_FOUND"))
                return
                
            # Preguntar por la dirección SSH
            ssh_server, ok = QInputDialog.getText(
                self, tr("DEPLOY_REMOTE_BTN"), 
                tr("ENTER_SSH_ADDRESS") + "\n(ej: shark@192.168.1.50):",
                QLineEdit.EchoMode.Normal, "shark@sharkserver"
            )
            if not ok or not ssh_server.strip():
                return
                
            ssh_target = ssh_server.strip()
            
            # Extract IP from target to build Server URL (assuming standard 5000 port for Docker)
            ip_part = ssh_target.split('@')[-1]
            sync_url = f"http://{ip_part}:5000"
            sync_token = uuid.uuid4().hex
            
            # Guardamos la configuración de sync en la base de datos local ANTES de comprimir, 
            # así se sube ya configurada en el servidor si Javi exporta
            self.controller.db.set_config('sync_enabled', '1')
            self.controller.db.set_config('sync_url', sync_url)
            self.controller.db.set_config('sync_token', sync_token)

            QMessageBox.information(self, tr("LAUNCHING_INSTALLER_TITLE"), tr("LAUNCHING_INSTALLER_MSG"))
            
            # Lanzamos PowerShell externo pasando el argumento -ServerAddress y -SyncToken
            cmd = f'start cmd /c powershell -ExecutionPolicy Bypass -NoExit -File "{script_path}" -ServerAddress "{ssh_target}" -SyncToken "{sync_token}"'
            subprocess.Popen(cmd, shell=True, cwd=base_path)
            
        except Exception as e:
            QMessageBox.critical(self, tr("ERROR"), f"{tr('DEPLOY_FAILED')}\n{str(e)}")

    def manual_sync(self):
        from utils.sync_manager import SyncManager
        import threading
        
        self.btn_sync.setEnabled(False)
        self.btn_sync.setText("Sincronizando...")
        
        def run_sync():
            sync_man = SyncManager(self.controller.db)
            success, msg = sync_man.sync_bidirectional()
            return success, msg
            
        def on_sync_done(success, msg):
            self.btn_sync.setEnabled(True)
            self.btn_sync.setText("Sincronizar Ahora (Nube)")
            if success:
                QMessageBox.information(self, "Sincronización", msg)
                # Opcional: Notificar al parent para refrescar UI si hubo cambios
            else:
                QMessageBox.warning(self, "Aviso de Sincronización", msg)
                
        class SyncThread(threading.Thread):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback
            def run(self):
                success, msg = run_sync()
                # Use QTimer or invokeMethod to call safely from thread in real app,
                # but simple callback might work depending on PyQt strictness. 
                # Better safe using signal/slot, or lambda in QTimer.
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                QMetaObject.invokeMethod(self.callback.__self__, self.callback.__name__, Qt.ConnectionType.QueuedConnection, Q_ARG(bool, success), Q_ARG(str, msg))

        # We'll avoid complex threading if we just block for 1 second.
        # But for robustness:
        success, msg = run_sync()
        on_sync_done(success, msg)
