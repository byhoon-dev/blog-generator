"""
티스토리 관리 모듈 - 시스템 Chrome 사용 버전
"""

import os
import time
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class TistoryManager:
    """티스토리 관리 클래스"""

    def __init__(self, use_profile=False):  # 배포용 기본값 False
        self.driver = None
        self.is_logged_in = False
        self.use_profile = use_profile

    def setup_driver(self, use_profile=False):  # 배포시 기본값을 False로 변경
        """Chrome 드라이버 설정 - 배포용 최적화"""
        try:
            chrome_options = Options()
            
            # 배포용 안정성 옵션
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            # 메모리 최적화
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            
            # 배포용: 프로필 사용 안함 (일관된 환경)
            # chrome_options.add_argument("--incognito")  # 시크릿 모드로 실행
            
            # 1순위: webdriver-manager로 자동 다운로드 (배포용 최적)
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ Chrome 드라이버 자동 설정 완료")
                return True
            except Exception as e:
                print(f"⚠️ 자동 설정 실패: {e}")
    
            # 2순위: 시스템 Chrome 사용
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✅ 시스템 Chrome 사용 성공")
                return True
            except Exception as e:
                print(f"⚠️ 시스템 Chrome 실패: {e}")
    
            # 실패 시 안내
            print("❌ Chrome 브라우저를 찾을 수 없습니다.")
            print("💡 Chrome 브라우저를 설치해주세요: https://www.google.com/chrome/")
            return False
    
        except Exception as e:
            print(f"드라이버 설정 오류: {e}")
            return False

    def open_tistory_login(self):
        """티스토리 로그인 페이지 열기"""
        try:
            if not self.driver:
                # TODO 배포 시 삭제 시작 - 아래 라인을 if not self.setup_driver(): 로 변경
                if not self.setup_driver(self.use_profile):
                # 배포 시 삭제 끝
                    return False

            # Selenium 드라이버 사용 중인 경우
            self.driver.get("https://www.tistory.com/auth/login")
            return True
        except Exception as e:
            print(f"로그인 페이지 열기 오류: {e}")
            return False

    def go_to_write_page(self):
        # 현재 창 개수 저장
        initial_window_count = len(self.driver.window_handles)

        # 글쓰기 버튼 클릭 해 글 작성 페이지로 이동
        try:
            print("📝 글쓰기 버튼 찾는 중...")
            write_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".wrap_link .link_tab")
            if write_buttons:
                # 첫 번째 버튼이 글쓰기 버튼
                write_button = write_buttons[0]
                print("📝 글쓰기 버튼 발견, 클릭 중...")
                write_button.click()
                time.sleep(3)
            
                print("✅ 글쓰기 페이지로 이동 완료")
            else:
                print("⚠️ 글쓰기 버튼을 찾을 수 없습니다.")
                return False
        except Exception as e:
            print("⚠️ 글쓰기 버튼을 찾을 수 없습니다.")
            return False
        
        # 새창 뜰때까지 대기
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: len(driver.window_handles) > initial_window_count
            )

            new_window = self.driver.window_handles[-1]
            self.driver.switch_to.window(new_window)
        except Exception as e:
            print(f"⚠️ 새창 찾기 실패: {e}")
            return False

        try:
            # 알림창이 있는지 확인
            alert = WebDriverWait(self.driver, 3).until(EC.alert_is_present())
            print("⚠️ 알림창 발견, 닫는 중...")
            # 알림창 텍스트 출력
            alert_text = alert.text
            print(f"알림창 내용: {alert_text}")
            # 알림창 닫기
            alert.dismiss()
            print("✅ 알림창 닫기 완료")
        except Exception as e:
            print("ℹ️ 알림창 없음, 계속 진행합니다.")
            pass

    def write_post(self, title, content, category=""):
        """글 작성 - 자동 입력 시도 후 수동 안내"""
        try:
            print(f"📝 글 작성 시작: {title}")
            try:
                # 제목 입력 시도
                print("🔍 제목 입력 필드 찾는 중...")
                title_input = None
                try:
                    title_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#post-title-inp"))
                    )
                    print("✅ 제목 필드 발견: #post-title-inp")
                except Exception as e:
                    print(f"⚠️ 제목 필드 찾기 실패: {e}")
                    return
                
                if title_input:
                    title_input.clear()
                    title_input.send_keys(title)
                    print("✅ 제목 입력 완료")
                else:
                    print("⚠️ 제목 입력 필드를 찾을 수 없습니다.")
                    return
                
                # 내용 입력 시도
                print("🔍 내용 입력 영역 찾는 중...")
                content_input = None
                try:
                    # iframe 요소 찾기
                    iframe = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#editor-tistory_ifr")) 
                    )

                    # iframe으로 전환
                    self.driver.switch_to.frame(iframe)

                    content_input = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#tinymce p"))
                    )
                    print("✅ 내용 필드 발견: #tinymce p")
                except:
                    print("⚠️ 내용 입력 필드를 찾을 수 없습니다.")
                    return
            
                if content_input:
                    content_input.clear()
                    content_input.send_keys(content)
                    print("✅ 내용 입력 완료")
                    
                    # iframe에서 나오기
                    self.driver.switch_to.default_content()
                else:
                    print("⚠️ 내용 입력 영역을 찾을 수 없습니다.")
                    return
                
                print("🎯 자동 입력 완료! 발행 버튼을 직접 클릭하세요.")
                return True
                
            except Exception as e:
                print(f"⚠️ 자동 입력 실패: {e}")
                return True
                
        except Exception as e:
            print(f"글 작성 오류: {e}")
            return False

    def publish_post(self):
        """글 발행 - 자동 발행 시도"""
        try:
            print("🚀 발행 시도 중...")
            
            # Selenium 드라이버 사용 중인 경우 - 발행 버튼 찾기
            try:
                # 1. 먼저 완료 버튼 클릭 (#publish-layer-btn)
                try:
                    complete_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#publish-layer-btn"))
                    )
                    complete_button.click()
                    print("✅ 완료 버튼 클릭 완료!")
                    time.sleep(2)
                    
                    # 2. 공개 설정 (팝업에서 #open20 라디오 버튼 클릭)
                    try:
                        # 팝업 내 공개 설정 영역 찾기
                        popup_items = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".info_editor.info_editor_type2 .inp_item"))
                        )
                        
                        if len(popup_items) >= 1:
                            # 첫 번째 항목이 공개 설정
                            open_radio = WebDriverWait(popup_items[0], 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "#open20"))
                            )
                            open_radio.click()
                            print("✅ 공개 설정 완료!")
                            
                            # 3. 발행일 설정 (세 번째 항목의 두 번째 버튼 클릭)
                            if len(popup_items) >= 3:
                                date_buttons = popup_items[2].find_elements(By.TAG_NAME, "button")
                                if len(date_buttons) >= 2:
                                    date_buttons[1].click()
                                    print("✅ 발행일 설정 완료!")
                    except Exception as e:
                        print(f"⚠️ 공개 설정 실패: {e}")
                    
                    # 4. 최종 발행 버튼 클릭 (#publish-btn)
                    try:
                        final_publish_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "#publish-btn"))
                        )
                        final_publish_button.click()
                        print("✅ 발행 버튼 클릭 완료!")
                        time.sleep(2)
                        return True
                    except Exception as e:
                        print(f"⚠️ 최종 발행 버튼 클릭 실패: {e}")
                        
                except Exception as e:
                    print(f"⚠️ 완료 버튼 클릭 실패: {e}")
                
                # 기존 방식으로 폴백
                publish_selectors = [
                    "#publish-btn",  # 사용자가 제공한 정확한 ID
                ]
                
                publish_button = None
                try:
                    # XPath로 텍스트 포함 검색
                    xpath = f"//button[contains(text(), '발행')] | //button[contains(text(), '저장')]"
                    publish_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    print("✅ 발행 버튼 발견: XPath 사용")
                except:
                    print("발행에 실패하였습니다.")
                    return
                
                if publish_button:
                    publish_button.click()
                    print("✅ 발행 버튼 클릭 완료!")
                    time.sleep(2)
                    return True
                else:
                    print("⚠️ 발행 버튼을 찾을 수 없습니다. 수동으로 클릭하세요.")
                    return True
                    
            except Exception as e:
                print(f"⚠️ 자동 발행 실패: {e}")
                print("📱 수동으로 발행 버튼을 클릭하세요.")
                return True
                
        except Exception as e:
            print(f"발행 오류: {e}")
            return False

    def close_driver(self):
        """드라이버 종료"""
        if self.driver and self.driver != "default_browser":
            self.driver.quit()
            self.driver = None
            self.is_logged_in = False