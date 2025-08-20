import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QListWidget, QGroupBox, QMessageBox, QFileDialog,
    QSplitter
)
from PyQt5.QtCore import Qt
from core.workers import ContentGenerateWorker
from utils.utils import sanitize_filename


class ContentGenerationTab(QWidget):
    """글 생성 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_titles = []
        self.current_title_index = 0
        self.total_titles = 0
        self.generated_count = 0
        self.batch_prompt = ""
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
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
        self.content_titles_list.setStyleSheet("""
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
        """)
        title_select_layout.addWidget(self.content_titles_list)
        
        # 선택 관련 버튼들
        select_btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(self.select_all_titles)
        select_all_btn.setStyleSheet("""
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
        """)
        
        clear_selection_btn = QPushButton("선택 해제")
        clear_selection_btn.clicked.connect(self.clear_title_selection)
        clear_selection_btn.setStyleSheet("""
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
        """)
        
        select_btn_layout.addWidget(select_all_btn)
        select_btn_layout.addWidget(clear_selection_btn)
        select_btn_layout.addStretch()
        
        title_select_layout.addLayout(select_btn_layout)
        
        # 제목 동기화 버튼
        sync_btn = QPushButton("🔄 제목 목록 새로고침")
        sync_btn.clicked.connect(self.sync_titles)
        sync_btn.setStyleSheet("""
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
        """)
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
        self.prompt_input.setPlaceholderText("글 생성 프롬프트를 입력하세요 (비워두면 기본 프롬프트 사용)")
        
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
        self.browse_btn.setStyleSheet("""
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
        """)
        save_layout.addWidget(self.browse_btn)
        
        right_layout.addWidget(save_group)
        
        # 글 생성 버튼
        self.generate_content_btn = QPushButton("📝 선택된 제목들로 일괄 글 생성")
        self.generate_content_btn.clicked.connect(self.generate_multiple_contents)
        self.generate_content_btn.setEnabled(False)
        self.generate_content_btn.setStyleSheet("""
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
        """)
        right_layout.addWidget(self.generate_content_btn)
        
        splitter.addWidget(right_widget)
        layout.addWidget(splitter)
    
    def sync_titles(self):
        """제목 목록 동기화"""
        self.content_titles_list.clear()
        
        # 제목 생성 탭에서 제목 가져오기
        if hasattr(self.parent, 'title_tab'):
            titles = self.parent.title_tab.get_titles()
            for title in titles:
                self.content_titles_list.addItem(title)
        
        if self.content_titles_list.count() > 0:
            self.generate_content_btn.setEnabled(True)
            self.parent.update_status(f"{self.content_titles_list.count()}개 제목을 동기화했습니다.")
        else:
            self.generate_content_btn.setEnabled(False)
            self.parent.update_status("동기화할 제목이 없습니다.")
    
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
            QMessageBox.warning(self, "선택 오류", "글을 생성할 제목을 하나 이상 선택하세요.")
            return
        
        api_key = os.getenv("GEMINI_API_KEY") or self.parent.gemini_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "API 오류", "Gemini API 키를 입력하세요.")
            return
        
        save_path = os.getenv("DEFAULT_SAVE_PATH") or self.save_path_input.text().strip()
        if not save_path:
            QMessageBox.warning(self, "경로 오류", "저장 경로를 선택하세요.")
            return
        
        # 확인 메시지
        reply = QMessageBox.question(
            self, "일괄 생성 확인",
            f"{len(selected_items)}개의 제목으로 글을 생성하시겠습니까?\n\n"
            f"예상 소요 시간: 약 {len(selected_items) * 30}초",
            QMessageBox.Yes | QMessageBox.No
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
        self.parent.progress_bar.setVisible(True)
        self.parent.progress_bar.setRange(0, self.total_titles)
        self.parent.progress_bar.setValue(0)
        
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
        self.content_worker.progress.connect(self.parent.update_status)
        self.content_worker.start()
    
    def on_batch_content_generated(self, title, content):
        """일괄 생성 중 개별 글 생성 완료"""
        try:
            # 파일 저장
            safe_title = sanitize_filename(title)
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
            self.parent.progress_bar.setValue(self.generated_count)
            
            # 로그 추가
            self.generation_log_text.append(
                f"[{self.generated_count}/{self.total_titles}] {title} - 완료"
            )
            
            # 다음 제목으로 진행
            api_key = os.getenv("GEMINI_API_KEY") or self.parent.gemini_key_input.text().strip()
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
        self.parent.progress_bar.setValue(self.current_title_index)
        
        api_key = os.getenv("GEMINI_API_KEY") or self.parent.gemini_key_input.text().strip()
        self.generate_next_content(api_key)
    
    def on_batch_generation_completed(self):
        """일괄 생성 완료"""
        self.generate_content_btn.setEnabled(True)
        self.parent.progress_bar.setVisible(False)
        
        success_count = self.generated_count
        total_count = self.total_titles
        
        self.generation_log_text.append(f"=== 일괄 생성 완료 ===")
        self.generation_log_text.append(f"성공: {success_count}개, 실패: {total_count - success_count}개")
        self.generation_log_text.append("")
        
        self.parent.update_status(f"일괄 생성 완료: {success_count}/{total_count}개 성공")
        
        QMessageBox.information(
            self, "일괄 생성 완료",
            f"총 {total_count}개 중 {success_count}개의 글이 성공적으로 생성되었습니다!"
        )