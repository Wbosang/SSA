import re
from typing import List, Dict, Optional

def parse_time_location(raw_str: Optional[str]) -> List[Dict[str, int]]:
    """
    '월[1,2]/37-나602,수[8,9]/39-B126'와 같은 원본 시간 문자열을
    파싱하여 요일과 교시를 나타내는 딕셔너리 리스트로 변환합니다.
    
    :param raw_str: 원본 시간 문자열
    :return: [{'day': 0, 'period': 1}, {'day': 0, 'period': 2}, ...] 형태의 리스트
             (day: 0=월, 1=화, ..., 4=금)
    """
    if not raw_str:
        return []

    day_map = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4}
    parsed_slots = []
    
    # 정규표현식을 사용하여 "월[1,2]"와 같은 패턴을 모두 찾음
    pattern = r'([월화수목금])\[([\d,]+)\]'
    matches = re.findall(pattern, raw_str)
    
    for match in matches:
        day_char, periods_str = match
        day_num = day_map.get(day_char)
        
        if day_num is None:
            continue
            
        periods = [int(p) for p in periods_str.split(',')]
        
        for period in periods:
            parsed_slots.append({'day': day_num, 'period': period})
            
    return parsed_slots

def normalize_day_format(days: List[str]) -> List[str]:
    """
    LLM이 반환한 다양한 형태의 요일 문자열을 표준 형식('월', '화', ...)으로 변환합니다.
    예: ['FRIDAY', '화요일', '수'] -> ['금', '화', '수']
    """
    if not days:
        return []

    day_map = {
        'mon': '월', '월': '월',
        'tue': '화', '화': '화',
        'wed': '수', '수': '수',
        'thu': '목', '목': '목',
        'fri': '금', '금': '금',
    }
    
    normalized_days = set()
    for day in days:
        day_lower = day.lower()
        for key, value in day_map.items():
            if key in day_lower:
                normalized_days.add(value)
                break
    
    return sorted(list(normalized_days), key=lambda d: ['월', '화', '수', '목', '금'].index(d))

def preprocess_preference_text(text: str) -> str:
    """
    LLM이 더 잘 이해하도록 사용자 입력 텍스트를 전처리합니다.
    예: "월 공강" -> "월요일 공강"
    """
    # 요일 약어와 전체 이름 매핑
    day_map = {
        '월': '월요일',
        '화': '화요일',
        '수': '수요일',
        '목': '목요일',
        '금': '금요일',
    }

    # 정규표현식을 사용하여 "(요일) 공강" 패턴을 찾고 변환
    for short, full in day_map.items():
        # "월 공강", "월공강" 같은 패턴을 찾되, "월요일"은 건드리지 않도록
        # (?!요일)은 "요일"이라는 문자열이 뒤따라오지 않는 경우에만 매치 (Negative Lookahead)
        pattern = re.compile(f'{short}(?!요일)\s*공강')
        text = pattern.sub(f'{full} 공강', text)

    return text

# --- 테스트를 위한 실행 블록 (핵심 원칙 4) ---
if __name__ == '__main__':
    print("--- 시간 파싱 유틸리티 테스트 시작 ---")
    
    test_cases = [
        "목[7,8,9]/01-208",
        "월[1,2]/37-나602,수[8,9]/39-B126",
        "화[6,7,8,9]/19-213,14",
        "",
        None,
        "시간정보없음"
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n--- 테스트 케이스 {i+1} ---")
        print(f"입력: {case}")
        result = parse_time_location(case)
        print(f"결과: {result}")

    print("\n--- 시간 파싱 유틸리티 테스트 종료 ---")