import os
import glob
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QDateTimeEdit,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QProgressBar,
    QComboBox,
    QCheckBox,
    QHeaderView,
    QSizePolicy,
)

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime
from core.tistory_manager import TistoryManager
from core.workers import TistoryPublishWorker

class BlogPublishTab(QWidget):
    """블로그 발행 탭"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.tistory_manager = TistoryManager()
        self.files_to_publish = []
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 티스토리 로그인과 폴더 선택을 같은 줄에 배치 (1:1 비율, 높이 축소)
        top_section_layout = QHBoxLayout()
        
        # 로그인 그룹 (왼쪽 50%)
        login_group = QGroupBox("티스토리")
        login_group.setMaximumHeight(100)  # 높이 제한
        login_layout = QHBoxLayout(login_group)  # 수평 레이아웃으로 변경
        login_layout.setContentsMargins(10, 10, 10, 10)  # 여백 축소
        
        self.login_btn = QPushButton("🔐 로그인")
        self.login_btn.clicked.connect(self.open_tistory_login)
        self.login_btn.setMaximumWidth(250)  # 버튼 너비 제한
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35;
                color: white;
                border: none;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e55a2b;
            }
        """)
        
        # 일괄 발행 버튼 추가
        self.batch_publish_btn = QPushButton("🚀 파일 일괄발행")
        self.batch_publish_btn.clicked.connect(self.publish_all_files)
        self.batch_publish_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        
        login_layout.addWidget(self.login_btn)
        login_layout.addWidget(self.batch_publish_btn)
        
        # 폴더 선택 그룹 (오른쪽 50%)
        folder_group = QGroupBox("발행할 글 폴더 선택")
        folder_group.setMaximumHeight(100)  # 높이 제한
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setContentsMargins(10, 10, 10, 10)  # 여백 축소

        folder_select_layout = QHBoxLayout()
        self.folder_path_input = QLineEdit()
        folder_select_layout.addWidget(self.folder_path_input)

        self.browse_folder_btn = QPushButton("📁 선택")
        self.browse_folder_btn.clicked.connect(self.browse_folder)
        self.browse_folder_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #607d8b;
                color: white;
                border: none;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #455a64;
            }
        """
        )
        folder_select_layout.addWidget(self.browse_folder_btn)

        folder_layout.addLayout(folder_select_layout)

        # 1:1 비율로 추가
        top_section_layout.addWidget(login_group, 1)  # stretch factor 1
        top_section_layout.addWidget(folder_group, 1)  # stretch factor 1
        
        layout.addLayout(top_section_layout)

        # 파일 목록 (전체 화면)
        files_group = QGroupBox("발행할 파일 목록")
        files_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 수평, 수직 확장
        files_layout = QVBoxLayout(files_group)

        # 테이블 위젯 - 파일명, 예약시간, 상태, 삭제 버튼
        self.files_table = QTableWidget(0, 4)
        self.files_table.setHorizontalHeaderLabels(["파일명", "예약 시간", "상태", "삭제"])
        
        # 컬럼 너비 설정
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 파일명 (남은 공간 모두 차지)
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # 예약시간
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # 상태
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # 삭제 버튼
        
        self.files_table.setColumnWidth(1, 250)  # 예약시간 컬럼 (더 넓게 수정)
        self.files_table.setColumnWidth(2, 80)   # 상태 컬럼
        self.files_table.setColumnWidth(3, 60)   # 삭제 버튼 컬럼
        
        self.files_table.setStyleSheet("""
            QTableWidget {
                background: white;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)
        
        # 테이블이 전체 화면 너비를 사용하도록 설정
        self.files_table.horizontalHeader().setStretchLastSection(False)
        self.files_table.setMinimumWidth(800)  # 최소 너비 설정

        # 테이블이 가능한 모든 공간을 사용하도록 설정
        self.files_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        files_layout.addWidget(self.files_table, 1)  # stretch factor 1로 설정

        # 파일 관리 버튼들
        file_btn_layout = QHBoxLayout()

        # 일괄 시간 설정
        self.set_batch_time_btn = QPushButton("일괄 시간 설정")
        self.set_batch_time_btn.clicked.connect(self.set_batch_time)
        self.set_batch_time_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """
        )

        file_btn_layout.addWidget(self.set_batch_time_btn)
        file_btn_layout.addStretch()

        files_layout.addLayout(file_btn_layout)
        layout.addWidget(files_group, 1)  # stretch factor 1로 설정하여 남은 공간 모두 차지
        
        # 로그 텍스트 영역 (숨김 처리)
        self.publish_log_text = QTextEdit()
        self.publish_log_text.setVisible(False)  # 로그 영역 숨김

    def open_tistory_login(self):
        """티스토리 로그인 페이지 열기"""
        try:
            if self.tistory_manager.open_tistory_login():
                QMessageBox.information(self, "로그인", "🌐 티스토리 로그인 페이지가 열렸습니다.\n👤 브라우저에서 직접 로그인을 완료한 후 발행 버튼을 클릭하세요.")
            else:
                QMessageBox.critical(self, "오류", "브라우저를 열 수 없습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"로그인 페이지 열기 실패: {str(e)}")

    def browse_folder(self):
        """폴더 선택"""
        folder = QFileDialog.getExistingDirectory(self, "발행할 글 폴더 선택")
        if folder:
            self.folder_path_input.setText(folder)
            self.refresh_file_list()

    def refresh_file_list(self):
        """파일 목록 새로고침"""
        folder_path = self.folder_path_input.text().strip()
        if not folder_path or not os.path.exists(folder_path):
            self.files_table.setRowCount(0)
            return

        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        self.files_table.setRowCount(len(txt_files))

        # 현재 시간 기준 5분 후부터 시작
        current_time = QDateTime.currentDateTime()
        start_time = current_time.addSecs(5 * 60)  # 5분 후

        for row, file_path in enumerate(txt_files):
            filename = os.path.basename(file_path)

            # 파일명
            item = QTableWidgetItem(filename)
            item.setData(Qt.UserRole, file_path)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 읽기 전용

            self.files_table.setItem(row, 0, item)

            # 예약 시간 (기본값: 현재 시각 + 5분 + row*5분)
            dt_edit = QDateTimeEdit()
            dt_edit.setCalendarPopup(True)
            dt_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
            dt_edit.setMinimumWidth(160)  # 최소 너비 설정

            dt_edit.setStyleSheet("""
                QDateTimeEdit {
                    padding: 5px;
                    font-size: 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                QDateTimeEdit:focus {
                    border: 2px solid #2196f3;
                }
            """)
            
            # 각 파일마다 5분씩 간격을 두어 기본 시간 설정 (시작은 현재 시간 + 5분부터)
            scheduled_time = start_time.addSecs(row * 5 * 60)
            dt_edit.setDateTime(scheduled_time)
            
            self.files_table.setCellWidget(row, 1, dt_edit)

            # 상태
            status_item = QTableWidgetItem("대기")
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.files_table.setItem(row, 2, status_item)
            
            # 삭제 버튼
            delete_btn = QPushButton("🗑️")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 5px;
                    font-weight: bold;
                    border-radius: 4px;
                    min-width: 30px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_file_row(r))
            self.files_table.setCellWidget(row, 3, delete_btn)

        if hasattr(self.parent, 'update_status'):
            self.parent.update_status(f"📁 {len(txt_files)}개의 텍스트 파일을 발견했습니다.")

    def delete_file_row(self, row):
        """특정 행 삭제"""
        if row >= self.files_table.rowCount():
            return
            
        file_item = self.files_table.item(row, 0)
        if file_item:
            filename = file_item.text()
            reply = QMessageBox.question(
                self,
                "파일 삭제 확인",
                f"'{filename}' 파일을 목록에서 제거하시겠습니까?\n(실제 파일은 삭제되지 않습니다)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.files_table.removeRow(row)
                
                if hasattr(self.parent, 'update_status'):
                    self.parent.update_status(f"🗑️ {filename} 파일이 목록에서 제거되었습니다.")



    def set_batch_time(self):
        """모든 파일들에 일괄 시간 설정"""
        # 기본 간격 5분 사용
        interval_minutes = 5

        total_rows = self.files_table.rowCount()
        if total_rows == 0:
            QMessageBox.warning(self, "파일 없음", "시간을 설정할 파일이 없습니다.")
            return

        # 시작 시간 설정 다이얼로그
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("일괄 시간 설정")
        dialog.setModal(True)
        dialog_layout = QVBoxLayout(dialog)
        
        dialog_layout.addWidget(QLabel("시작 시간을 설정하세요:"))
        start_time_edit = QDateTimeEdit()
        start_time_edit.setCalendarPopup(True)
        start_time_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        
        # 현재 시간 + 5분을 기본값으로 설정
        current_time = QDateTime.currentDateTime()
        start_time = current_time.addSecs(5 * 60)  # 5분 후
        start_time_edit.setDateTime(start_time)
        
        dialog_layout.addWidget(start_time_edit)
        
        dialog_layout.addWidget(QLabel(f"전체 {total_rows}개 파일에 {interval_minutes}분 간격으로 설정됩니다."))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            base_time = start_time_edit.dateTime()
            
            for row in range(total_rows):
                dt_edit = self.files_table.cellWidget(row, 1)
                if dt_edit:
                    scheduled_time = base_time.addSecs(row * interval_minutes * 60)
                    dt_edit.setDateTime(scheduled_time)
            
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status(f"⏰ {total_rows}개 파일의 시간이 일괄 설정되었습니다.")






        
    def publish_all_files(self):
        """모든 파일 일괄 발행"""
        files_to_publish = []
        past_time_files = []
        current_time = QDateTime.currentDateTime()
        
        # 모든 파일의 경로와 예약 시간 수집
        for row in range(self.files_table.rowCount()):
            file_item = self.files_table.item(row, 0)
            dt_edit = self.files_table.cellWidget(row, 1)
            
            if file_item and dt_edit:
                file_path = file_item.data(Qt.UserRole)
                filename = file_item.text()
                schedule_time = dt_edit.dateTime()
                
                # 현재 시간보다 이전인지 확인
                if schedule_time < current_time:
                    past_time_files.append(filename)
                else:
                    files_to_publish.append((file_path, schedule_time.toPyDateTime()))
        
        # 과거 시간이 설정된 파일이 있으면 경고
        if past_time_files:
            msg = "다음 파일들의 예약 시간이 현재 시간보다 이전입니다:\n\n"
            for filename in past_time_files:
                msg += f"- {filename}\n"
            msg += "\n발행을 계속하시려면 예약 시간을 수정하세요."
            
            QMessageBox.warning(self, "예약 시간 오류", msg)
            return
        
        if not files_to_publish:
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("발행할 파일이 없습니다.")
            return
        
        # 파일 상태를 '준비중'으로 변경
        for row in range(self.files_table.rowCount()):
            status_item = self.files_table.item(row, 2)
            if status_item:
                status_item.setText("준비중")

        if hasattr(self.parent, 'update_status'):
            self.parent.update_status(f"🚀 {len(files_to_publish)}개 파일 발행 시작...")
            
        # 발행 작업 시작
        self.start_publish_worker(files_to_publish)

    def start_publish_worker(self, files_to_publish):
        """티스토리 발행 워커 시작"""
        # 프로그레스바 설정
        if hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.setVisible(True)
            self.parent.progress_bar.setRange(0, len(files_to_publish))
            self.parent.progress_bar.setValue(0)
        
        # 파일 경로만 추출
        file_paths = [file_path for file_path, _ in files_to_publish]
        
        # 티스토리 발행 워커 시작
        self.publish_worker = TistoryPublishWorker(self.tistory_manager, file_paths)
        self.publish_worker.progress_updated.connect(lambda val: self.parent.progress_bar.setValue(val) if hasattr(self.parent, 'progress_bar') else None)
        self.publish_worker.publish_completed.connect(self.on_publish_completed)
        self.publish_worker.publish_failed.connect(self.on_publish_failed)
        self.publish_worker.progress.connect(lambda msg: self.parent.update_status(msg) if hasattr(self.parent, 'update_status') else None)
        self.publish_worker.all_completed.connect(self.on_publish_finished)
        self.publish_worker.start()
        


    def update_file_status(self, filename, status):
        """파일 상태 업데이트"""
        for row in range(self.files_table.rowCount()):
            file_item = self.files_table.item(row, 0)
            if file_item and file_item.text() == filename:
                status_item = self.files_table.item(row, 2)
                if status_item:
                    status_item.setText(status)
                break

    def on_publish_completed(self, filename, message):
        """파일 발행 완료 처리"""
        self.update_file_status(filename, "완료")
        if hasattr(self.parent, 'update_status'):
            self.parent.update_status(f"✅ {filename} 파일 발행 완료: {message}")
        if hasattr(self.parent, 'progress_bar'):
            current_value = self.parent.progress_bar.value()
            self.parent.progress_bar.setValue(current_value + 1)

    def on_publish_failed(self, filename, error):
        """파일 발행 실패 처리"""
        self.update_file_status(filename, "실패")
        if hasattr(self.parent, 'update_status'):
            self.parent.update_status(f"❌ {filename} 파일 발행 실패: {error}")
        if hasattr(self.parent, 'progress_bar'):
            current_value = self.parent.progress_bar.value()
            self.parent.progress_bar.setValue(current_value + 1)

    def on_publish_finished(self):
        """모든 파일 발행 완료 처리"""
        if hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.setVisible(False)
        
        if hasattr(self.parent, 'update_status'):
            self.parent.update_status("모든 파일 발행이 완료되었습니다.")
            
        QMessageBox.information(
            self,
            "발행 완료",
            "모든 파일이 발행되었습니다.\n티스토리 관리자 페이지에서 확인하세요."
        )