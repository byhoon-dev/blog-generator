"""
PyInstaller를 사용해서 exe 파일을 생성하는 스크립트
"""
import os
import subprocess
import sys

def build_exe():
    """exe 파일 빌드"""
    print("🚀 블로그 생성기 exe 파일 빌드 시작...")
    
    # PyInstaller 설치 확인
    try:
        import PyInstaller
        print("✅ PyInstaller가 설치되어 있습니다.")
    except ImportError:
        print("❌ PyInstaller가 설치되어 있지 않습니다.")
        print("설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller 설치 완료")
    
    # 빌드 명령어
    cmd = [
        "pyinstaller",
        "--onefile",  # 단일 exe 파일로 생성
        "--windowed",  # 콘솔 창 숨김 (GUI 앱이므로)
        "--name=BlogGenerator",  # exe 파일명
        "--icon=icon.ico",  # 아이콘 (있으면)
        "--add-data=.env;.",  # .env 파일 포함
        "--hidden-import=requests",
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtGui",
        "blog_generator.py"
    ]
    
    # 아이콘 파일이 없으면 제거
    if not os.path.exists("icon.ico"):
        cmd.remove("--icon=icon.ico")
    
    try:
        print("🔨 exe 파일 생성 중...")
        subprocess.run(cmd, check=True)
        print("✅ exe 파일 생성 완료!")
        print("📁 dist/BlogGenerator.exe 파일을 확인하세요.")
        
        # 배포용 폴더 생성
        create_distribution_folder()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        return False
    
    return True

def create_distribution_folder():
    """배포용 폴더 생성"""
    print("\n📦 배포용 폴더 생성 중...")
    
    dist_folder = "BlogGenerator_Distribution"
    
    # 폴더 생성
    os.makedirs(dist_folder, exist_ok=True)
    
    # 필요한 파일들 복사
    import shutil
    
    files_to_copy = [
        ("dist/BlogGenerator.exe", "BlogGenerator.exe"),
        (".env", ".env.example"),  # 예제 파일로 복사
        ("README.md", "README.md"),
        (".gitignore", ".gitignore")
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            dst_path = os.path.join(dist_folder, dst)
            shutil.copy2(src, dst_path)
            print(f"✅ {src} → {dst_path}")
    
    # 사용법 파일 생성
    create_usage_guide(dist_folder)
    
    print(f"\n🎉 배포용 폴더 '{dist_folder}' 생성 완료!")
    print("이 폴더를 통째로 다른 사람에게 주면 됩니다.")

def create_usage_guide(folder):
    """사용법 가이드 생성"""
    guide_content = """# 블로그 글 자동 생성기 사용법

## 🚀 시작하기

### 1단계: API 키 설정
`.env.example` 파일을 `.env`로 이름을 바꾸고 다음 정보를 입력하세요:

```
NAVER_CLIENT_ID=여기에_네이버_클라이언트_ID_입력
NAVER_CLIENT_SECRET=여기에_네이버_클라이언트_시크릿_입력
GEMINI_API_KEY=여기에_구글_제미나이_API_키_입력
DEFAULT_SAVE_PATH=./generated_posts
```

### 2단계: 프로그램 실행
`BlogGenerator.exe` 파일을 더블클릭하여 실행하세요.

### 3단계: 사용하기
1. **제목 생성 탭**: 키워드 검색 → 제목 생성
2. **글 생성 탭**: 제목 선택 → 글 생성

## 📋 API 키 발급 방법

### 네이버 검색 API
1. https://developers.naver.com/main/ 접속
2. 애플리케이션 등록
3. 검색 API 사용 설정
4. Client ID, Client Secret 복사

### Google Gemini API
1. https://aistudio.google.com/ 접속
2. API 키 생성
3. API 키 복사

## ❓ 문제 해결

### 프로그램이 실행되지 않는 경우
- Windows Defender나 백신 프로그램에서 차단했을 수 있습니다
- 예외 처리하거나 신뢰할 수 있는 프로그램으로 추가하세요

### API 오류가 발생하는 경우
- `.env` 파일의 API 키가 올바른지 확인하세요
- 네이버 API 할당량을 확인하세요
- Gemini API 키가 활성화되어 있는지 확인하세요

## 📞 지원
문제가 있으면 개발자에게 문의하세요.
"""
    
    with open(os.path.join(folder, "사용법.txt"), "w", encoding="utf-8") as f:
        f.write(guide_content)

if __name__ == "__main__":
    build_exe()