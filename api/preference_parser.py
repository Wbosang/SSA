import os
import json
from typing import Dict
from .models import UserPreferences

# LangChain 관련 라이브러리 임포트
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_extraction_chain_pydantic

# .env 파일 로드를 위한 라이브러리
from dotenv import load_dotenv

# 파일 기반 캐시 설정
CACHE_FILE = 'preference_cache.json'

def load_cache() -> Dict[str, Dict]:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {}

def save_cache(cache: Dict[str, Dict]):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except IOError:
        pass # 파일 쓰기 실패 시 무시

preference_cache = load_cache()

def parse_user_preferences(user_input: str) -> Dict:
    """
    사용자의 자연어 입력을 LangChain과 LLM을 사용하여 분석하고,
    UserPreferences Pydantic 모델에 정의된 구조로 변환합니다.
    결과는 파일 캐시에 저장됩니다.
    """
    if user_input in preference_cache:
        return preference_cache[user_input]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경 변수를 찾을 수 없습니다. .env 파일을 확인하세요.")

    llm = ChatGoogleGenerativeAI(model="gemini-pro-latest", google_api_key=api_key, convert_system_message_to_human=True)
    structured_llm = llm.with_structured_output(UserPreferences)

    result = structured_llm.invoke(user_input)
    
    # Pydantic 모델을 딕셔너리로 변환
    result_dict = result.model_dump()

    preference_cache[user_input] = result_dict
    save_cache(preference_cache)

    return result_dict

# --- 테스트를 위한 실행 블록 (핵심 원칙 4) ---
if __name__ == '__main__':
    print("--- 자연어 선호도 분석 모듈 테스트 시작 ---")
    
    # 테스트할 자연어 입력 목록
    test_inputs = [
        "금요일은 수업 없게 해줘. 그리고 오후 수업이 좋아.",
        "아침 수업만 넣어줘",
        "월공강 만들어주세요.",
        "화요일은 빼고, 오전보다는 오후가 나을 것 같아"
    ]

    for text in test_inputs:
        print(f"\n--- 입력: \"{text}\" ---")
        try:
            preferences = parse_user_preferences(text)
            print(f"추출된 선호도: {preferences.model_dump()}")
        except Exception as e:
            print(f"오류 발생: {e}")

    print("\n--- 자연어 선호도 분석 모듈 테스트 종료 ---")
