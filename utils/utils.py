import os

def load_env_file(file_path=".env"):
    """
    .env 파일을 읽어서 환경변수로 설정
    python-dotenv가 없어도 작동하는 간단한 구현
    """
    env_vars = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
                        os.environ[key] = value
        except Exception as e:
            print(f".env 파일 로드 오류: {e}")
    return env_vars


def sanitize_filename(filename):
    """파일명에서 특수문자 제거"""
    return "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_")).rstrip()