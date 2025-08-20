import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QSpinBox, QGroupBox, QMessageBox,
    QSplitter, QInputDialog
)
from PyQt5.QtCore import Qt
from core.workers import NaverSearchWorker, TitleGenerateWorker


class TitleGenerationTab(QWidget):
    """제목 생성 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.blog_posts = []
        self.generated_titles = []
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 키워드 검색
        search_group = QGroupBox("키워드 검색")
        search_layout = QHBoxLayout(search_group)
        
        search_layout.addWidget(QLabel("키워드:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("검색할 키워드를 입력하세요")
        search_layout.addWidget(self.keyword_input)
        
        self.search_btn = QPushButton("🔍 검색")
        self.search_btn.clicked.connect(self.search_blogs)
        self.search_btn.setStyleSheet("""
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
        """)
        search_layout.addWidget(self.search_btn)
        
        layout.addWidget(search_group)
        
        # 수평 분할
        splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 검색 결과
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        search_result_group = QGroupBox("검색된 블로그 글 (제목 위에 마우스를 올리면 상세 정보)")
        search_result_layout = QVBoxLayout(search_result_group)
        
        self.search_result_list = QListWidget()
        self.search_result_list.setStyleSheet("""
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
        """)
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
        self.generate_titles_btn.setStyleSheet("""
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
        """)
        count_layout.addWidget(self.generate_titles_btn)
        
        title_gen_layout.addLayout(count_layout)
        right_layout.addWidget(title_gen_group)
        
        # 생성된 제목 리스트
        titles_group = QGroupBox("생성된 제목")
        titles_layout = QVBoxLayout(titles_group)
        
        self.titles_list = QListWidget()
        self.titles_list.setStyleSheet("""
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
        """)
        titles_layout.addWidget(self.titles_list)
        
        # 제목 편집 버튼들
        title_btn_layout = QHBoxLayout()
        self.edit_title_btn = QPushButton("✏️ 편집")
        self.edit_title_btn.clicked.connect(self.edit_selected_title)
        self.edit_title_btn.setStyleSheet("""
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
        """)
        
        self.delete_title_btn = QPushButton("🗑️ 삭제")
        self.delete_title_btn.clicked.connect(self.delete_selected_title)
        self.delete_title_btn.setStyleSheet("""
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
        """)
        
        title_btn_layout.addWidget(self.edit_title_btn)
        title_btn_layout.addWidget(self.delete_title_btn)
        title_btn_layout.addStretch()
        
        titles_layout.addLayout(title_btn_layout)
        right_layout.addWidget(titles_group)
        
        splitter.addWidget(right_widget)
        layout.addWidget(splitter)
    
    def search_blogs(self):
        """네이버 블로그 검색"""
        keyword = self.keyword_input.text().strip()
        
        client_id = os.getenv("NAVER_CLIENT_ID") or self.parent.naver_id_input.text().strip()
        client_secret = os.getenv("NAVER_CLIENT_SECRET") or self.parent.naver_secret_input.text().strip()
        
        if not keyword:
            QMessageBox.warning(self, "입력 오류", "키워드를 입력하세요.")
            return
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "API 오류", "네이버 API 정보를 입력하거나 .env 파일에 설정하세요.")
            return
        
        self.search_btn.setEnabled(False)
        self.parent.progress_bar.setVisible(True)
        self.parent.progress_bar.setRange(0, 0)
        
        # 검색 워커 시작
        self.search_worker = NaverSearchWorker(keyword, client_id, client_secret)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_failed.connect(self.on_search_failed)
        self.search_worker.progress.connect(self.parent.update_status)
        self.search_worker.start()
    
    def on_search_completed(self, blog_posts):
        """검색 완료 처리"""
        self.blog_posts = blog_posts
        self.search_btn.setEnabled(True)
        self.generate_titles_btn.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        
        # 검색 결과를 리스트로 표시
        self.search_result_list.clear()
        
        for i, post in enumerate(blog_posts, 1):
            item_text = f"{i:2d}. {post['title']}"
            item = QListWidgetItem(item_text)
            tooltip = f"블로거: {post['bloggername']}\n날짜: {post['postdate']}\n내용: {post['description'][:200]}...\n링크: {post['link']}"
            item.setToolTip(tooltip)
            self.search_result_list.addItem(item)
        
        self.parent.update_status(f"검색 완료: {len(blog_posts)}개 블로그 글 발견")
    
    def on_search_failed(self, error_msg):
        """검색 실패 처리"""
        self.search_btn.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        self.parent.update_status("검색 실패")
        QMessageBox.critical(self, "검색 실패", error_msg)
    
    def generate_titles(self):
        """제목 생성"""
        if not self.blog_posts:
            QMessageBox.warning(self, "데이터 없음", "먼저 키워드 검색을 실행하세요.")
            return
        
        api_key = os.getenv("GEMINI_API_KEY") or self.parent.gemini_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "API 오류", "Gemini API 키를 입력하거나 .env 파일에 설정하세요.")
            return
        
        count = self.title_count_spin.value()
        
        self.generate_titles_btn.setEnabled(False)
        self.parent.progress_bar.setVisible(True)
        self.parent.progress_bar.setRange(0, 0)
        
        # 제목 생성 워커 시작
        self.title_worker = TitleGenerateWorker(self.blog_posts, count, api_key)
        self.title_worker.titles_generated.connect(self.on_titles_generated)
        self.title_worker.generation_failed.connect(self.on_title_generation_failed)
        self.title_worker.progress.connect(self.parent.update_status)
        self.title_worker.start()
    
    def on_titles_generated(self, titles):
        """제목 생성 완료 처리"""
        self.generated_titles.extend(titles)
        
        # 리스트에 제목 추가
        for title in titles:
            self.titles_list.addItem(title)
        
        self.generate_titles_btn.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        
        self.parent.update_status(f"제목 생성 완료: {len(titles)}개")
    
    def on_title_generation_failed(self, error_msg):
        """제목 생성 실패 처리"""
        self.generate_titles_btn.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        self.parent.update_status("제목 생성 실패")
        QMessageBox.critical(self, "제목 생성 실패", error_msg)
    
    def edit_selected_title(self):
        """선택된 제목 편집"""
        current_item = self.titles_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "선택 오류", "편집할 제목을 선택하세요.")
            return
        
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
    
    def get_titles(self):
        """생성된 제목 목록 반환"""
        titles = []
        for i in range(self.titles_list.count()):
            titles.append(self.titles_list.item(i).text())
        return titles