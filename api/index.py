from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

# 로컬 모듈 임포트
from .models import Lecture, UserPreferences, ScoringWeights
from .engine import find_combinations, rank_combinations
from .preference_parser import parse_user_preferences
from .data_loader import load_lectures

# FastAPI 앱 생성
# Vercel에서 실행될 때, 이 'app' 변수를 찾습니다.
app = FastAPI()

# CORS 미들웨어 추가
# 프론트엔드 개발 서버(localhost:5173)からの API 요청을 허용합니다.
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 요청 본문을 위한 Pydantic 모델
class TimetableRequest(BaseModel):
    lecture_nos: List[int]
    user_preference_text: str

@app.get("/api/lectures")
def get_all_lectures():
    """
    전체 강의 목록을 반환하는 API 엔드포인트.
    """
    try:
        lectures = load_lectures()
        return [lecture.model_dump() for lecture in lectures]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"강의 목록을 불러오는 중 오류 발생: {e}")

@app.post("/api/generate")
def generate_timetable(request: TimetableRequest):
    """
    과목 ID 리스트와 사용자 선호도 텍스트를 받아,
    최적의 시간표 조합들을 반환하는 API 엔드포인트.
    """
    try:
        # 1. 가능한 모든 시간표 조합 찾기
        combinations = find_combinations(request.lecture_nos)
        
        if not combinations:
            return []

        # 2. 사용자 선호도 분석 (선호도 텍스트가 있을 경우에만)
        preferences = UserPreferences()
        preferences_understood = True
        if request.user_preference_text:
            preferences_dict = parse_user_preferences(request.user_preference_text)
            # 파싱 결과가 비어있거나, 모든 값이 None이면 이해하지 못한 것으로 간주
            if not preferences_dict or all(value is None for value in preferences_dict.values()):
                preferences_understood = False
            else:
                preferences = UserPreferences.model_validate(preferences_dict)

        # 3. 기본 가중치로 조합 순위 매기기
        weights = ScoringWeights()
        ranked_combinations = rank_combinations(combinations, preferences, weights)
        
        # 4. 결과를 JSON으로 변환하기 쉬운 딕셔너리 리스트로 변환
        result_json = [[lecture.model_dump() for lecture in combo] for combo in ranked_combinations]
        
        return {
            "timetables": result_json,
            "preferences_understood": preferences_understood
        }

    except ValueError as e:
        # API 키가 없는 경우 등의 에러 처리
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 기타 예기치 않은 에러 처리
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# 로컬 테스트를 위한 루트 엔드포인트
@app.get("/")
def read_root():
    return {"message": "SSA Timetable Generator API"}
