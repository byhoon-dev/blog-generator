"""
    블로그 생성기 백그라운드 작업 모듈

    이 모듈은 블로그 생성기의 모든 백그라운드 작업을 처리하는 워커 클래스들을 포함합니다.
    NaverSearchWorker: 네이버 블로그 검색
    TitleGenerateWorker: AI 제목 생성
    ContentGenerateWorker: AI 글 생성
    TistoryPublishWorker: 티스토리 발행
"""

import os
import requests
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import google.generativeai as genai
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
import time

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
            params = {"query": self.keyword, "display": 20, "sort": "sim"}

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
    """블로그 제목 생성 워커"""

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
            self.progress.emit("제목 생성 중...")

            # Gemini API 설정
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")

            # 블로그 글 내용 요약
            content_summary = ""
            for i, post in enumerate(self.blog_posts[:10], 1):
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

            response = model.generate_content(prompt)
            content = response.text

            # 제목 추출
            titles = []
            lines = content.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    title = line.split(".", 1)[-1].split("-", 1)[-1].strip()
                    if title:
                        titles.append(title)

            self.progress.emit(f"제목 생성 완료: {len(titles)}개")
            self.titles_generated.emit(titles)

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

            # Gemini API 설정
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")

            full_prompt = f"""
                제목: {self.title}

                {self.prompt}

                위 제목으로 블로그 글을 작성해주세요.
            """
            response = model.generate_content(full_prompt)
            content = response.text

            self.progress.emit("글 생성 완료")
            self.content_generated.emit(self.title, content)

        except Exception as e:
            self.generation_failed.emit(f"글 생성 오류: {str(e)}")


class TistoryPublishWorker(QThread):
    """티스토리 발행 워커 - 브라우저 열고 사용자가 수동 진행"""

    publish_completed = pyqtSignal(str, str) 
    publish_failed = pyqtSignal(str, str)
    progress = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    all_completed = pyqtSignal()

    def __init__(self, tistory_manager, files_to_publish, tab, blog_url="", category=""):
        super().__init__()
        self.tistory_manager = tistory_manager
        self.files_to_publish = files_to_publish
        self.tab = tab
        self.blog_url = blog_url
        self.category = category

    def run(self):
        """발행 실행 - 각 파일마다 브라우저에서 글쓰기 페이지 열기"""
        completed_count = 0
        total_files = len(self.files_to_publish)
        
        for i, file_path in enumerate(self.files_to_publish):
            try:
                self.progress.emit(f"'{os.path.basename(file_path)}' 준비 중...")

                # 파일 읽기
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 제목 추출
                lines = content.split("\n")
                title = ""
                actual_content = content

                for line in lines:
                    if line.startswith("제목:"):
                        title = line.replace("제목:", "").strip()
                        # 제목과 메타데이터 제거하고 실제 내용만 추출
                        content_start = content.find("=" * 50)
                        if content_start != -1:
                            actual_content = content[content_start + 52 :].strip()
                        break

                if not title:
                    title = os.path.splitext(os.path.basename(file_path))[0]

                # 글쓰기 페이지 열기
                success = self.open_write_page(title, actual_content)

                if success:
                    self.publish_completed.emit(
                        os.path.basename(file_path), "브라우저에서 수동 발행 준비 완료"
                    )
                else:
                    self.publish_failed.emit(
                        os.path.basename(file_path), "브라우저 열기 실패"
                    )
                
                # 진행 상황 업데이트
                completed_count += 1
                self.progress_updated.emit(completed_count)

                self.tistory_manager.driver.close()
                self.tistory_manager.driver.switch_to.window(self.tistory_manager.driver.window_handles[0])
                time.sleep(2) 

            except Exception as e:
                self.publish_failed.emit(os.path.basename(file_path), f"오류: {str(e)}")
                # 오류가 발생해도 진행 상황 업데이트
                completed_count += 1
                self.progress_updated.emit(completed_count)
        
        # 모든 파일 처리 완료
        self.all_completed.emit()

    def open_write_page(self, title, content):
        """글쓰기 버튼 클릭하고 자동 작성 시도"""
        try:
            # 글쓰기 버튼 클릭
            if not self.tistory_manager.go_to_write_page():
                return False

            dropdown_btn = self.tistory_manager.driver.find_element(By.CSS_SELECTOR, "#editor-mode-layer-btn-open")
            dropdown_btn.click()

            time.sleep(2)  

            # 마크다운 모드 버튼 클릭 시 알림창 처리를 위한 try-except 블록
            layout_btn = self.tistory_manager.driver.find_element(By.CSS_SELECTOR, "#editor-mode-markdown-text")
            print("🖱️ 마크다운 모드 버튼 클릭")
            layout_btn.click()
            
            # 클릭 후 알림창이 나타날 시간을 충분히 대기
            time.sleep(2)
            
            print("🔍 알림창 확인 및 처리 중...")
            
            # 알림창 확인 및 처리 (클릭 후 나타날 수 있는 알림창)
            for attempt in range(3):  # 최대 3번 시도
                try:
                    print(f"🔍 알림창 확인 시도 {attempt + 1}/3")
                    # WebDriverWait로 알림창 대기 (2초)
                    alert = WebDriverWait(self.tistory_manager.driver, 2).until(EC.alert_is_present())
                    alert_text = alert.text
                    print(f"⚠️ 알림창 발견: '{alert_text}'")
                    alert.accept()
                    print("✅ 알림창 닫기 완료")
                    break
                except TimeoutException:
                    print(f"ℹ️ 시도 {attempt + 1}: 알림창 없음")
                    if attempt == 2:  # 마지막 시도
                        print("ℹ️ 알림창이 없는 것으로 확인, 계속 진행합니다.")
                except Exception as e:
                    print(f"⚠️ 알림창 처리 중 오류 (시도 {attempt + 1}): {type(e).__name__}: {str(e)}")
                    time.sleep(1)  # 1초 대기 후 재시도
            
            time.sleep(2)

            # 클립보드에 내용 복사
            try:
                import pyperclip
                pyperclip.copy(content)
                print("📋 내용이 클립보드에 복사됨")
            except ImportError:
                print("📋 클립보드 복사 기능 없음")

            # 자동 글 작성 시도
            if not self.tistory_manager.write_post(title, content, self.category):
                print("자동 작성 실패")
                return False

            time.sleep(2)
            
            print("🚀 자동 발행 시도 중...")
            # GUI에서 날짜/시간 값 파싱
            publish_date = self.tab.get_publish_date()  # YYYY-MM-DD
            publish_hour = self.tab.get_publish_hour()  # 0-23
            publish_minute = self.tab.get_publish_minute()  # 0-59
            
            if self.tistory_manager.publish_post(publish_date, publish_hour, publish_minute):
                print("🎉 자동 발행 완료!")
            return True
            
        except Exception as e:
            print(f"글쓰기 페이지 열기 오류: {e}")
            return False