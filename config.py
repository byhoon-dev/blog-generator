"""
배포용 설정 파일
"""

# 배포 모드 설정
DEPLOYMENT_MODE = True

# WebDriver 설정
WEBDRIVER_CONFIG = {
    'use_profile': False,  # 배포시 프로필 사용 안함
    'headless': False,     # 사용자가 로그인해야 하므로 headless 모드 사용 안함
    'timeout': 30,         # 대기 시간
    'implicit_wait': 10,   # 암시적 대기
}

# Chrome 옵션 (배포용)
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-features=TranslateUI",
    "--memory-pressure-off",
]