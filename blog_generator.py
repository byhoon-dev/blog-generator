import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QGroupBox,
    QProgressBar,
    QStatusBar,
    QTabWidget,
)
from PyQt5.QtCore import Qt
from utils.utils import load_env_file
from tabs.title_generation_tab import TitleGenerationTab
from tabs.content_generation_tab import ContentGenerationTab
from tabs.blog_publish_tab import BlogPublishTab


class BlogGeneratorApp(QMainWindow):
    """블로그 글 자동 생성기 메인 애플리케이션"""
    
    def __init__(self):
        super().__init__()
        
        # 환경변수 로드
        self.env_vars = load_env_file()
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("블로그 글 자동 생성기 v2.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # API 설정 (공통)
        api_group = QGroupBox("API 설정")
        api_layout = QVBoxLayout(api_group)
        
        # 네이버 API
        naver_layout = QHBoxLayout()
        naver_layout.addWidget(QLabel("네이버 Client ID:"))
        self.naver_id_input = QLineEdit()
        self.naver_id_input.setPlaceholderText("네이버 개발자센터에서 발급받은 Client ID")
        naver_layout.addWidget(self.naver_id_input)
        
        naver_layout.addWidget(QLabel("Client Secret:"))
        self.naver_secret_input = QLineEdit()
        self.naver_secret_input.setEchoMode(QLineEdit.Password)
        self.naver_secret_input.setPlaceholderText("Client Secret")
        naver_layout.addWidget(self.naver_secret_input)
        api_layout.addLayout(naver_layout)
        
        # Gemini API
        gemini_layout = QHBoxLayout()
        gemini_layout.addWidget(QLabel("Gemini API Key:"))
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_key_input.setPlaceholderText("Google AI Studio에서 발급받은 Gemini API 키")
        gemini_layout.addWidget(self.gemini_key_input)
        api_layout.addLayout(gemini_layout)
        
        main_layout.addWidget(api_group)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 탭들 생성
        self.title_tab = TitleGenerationTab(self)
        self.content_tab = ContentGenerationTab(self)
        self.publish_tab = BlogPublishTab(self)
        
        # 탭 추가
        self.tab_widget.addTab(self.title_tab, "📝 제목 생성")
        self.tab_widget.addTab(self.content_tab, "✍️ 글 생성")
        self.tab_widget.addTab(self.publish_tab, "🚀 블로그 발행")
        
        main_layout.addWidget(self.tab_widget)
        
        # 진행 상황 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비됨")
        
        # 스타일 적용
        self.apply_styles()
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
                border-radius: 4px;
                margin-top: 5px;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                border: 1px solid #c0c0c0;
                padding: 15px 30px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
                min-height: 20px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                color: #2196f3;
            }
            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #2196f3;
            }
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f8f9fa;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QSpinBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
    
    # TODO 나중에 삭제
    def load_settings(self):
        """설정 로드 (환경변수)"""
        # 환경변수에서 먼저 로드
        naver_id = os.getenv("NAVER_CLIENT_ID", "")
        naver_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        # GUI에 설정값 표시
        self.naver_id_input.setText(naver_id)
        self.naver_secret_input.setText(naver_secret)
        self.gemini_key_input.setText(gemini_key)
        
        # 환경변수가 설정되어 있으면 입력 필드를 읽기 전용으로 만들고 힌트 표시
        if naver_id:
            self.naver_id_input.setReadOnly(True)
            self.naver_id_input.setStyleSheet("background-color: #f0f0f0;")
            self.naver_id_input.setToolTip("환경변수에서 로드됨 (.env 파일)")
        
        if naver_secret:
            self.naver_secret_input.setReadOnly(True)
            self.naver_secret_input.setStyleSheet("background-color: #f0f0f0;")
            self.naver_secret_input.setToolTip("환경변수에서 로드됨 (.env 파일)")
        
        if gemini_key:
            self.gemini_key_input.setReadOnly(True)
            self.gemini_key_input.setStyleSheet("background-color: #f0f0f0;")
            self.gemini_key_input.setToolTip("환경변수에서 로드됨 (.env 파일)")
    
    def update_status(self, message):
        """상태 업데이트"""
        self.status_bar.showMessage(message)
    

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = BlogGeneratorApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()