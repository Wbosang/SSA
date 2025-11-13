from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

# 로컬 모듈 임포트
from .models import Lecture, UserPreferences, ScoringWeights
from .engine import find_combinations, rank_combinations, find_combinations_with_preferences
from .preference_parser import parse_user_preferences, clear_preference_cache
from .data_loader import load_lectures
from .utils import normalize_day_format, preprocess_preference_text

# FastAPI 앱 생성
# Vercel에서 실행될 때, 이 'app' 변수를 찾습니다.
app = FastAPI()

# CORS 미들웨어 추가
# 프론트엔드 개발 서버(localhost:5173) API 요청을 허용합니다.
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
    1차 시도 후 결과가 없으면, 선호도를 반영하여 2차 시도를 합니다.
    """
    try:
        # 1. 사용자 선호도 분석
        preferences = UserPreferences()
        preferences_understood = True
        if request.user_preference_text:
            processed_text = preprocess_preference_text(request.user_preference_text)
            preferences_dict = parse_user_preferences(processed_text)
            if not preferences_dict or all(value is None for value in preferences_dict.values()):
                preferences_understood = False
            else:
                preferences = UserPreferences.model_validate(preferences_dict)
                if preferences.no_class_days:
                    preferences.no_class_days = normalize_day_format(preferences.no_class_days)

        # 2. 1차 시도: 선호도를 고려하지 않고 조합 생성 후 필터링
        weights = ScoringWeights()
        combinations = find_combinations(request.lecture_nos)
        ranked_combinations = rank_combinations(combinations, preferences, weights)
        
        # 3. 1차 시도 실패 시 2차 시도
        if not ranked_combinations:
            # 선호도를 조합 생성에 직접 반영하여 다시 시도
            combinations_v2 = find_combinations_with_preferences(request.lecture_nos, preferences)
            # 다시 순위 매기기
            ranked_combinations = rank_combinations(combinations_v2, preferences, weights)

        # 4. 결과를 JSON으로 변환
        result_json = [[lecture.model_dump() for lecture in combo] for combo in ranked_combinations]
        
        return {
            "timetables": result_json,
            "preferences_understood": preferences_understood
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/api/clear-cache")
def clear_cache_endpoint():
    """
    선호도 분석 캐시를 삭제하는 API 엔드포인트.
    """
    try:
        clear_preference_cache()
        return {"message": "Preference cache cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {e}")

# 로컬 테스트를 위한 루트 엔드포인트
@app.get("/")
def read_root():
    return {"message": "SSA Timetable Generator API"}
