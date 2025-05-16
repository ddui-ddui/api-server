# Ddui Ddui 🐕
강아지를 위한 날씨 앱.  
키우는 개 사이즈와 민감군에 대한 정보를 활용하여 산책에 대한 수치를 산출하여 사용자에게 시각적으로 전달.

## Stack
### Language
- Python(3.11.5)
### Library
- FastAPI(+ Swagger)
- uvicorn
- dotenv

## API
한국 공공 데이터의 오픈 API를 사용함.
### 미세먼지 데이터
에어코리아

### 날씨 데이터
기상청

### 설치
#### 라이브러리 관련파일 갱신
./generate-reqs.sh
또는
./generate-reqs.bat
#### 라이브러리 설치
```bash
pip install -r requirements.txt
pip install -r dev-requirements.txt
```
