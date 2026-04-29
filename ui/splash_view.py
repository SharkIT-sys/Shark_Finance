import os
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt

class VideoSplashScreen(QWidget):
    def __init__(self, video_path, on_finished_callback):
        super().__init__()
        self.on_finished_callback = on_finished_callback
        
        self.setWindowTitle("Shark Contabilidad")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Optionally, set a specific size
        self.resize(800, 450)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        
        # Audio output set to 0 to satisfy "sin audio" requirement
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.0)
        self.player.setAudioOutput(self.audio_output)
        
        # Ensure path format is correct for QUrl
        file_url = QUrl.fromLocalFile(os.path.abspath(video_path))
        self.player.setSource(file_url)
        
        self.player.mediaStatusChanged.connect(self.check_status)
        
        # Center on screen
        self.center_on_screen()
        
        self.player.play()
        
    def center_on_screen(self):
        screen = self.screen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
    def check_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.on_finished_callback()
            self.close()
