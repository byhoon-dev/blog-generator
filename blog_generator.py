import sys
import os
import json
import requests
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QStatusBar,
    QSplitter,
    QFrame,
    QTabWidget,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon


def load_env_file(file_path=".env"):
    """
    .env 파일을 읽어서 환경변수로 설정
    python-dotenv가 없어도 작동하는 간단한 구현
    """
    env_vars = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
                        os.environ[key] = value
        except Exception as e:
            print(f".env 파일 로드 오류: {e}")
    return env_vars


class NaverSearchWorker(QThread):
    """네이버 블로그 검색 워커"""

    search_completed = pyqtSignal(list)
    search_failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, keyword, client_id, client_secret):
        super().__init__()
        self.keyword = keyword
        self.client_id = client_id
        self.client_secret = client_secret

    def run(self):
        try:
            self.progress.emit("네이버 블로그 검색 중...")

            url = "https://openapi.naver.com/v1/search/blog"
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
            }
            params = {"query": self.keyword, "display": 20, "sort": "sim"}  # 정확도순

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                blog_posts = []

                for item in data.get("items", []):
                    blog_post = {
                        "title": item.get("title", "")
                        .replace("<b>", "")
                        .replace("</b>", ""),
                        "description": item.get("description", "")
                        .replace("<b>", "")
                        .replace("</b>", ""),
                        "link": item.get("link", ""),
                        "bloggername": item.get("bloggername", ""),
                        "postdate": item.get("postdate", ""),
                    }
                    blog_posts.append(blog_post)

                self.progress.emit(f"검색 완료: {len(blog_posts)}개 글 발견")
                self.search_completed.emit(blog_posts)
            else:
                self.search_failed.emit(f"네이버 API 오류: {response.status_code}")

        except Exception as e:
            self.search_failed.emit(f"검색 오류: {str(e)}")


class TitleGenerateWorker(QThread):
    """Gemini 제목 생성 워커"""

    titles_generated = pyqtSignal(list)
    generation_failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, blog_posts, count, api_key):
        super().__init__()
        self.blog_posts = blog_posts
        self.count = count
        self.api_key = api_key

    def run(self):
        try:
            self.progress.emit("Gemini로 제목 생성 중...")

            # 블로그 글 내용 요약
            content_summary = ""
            for i, post in enumerate(self.blog_posts[:10], 1):  # 상위 10개만 사용
                content_summary += f"{i}. {post['title']}\n{post['description']}\n\n"

            prompt = f"""
다음은 특정 키워드로 검색한 상위 블로그 글들의 제목과 내용입니다:

{content_summary}

위 내용들을 분석하여 SEO에 최적화되고 클릭률이 높은 블로그 제목을 {self.count}개 생성해주세요.
1. 제목의 구조적 특징(길이, 문장 구조, 문체 등)
2. 자주 사용되는 핵심 키워드와 표현
3. 제목 구성의 패턴(예: 질문형, 리스트형, 비교형 등)
4. 독자의 관심을 끌기 위한 기법(감정적 표현, 호기심 유발 등)
5. 제목의 SEO 최적화 특징

제목만 번호와 함께 나열해주세요.
"""

            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key,
            }

            data = {"contents": [{"parts": [{"text": prompt}]}]}

            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers=headers,
                json=data,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]

                # 제목 추출
                titles = []
                lines = content.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        # 번호나 - 제거
                        title = line.split(".", 1)[-1].split("-", 1)[-1].strip()
                        if title:
                            titles.append(title)

                self.progress.emit(f"제목 생성 완료: {len(titles)}개")
                self.titles_generated.emit(titles)
            else:
                self.generation_failed.emit(f"Gemini API 오류: {response.status_code}")

        except Exception as e:
            self.generation_failed.emit(f"제목 생성 오류: {str(e)}")


class ContentGenerateWorker(QThread):
    """Gemini 글 생성 워커"""

    content_generated = pyqtSignal(str, str)  # title, content
    generation_failed = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, title, prompt, api_key):
        super().__init__()
        self.title = title
        self.prompt = prompt
        self.api_key = api_key

    def run(self):
        try:
            self.progress.emit(f"'{self.title}' 글 생성 중...")

            full_prompt = f"""
제목: {self.title}

{self.prompt}

위 제목으로 블로그 글을 작성해주세요.
"""

            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key,
            }

            data = {"contents": [{"parts": [{"text": full_prompt}]}]}

            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers=headers,
                json=data,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]

                self.progress.emit("글 생성 완료")
                self.content_generated.emit(self.title, content)
            else:
                self.generation_failed.emit(f"Gemini API 오류: {response.status_code}")

        except Exception as e:
            self.generation_failed.emit(f"글 생성 오류: {str(e)}")


class BlogGeneratorTabs(QMainWindow):
    def __init__(self):
        super().__init__()
        self.blog_posts = []
        self.generated_titles = []

        # 환경변수 로드
        self.env_vars = load_env_file()

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("블로그 글 자동 생성기")
        self.setGeometry(100, 100, 1000, 700)

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
        self.naver_id_input.setPlaceholderText(
            "네이버 개발자센터에서 발급받은 Client ID"
        )
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
        self.gemini_key_input.setPlaceholderText(
            "Google AI Studio에서 발급받은 Gemini API 키"
        )
        gemini_layout.addWidget(self.gemini_key_input)
        api_layout.addLayout(gemini_layout)

        main_layout.addWidget(api_group)

        # 탭 위젯
        self.tab_widget = QTabWidget()

        # 탭 1: 제목 생성
        self.create_title_generation_tab()

        # 탭 2: 글 생성
        self.create_content_generation_tab()

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
        self.setStyleSheet(
            """
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
        """
        )

    def create_title_generation_tab(self):
        """제목 생성 탭 생성"""
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)

        # 키워드 검색
        search_group = QGroupBox("키워드 검색")
        search_layout = QHBoxLayout(search_group)

        search_layout.addWidget(QLabel("키워드:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("검색할 키워드를 입력하세요")
        search_layout.addWidget(self.keyword_input)

        self.search_btn = QPushButton("🔍 검색")
        self.search_btn.clicked.connect(self.search_blogs)
        self.search_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #bbbbbb;
            }
        """
        )
        search_layout.addWidget(self.search_btn)

        tab1_layout.addWidget(search_group)

        # 수평 분할
        splitter = QSplitter(Qt.Horizontal)

        # 왼쪽: 검색 결과
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        search_result_group = QGroupBox(
            "검색된 블로그 글 (제목 위에 마우스를 올리면 상세 정보)"
        )
        search_result_layout = QVBoxLayout(search_result_group)

        self.search_result_list = QListWidget()
        self.search_result_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
        """
        )
        self.search_result_list.setAlternatingRowColors(True)
        search_result_layout.addWidget(self.search_result_list)

        left_layout.addWidget(search_result_group)
        splitter.addWidget(left_widget)

        # 오른쪽: 제목 생성
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 제목 생성 설정
        title_gen_group = QGroupBox("제목 생성")
        title_gen_layout = QVBoxLayout(title_gen_group)

        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("생성할 제목 개수:"))
        self.title_count_spin = QSpinBox()
        self.title_count_spin.setRange(1, 20)
        self.title_count_spin.setValue(5)
        count_layout.addWidget(self.title_count_spin)
        count_layout.addStretch()

        self.generate_titles_btn = QPushButton("✨ 제목 생성")
        self.generate_titles_btn.clicked.connect(self.generate_titles)
        self.generate_titles_btn.setEnabled(False)
        self.generate_titles_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:disabled {
                background-color: #bbbbbb;
            }
        """
        )
        count_layout.addWidget(self.generate_titles_btn)

        title_gen_layout.addLayout(count_layout)
        right_layout.addWidget(title_gen_group)

        # 생성된 제목 리스트
        titles_group = QGroupBox("생성된 제목")
        titles_layout = QVBoxLayout(titles_group)

        self.titles_list = QListWidget()
        self.titles_list.setStyleSheet(
            """
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
                background-color: white;
            }
            QListWidget::item:hover {
                background-color: #fff3e0;
            }
            QListWidget::item:selected {
                background-color: #ff9800;
                color: white;
                font-weight: bold;
            }
        """
        )
        titles_layout.addWidget(self.titles_list)

        # 제목 편집 버튼들
        title_btn_layout = QHBoxLayout()
        self.edit_title_btn = QPushButton("✏️ 편집")
        self.edit_title_btn.clicked.connect(self.edit_selected_title)
        self.edit_title_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """
        )

        self.delete_title_btn = QPushButton("🗑️ 삭제")
        self.delete_title_btn.clicked.connect(self.delete_selected_title)
        self.delete_title_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """
        )

        title_btn_layout.addWidget(self.edit_title_btn)
        title_btn_layout.addWidget(self.delete_title_btn)
        title_btn_layout.addStretch()

        titles_layout.addLayout(title_btn_layout)
        right_layout.addWidget(titles_group)

        splitter.addWidget(right_widget)
        tab1_layout.addWidget(splitter)

        self.tab_widget.addTab(tab1, "제목 생성")

    def create_content_generation_tab(self):
        """글 생성 탭 생성"""
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)

        # 수평 분할
        splitter = QSplitter(Qt.Horizontal)

        # 왼쪽: 제목 선택
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 제목 선택
        title_select_group = QGroupBox("제목 선택 (여러 개 선택 가능)")
        title_select_layout = QVBoxLayout(title_select_group)

        self.content_titles_list = QListWidget()
        self.content_titles_list.setSelectionMode(QListWidget.MultiSelection)
        self.content_titles_list.setStyleSheet(
            """
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #eee;
                background-color: white;
                border-left: 4px solid transparent;
            }
            QListWidget::item:hover {
                background-color: #e8f5e8;
                border-left-color: #4caf50;
            }
            QListWidget::item:selected {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                border-left-color: #2e7d32;
            }
        """
        )
        title_select_layout.addWidget(self.content_titles_list)

        # 선택 관련 버튼들
        select_btn_layout = QHBoxLayout()

        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(self.select_all_titles)
        select_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """
        )

        clear_selection_btn = QPushButton("선택 해제")
        clear_selection_btn.clicked.connect(self.clear_title_selection)
        clear_selection_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """
        )

        select_btn_layout.addWidget(select_all_btn)
        select_btn_layout.addWidget(clear_selection_btn)
        select_btn_layout.addStretch()

        title_select_layout.addLayout(select_btn_layout)

        # 제목 동기화 버튼
        sync_btn = QPushButton("🔄 제목 목록 새로고침")
        sync_btn.clicked.connect(self.sync_titles)
        sync_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
        """
        )
        title_select_layout.addWidget(sync_btn)

        left_layout.addWidget(title_select_group)

        # 생성 로그
        log_group = QGroupBox("생성 로그")
        log_layout = QVBoxLayout(log_group)

        self.generation_log_text = QTextEdit()
        self.generation_log_text.setReadOnly(True)
        self.generation_log_text.setMaximumHeight(200)
        self.generation_log_text.setStyleSheet(
            "font-family: 'Consolas', 'Monaco', monospace; font-size: 10px;"
        )
        log_layout.addWidget(self.generation_log_text)

        left_layout.addWidget(log_group)
        splitter.addWidget(left_widget)

        # 오른쪽: 글 생성 설정
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 프롬프트 설정
        prompt_group = QGroupBox("글 생성 프롬프트")
        prompt_layout = QVBoxLayout(prompt_group)

        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(200)
        self.prompt_input.setPlaceholderText(
            "글 생성 프롬프트를 입력하세요 (비워두면 기본 프롬프트 사용)"
        )

        # 기본 프롬프트 설정
        default_prompt = """다음 조건에 맞는 블로그 글을 작성해주세요:

1. 2000-3000자 분량
2. SEO 최적화된 내용
3. 독자에게 유용한 정보 제공
4. 자연스러운 한국어 문체
5. 소제목을 활용한 구조화된 글
6. 마지막에 요약 또는 결론 포함

글의 톤앤매너는 친근하고 전문적으로 작성해주세요."""

        self.prompt_input.setPlainText(default_prompt)
        prompt_layout.addWidget(self.prompt_input)

        right_layout.addWidget(prompt_group)

        # 저장 경로 설정
        save_group = QGroupBox("저장 설정")
        save_layout = QHBoxLayout(save_group)

        save_layout.addWidget(QLabel("저장 경로:"))
        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("글을 저장할 폴더 경로")
        save_layout.addWidget(self.save_path_input)

        self.browse_btn = QPushButton("📁 찾아보기")
        self.browse_btn.clicked.connect(self.browse_save_path)
        self.browse_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #607d8b;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455a64;
            }
        """
        )
        save_layout.addWidget(self.browse_btn)

        right_layout.addWidget(save_group)

        # 글 생성 버튼
        self.generate_content_btn = QPushButton("📝 선택된 제목들로 일괄 글 생성")
        self.generate_content_btn.clicked.connect(self.generate_multiple_contents)
        self.generate_content_btn.setEnabled(False)
        self.generate_content_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                font-weight: bold;
                padding: 15px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        )
        right_layout.addWidget(self.generate_content_btn)

        splitter.addWidget(right_widget)
        tab2_layout.addWidget(splitter)

        self.tab_widget.addTab(tab2, "글 생성")

    def load_settings(self):
        """설정 로드 (환경변수)"""
        # 환경변수에서 먼저 로드
        naver_id = os.getenv("NAVER_CLIENT_ID", "")
        naver_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        save_path = os.getenv("DEFAULT_SAVE_PATH", "")

        # GUI에 설정값 표시
        self.naver_id_input.setText(naver_id)
        self.naver_secret_input.setText(naver_secret)
        self.gemini_key_input.setText(gemini_key)
        self.save_path_input.setText(save_path)

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

        if save_path:
            self.save_path_input.setReadOnly(True)
            self.save_path_input.setStyleSheet("background-color: #f0f0f0;")
            self.save_path_input.setToolTip("환경변수에서 로드됨 (.env 파일)")

    def search_blogs(self):
        """네이버 블로그 검색"""
        keyword = self.keyword_input.text().strip()

        # 환경변수 우선, 없으면 GUI 입력값 사용
        client_id = os.getenv("NAVER_CLIENT_ID") or self.naver_id_input.text().strip()
        client_secret = (
            os.getenv("NAVER_CLIENT_SECRET") or self.naver_secret_input.text().strip()
        )

        if not keyword:
            QMessageBox.warning(self, "입력 오류", "키워드를 입력하세요.")
            return

        if not client_id or not client_secret:
            QMessageBox.warning(
                self, "API 오류", "네이버 API 정보를 입력하거나 .env 파일에 설정하세요."
            )
            return

        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # 검색 워커 시작
        self.search_worker = NaverSearchWorker(keyword, client_id, client_secret)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_failed.connect(self.on_search_failed)
        self.search_worker.progress.connect(self.update_status)
        self.search_worker.start()

    def on_search_completed(self, blog_posts):
        """검색 완료 처리"""
        self.blog_posts = blog_posts
        self.search_btn.setEnabled(True)
        self.generate_titles_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # 검색 결과를 리스트로 표시 (제목만)
        self.search_result_list.clear()

        for i, post in enumerate(blog_posts, 1):
            item_text = f"{i:2d}. {post['title']}"
            item = QListWidgetItem(item_text)
            # 툴팁으로 상세 정보 표시
            tooltip = f"블로거: {post['bloggername']}\n날짜: {post['postdate']}\n내용: {post['description'][:200]}...\n링크: {post['link']}"
            item.setToolTip(tooltip)
            self.search_result_list.addItem(item)

        self.update_status(f"검색 완료: {len(blog_posts)}개 블로그 글 발견")

    def on_search_failed(self, error_msg):
        """검색 실패 처리"""
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.update_status("검색 실패")
        QMessageBox.critical(self, "검색 실패", error_msg)

    def generate_titles(self):
        """제목 생성"""
        if not self.blog_posts:
            QMessageBox.warning(self, "데이터 없음", "먼저 키워드 검색을 실행하세요.")
            return

        # 환경변수 우선, 없으면 GUI 입력값 사용
        api_key = os.getenv("GEMINI_API_KEY") or self.gemini_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(
                self, "API 오류", "Gemini API 키를 입력하거나 .env 파일에 설정하세요."
            )
            return

        count = self.title_count_spin.value()

        self.generate_titles_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # 제목 생성 워커 시작
        self.title_worker = TitleGenerateWorker(self.blog_posts, count, api_key)
        self.title_worker.titles_generated.connect(self.on_titles_generated)
        self.title_worker.generation_failed.connect(self.on_title_generation_failed)
        self.title_worker.progress.connect(self.update_status)
        self.title_worker.start()

    def on_titles_generated(self, titles):
        """제목 생성 완료 처리"""
        self.generated_titles.extend(titles)

        # 리스트에 제목 추가
        for title in titles:
            self.titles_list.addItem(title)

        self.generate_titles_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        self.update_status(f"제목 생성 완료: {len(titles)}개")

    def on_title_generation_failed(self, error_msg):
        """제목 생성 실패 처리"""
        self.generate_titles_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.update_status("제목 생성 실패")
        QMessageBox.critical(self, "제목 생성 실패", error_msg)

    def edit_selected_title(self):
        """선택된 제목 편집"""
        current_item = self.titles_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "선택 오류", "편집할 제목을 선택하세요.")
            return

        from PyQt5.QtWidgets import QInputDialog

        new_title, ok = QInputDialog.getText(
            self, "제목 편집", "새 제목:", text=current_item.text()
        )

        if ok and new_title.strip():
            current_item.setText(new_title.strip())

    def delete_selected_title(self):
        """선택된 제목 삭제"""
        current_row = self.titles_list.currentRow()
        if current_row >= 0:
            self.titles_list.takeItem(current_row)

    def sync_titles(self):
        """제목 목록 동기화"""
        self.content_titles_list.clear()

        for i in range(self.titles_list.count()):
            item = self.titles_list.item(i)
            self.content_titles_list.addItem(item.text())

        if self.content_titles_list.count() > 0:
            self.generate_content_btn.setEnabled(True)
            self.update_status(
                f"{self.content_titles_list.count()}개 제목을 동기화했습니다."
            )
        else:
            self.generate_content_btn.setEnabled(False)
            self.update_status("동기화할 제목이 없습니다.")

    def select_all_titles(self):
        """모든 제목 선택"""
        for i in range(self.content_titles_list.count()):
            self.content_titles_list.item(i).setSelected(True)

    def clear_title_selection(self):
        """제목 선택 해제"""
        self.content_titles_list.clearSelection()

    def browse_save_path(self):
        """저장 경로 선택"""
        folder = QFileDialog.getExistingDirectory(self, "저장 폴더 선택")
        if folder:
            self.save_path_input.setText(folder)

    def generate_multiple_contents(self):
        """선택된 여러 제목으로 일괄 글 생성"""
        selected_items = self.content_titles_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "선택 오류", "글을 생성할 제목을 하나 이상 선택하세요."
            )
            return

        # 환경변수 우선, 없으면 GUI 입력값 사용
        api_key = os.getenv("GEMINI_API_KEY") or self.gemini_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(
                self, "API 오류", "Gemini API 키를 입력하거나 .env 파일에 설정하세요."
            )
            return

        save_path = (
            os.getenv("DEFAULT_SAVE_PATH") or self.save_path_input.text().strip()
        )
        if not save_path:
            QMessageBox.warning(
                self, "경로 오류", "저장 경로를 선택하거나 .env 파일에 설정하세요."
            )
            return

        # 확인 메시지
        reply = QMessageBox.question(
            self,
            "일괄 생성 확인",
            f"{len(selected_items)}개의 제목으로 글을 생성하시겠습니까?\n\n"
            f"예상 소요 시간: 약 {len(selected_items) * 30}초",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # 선택된 제목들 저장
        self.selected_titles = [item.text() for item in selected_items]
        self.current_title_index = 0
        self.total_titles = len(self.selected_titles)
        self.generated_count = 0

        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            prompt = """다음 조건에 맞는 블로그 글을 작성해주세요:

1. 2000-3000자 분량
2. SEO 최적화된 내용
3. 독자에게 유용한 정보 제공
4. 자연스러운 한국어 문체
5. 소제목을 활용한 구조화된 글
6. 마지막에 요약 또는 결론 포함

글의 톤앤매너는 친근하고 전문적으로 작성해주세요."""

        self.batch_prompt = prompt

        # UI 비활성화
        self.generate_content_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, self.total_titles)
        self.progress_bar.setValue(0)

        # 첫 번째 제목으로 시작
        self.generate_next_content(api_key)

    def generate_next_content(self, api_key):
        """다음 제목으로 글 생성"""
        if self.current_title_index >= len(self.selected_titles):
            # 모든 글 생성 완료
            self.on_batch_generation_completed()
            return

        title = self.selected_titles[self.current_title_index]

        # 글 생성 워커 시작
        self.content_worker = ContentGenerateWorker(title, self.batch_prompt, api_key)
        self.content_worker.content_generated.connect(self.on_batch_content_generated)
        self.content_worker.generation_failed.connect(self.on_batch_content_failed)
        self.content_worker.progress.connect(self.update_status)
        self.content_worker.start()

    def on_batch_content_generated(self, title, content):
        """일괄 생성 중 개별 글 생성 완료"""
        try:
            # 파일 저장
            safe_title = "".join(
                c for c in title if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            save_path = self.save_path_input.text()
            full_path = os.path.join(save_path, filename)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(f"제목: {title}\n")
                f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)

            # 진행 상황 업데이트
            self.generated_count += 1
            self.current_title_index += 1
            self.progress_bar.setValue(self.generated_count)

            # 로그 추가
            self.generation_log_text.append(
                f"[{self.generated_count}/{self.total_titles}] {title} - 완료"
            )

            # 다음 제목으로 진행
            api_key = (
                os.getenv("GEMINI_API_KEY") or self.gemini_key_input.text().strip()
            )
            self.generate_next_content(api_key)

        except Exception as e:
            self.on_batch_content_failed(f"파일 저장 오류: {str(e)}")

    def on_batch_content_failed(self, error_msg):
        """일괄 생성 중 개별 글 생성 실패"""
        title = self.selected_titles[self.current_title_index]
        self.generation_log_text.append(
            f"[{self.current_title_index + 1}/{self.total_titles}] {title} - 실패: {error_msg}"
        )

        # 실패해도 다음으로 진행
        self.current_title_index += 1
        self.progress_bar.setValue(self.current_title_index)

        api_key = os.getenv("GEMINI_API_KEY") or self.gemini_key_input.text().strip()
        self.generate_next_content(api_key)

    def on_batch_generation_completed(self):
        """일괄 생성 완료"""
        self.generate_content_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        success_count = self.generated_count
        total_count = self.total_titles

        self.generation_log_text.append(f"=== 일괄 생성 완료 ===")
        self.generation_log_text.append(
            f"성공: {success_count}개, 실패: {total_count - success_count}개"
        )
        self.generation_log_text.append("")

        self.update_status(f"일괄 생성 완료: {success_count}/{total_count}개 성공")

        QMessageBox.information(
            self,
            "일괄 생성 완료",
            f"총 {total_count}개 중 {success_count}개의 글이 성공적으로 생성되었습니다!",
        )

    def update_status(self, message):
        """상태 업데이트"""
        self.status_bar.showMessage(message)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = BlogGeneratorTabs()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
