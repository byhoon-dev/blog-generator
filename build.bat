@echo off
echo 블로그 생성기 exe 파일 빌드 시작...
echo.

REM 필요한 패키지 설치
echo 필요한 패키지 설치 중...
pip install -r requirements.txt

echo.
echo exe 파일 생성 중...

REM PyInstaller로 exe 생성
pyinstaller --onefile --windowed --name=BlogGenerator --hidden-import=requests --hidden-import=PyQt5 --hidden-import=PyQt5.QtCore --hidden-import=PyQt5.QtWidgets --hidden-import=PyQt5.QtGui blog_generator.py

echo.
echo 배포용 폴더 생성 중...

REM 배포용 폴더 생성
mkdir BlogGenerator_Distribution 2>nul
copy dist\BlogGenerator.exe BlogGenerator_Distribution\
copy .env BlogGenerator_Distribution\.env.example
copy README.md BlogGenerator_Distribution\
copy .gitignore BlogGenerator_Distribution\

echo.
echo 사용법 파일 생성...
echo # 블로그 글 자동 생성기 사용법 > BlogGenerator_Distribution\사용법.txt
echo. >> BlogGenerator_Distribution\사용법.txt
echo 1. .env.example 파일을 .env로 이름 변경 >> BlogGenerator_Distribution\사용법.txt
echo 2. .env 파일에 API 키 입력 >> BlogGenerator_Distribution\사용법.txt
echo 3. BlogGenerator.exe 실행 >> BlogGenerator_Distribution\사용법.txt

echo.
echo ✅ 빌드 완료!
echo 📁 BlogGenerator_Distribution 폴더를 확인하세요.
echo.
pause