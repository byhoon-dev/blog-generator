# 블로그 글 자동 생성기

네이버 검색 API와 OpenAI GPT를 활용하여 키워드 기반으로 블로그 글을 자동 생성하는 프로그램입니다.

## 주요 기능

1. **네이버 블로그 검색**: 특정 키워드로 상위 20개 블로그 글 수집
2. **AI 제목 생성**: 수집된 글을 분석하여 SEO 최적화된 제목 생성
3. **제목 관리**: 생성된 제목 편집/삭제 기능
4. **AI 글 작성**: 선택된 제목으로 완성된 블로그 글 생성
5. **자동 저장**: 생성된 글을 지정된 경로에 자동 저장

## 필요한 API 키

### 1. 네이버 개발자센터 API

- [네이버 개발자센터](https://developers.naver.com/main/) 접속
- 애플리케이션 등록 후 Client ID, Client Secret 발급
- 검색 API 사용 설정

### 2. OpenAI API

- [OpenAI Platform](https://platform.openai.com/) 접속
- API 키 발급 (유료 서비스)

## 설치 및 실행

### 필요한 패키지 설치

```bash
pip install PyQt5 requests
```

### 실행

```bash
python blog_generator.py
```

## 사용 방법

### 1단계: API 설정

**방법 1: .env 파일 사용 (권장)**

```bash
# .env 파일 생성
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_SAVE_PATH=./generated_posts
```

**방법 2: GUI에서 직접 입력**

- 네이버 Client ID, Client Secret 입력
- Gemini API Key 입력
- 설정은 자동으로 저장됩니다

### 2단계: 키워드 검색

- 검색할 키워드 입력
- "검색" 버튼 클릭
- 상위 20개 블로그 글 수집

### 3단계: 제목 생성

- 생성할 제목 개수 설정 (1-20개)
- "제목 생성" 버튼 클릭
- AI가 SEO 최적화된 제목들 생성

### 4단계: 제목 관리

- 생성된 제목 리스트에서 편집/삭제 가능
- 원하는 제목 선택

### 5단계: 글 생성

- 글 생성 프롬프트 설정 (기본값 사용 가능)
- 저장 경로 선택
- "선택된 제목으로 글 생성" 버튼 클릭
- 완성된 글이 텍스트 파일로 저장

## 기본 프롬프트

```
다음 조건에 맞는 블로그 글을 작성해주세요:

1. 2000-3000자 분량
2. SEO 최적화된 내용
3. 독자에게 유용한 정보 제공
4. 자연스러운 한국어 문체
5. 소제목을 활용한 구조화된 글
6. 마지막에 요약 또는 결론 포함

글의 톤앤매너는 친근하고 전문적으로 작성해주세요.
```

## 파일 구조

```
generate_writing/
├── blog_generator.py    # 메인 프로그램
├── README.md           # 사용법 설명
└── settings.json       # API 키 설정 (자동 생성)
```

## 주의사항

1. **API 비용**: OpenAI API는 유료 서비스입니다
2. **네이버 API 제한**: 일일 검색 제한이 있을 수 있습니다
3. **저작권**: 생성된 글의 독창성을 확인하고 사용하세요
4. **품질 검토**: AI 생성 글은 반드시 검토 후 사용하세요

## 트러블슈팅

### API 오류 발생 시

- API 키가 올바른지 확인
- 네이버 API 사용량 제한 확인
- OpenAI API 크레딧 잔액 확인

### 프로그램 실행 오류 시

- Python 버전 확인 (3.6 이상 권장)
- 필요한 패키지 설치 확인
- 방화벽 설정 확인

## EXE 파일 생성

### 자동 빌드 (권장)

```bash
# Windows에서
build.bat

# 또는 Python으로
python build_exe.py
```

### 수동 빌드

```bash
# 필요한 패키지 설치
pip install -r requirements.txt

# exe 파일 생성
pyinstaller --onefile --windowed --name=BlogGenerator blog_generator.py
```

### 배포하기

1. `BlogGenerator_Distribution` 폴더가 생성됩니다
2. 이 폴더를 통째로 다른 사람에게 전달하면 됩니다
3. 받는 사람은 `.env.example`을 `.env`로 이름 변경 후 API 키 입력
4. `BlogGenerator.exe` 실행

## 업데이트 예정

- [ ] 다양한 AI 모델 지원
- [ ] 이미지 생성 기능
- [ ] 티스토리 자동 발행 연동
- [ ] 키워드 분석 기능
- [ ] 글 품질 평가 기능
