@echo off
echo 블로그 생성기 v2.0 exe 파일 빌드 시작 (안전 모드)...
echo.

REM 기존 빌드 파일 정리
echo 기존 빌드 파일 정리 중...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q BlogGenerator_Distribution 2>nul
del *.pyc 2>nul

REM 필요한 패키지 설치
echo 필요한 패키지 설치 중...
pip install -r requirements.txt

REM Chrome은 시스템에 설치된 버전을 사용합니다

echo.
echo exe 파일 생성 중 (recursion limit 증가)...

REM .spec 파일로 빌드 (recursion limit 설정됨)
pyinstaller BlogGenerator.spec

if not exist "dist\BlogGenerator.exe" (
    echo.
    echo ❌ 빌드 실패! 대안 방법을 시도합니다...
    echo.
    
    REM 대안: 콘솔 모드로 빌드
    pyinstaller --onefile --console --name=BlogGenerator_Console blog_generator.py
    
    if exist "dist\BlogGenerator_Console.exe" (
        echo ✅ 콘솔 모드로 빌드 성공!
        copy dist\BlogGenerator_Console.exe dist\BlogGenerator.exe
    ) else (
        echo ❌ 모든 빌드 방법 실패
        pause
        exit /b 1
    )
)

echo.
echo 배포용 폴더 생성 중...

REM 배포용 폴더 생성
mkdir BlogGenerator_Distribution 2>nul
copy dist\BlogGenerator.exe BlogGenerator_Distribution\
copy .env BlogGenerator_Distribution\.env.example 2>nul
copy README.md BlogGenerator_Distribution\ 2>nul

REM Chrome은 사용자 시스템에 설치된 버전을 사용합니다
echo ℹ️ Chrome 브라우저가 필요합니다 (사용자가 설치해야 함)

echo.
echo 사용법 파일 생성...
echo # 블로그 글 자동 생성기 v2.0 사용법 > BlogGenerator_Distribution\사용법.txt
echo. >> BlogGenerator_Distribution\사용법.txt
echo ## 새로운 기능 >> BlogGenerator_Distribution\사용법.txt
echo - 제목 생성: 키워드 검색 후 AI로 제목 생성 >> BlogGenerator_Distribution\사용법.txt
echo - 글 생성: 선택된 제목들로 일괄 글 생성 >> BlogGenerator_Distribution\사용법.txt
echo - 블로그 발행: 티스토리에 자동 발행 (NEW!) >> BlogGenerator_Distribution\사용법.txt
echo. >> BlogGenerator_Distribution\사용법.txt
echo ## API 키 설정 >> BlogGenerator_Distribution\사용법.txt
echo 1. .env.example 파일을 .env로 이름 변경 >> BlogGenerator_Distribution\사용법.txt
echo 2. .env 파일에 API 키 입력: >> BlogGenerator_Distribution\사용법.txt
echo    NAVER_CLIENT_ID=your_client_id >> BlogGenerator_Distribution\사용법.txt
echo    NAVER_CLIENT_SECRET=your_client_secret >> BlogGenerator_Distribution\사용법.txt
echo    GEMINI_API_KEY=your_gemini_api_key >> BlogGenerator_Distribution\사용법.txt
echo    DEFAULT_SAVE_PATH=C:\your\save\path >> BlogGenerator_Distribution\사용법.txt
echo. >> BlogGenerator_Distribution\사용법.txt
echo ## 사용 순서 >> BlogGenerator_Distribution\사용법.txt
echo 1. [제목 생성] 탭: 키워드 검색 → 제목 생성 >> BlogGenerator_Distribution\사용법.txt
echo 2. [글 생성] 탭: 제목 동기화 → 글 생성 >> BlogGenerator_Distribution\사용법.txt
echo 3. [블로그 발행] 탭: 티스토리 로그인 → 파일 선택 → 발행 >> BlogGenerator_Distribution\사용법.txt
echo. >> BlogGenerator_Distribution\사용법.txt
echo ## Chrome 브라우저 필요 >> BlogGenerator_Distribution\사용법.txt
echo - Chrome 설치: https://www.google.com/chrome/ >> BlogGenerator_Distribution\사용법.txt
echo - Chrome 없으면 기본 브라우저로 자동 전환 >> BlogGenerator_Distribution\사용법.txt
echo. >> BlogGenerator_Distribution\사용법.txt
echo ※ 만약 실행이 안 되면 Python이 설치된 환경에서 >> BlogGenerator_Distribution\사용법.txt
echo   blog_generator.py를 직접 실행하세요. >> BlogGenerator_Distribution\사용법.txt

echo.
echo ✅ 빌드 완료!
echo 📁 BlogGenerator_Distribution 폴더를 확인하세요.
echo.
echo 🚀 새로운 기능:
echo   - 리팩토링된 모듈 구조
echo   - 티스토리 자동 발행 기능
echo   - 향상된 안정성과 에러 처리
echo.
pause