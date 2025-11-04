from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

class Lecture(BaseModel):
    """
    하나의 강의 정보를 담는 데이터 모델
    CSV 파일의 각 행에 해당합니다.
    """
    no: int = Field(alias='NO.')
    course_id: str = Field(alias='교과번호')
    class_section: str = Field(alias='분반')
    course_name: str = Field(alias='교과목명')
    grade: str = Field(alias='학년')
    credits: int = Field(alias='학점')
    department: str = Field(alias='학부(과)')
    course_type: str = Field(alias='교과구분')
    detailed_area: str = Field(alias='세부영역')
    raw_time_location: Optional[str] = Field(alias='수업시간(강의실)')

class ScoringWeights(BaseModel):
    """
    시간표 점수 계산에 사용될 가중치 모델
    """
    maximize_credits: int = 50
    credit_limit: int = 23
    fewer_morning_classes: int = 5
    more_empty_days: int = 10
    no_consecutive_classes: int = 2
    user_preference_multiplier: int = 100 # 사용자가 명시한 선호도에 대한 가중치 배수

class UserPreferences(BaseModel):
    """
    사용자의 자연어 선호 조건을 구조화된 데이터로 담는 모델
    LLM이 이 스키마에 맞춰 정보를 추출합니다.
    """
    no_class_days: Optional[List[str]] = Field(
        default=None, 
        description="수업이 없기를 바라는 요일 목록 (예: ['금', '월'])"
    )
    avoid_morning: Optional[bool] = Field(
        default=None, 
        description="오전 수업(1-4교시)을 피하고 싶은지 여부. 사용자가 '오전' 또는 '아침' 수업을 피하고 싶다고 명시적으로 언급할 때만 True로 설정합니다."
    )
    avoid_afternoon: Optional[bool] = Field(
        default=None, 
        description="오후 수업(5교시 이후)을 피하고 싶은지 여부. 사용자가 '오후' 또는 '저녁' 수업을 피하고 싶다고 명시적으로 언급할 때만 True로 설정합니다."
    )
    prefer_morning: Optional[bool] = Field(
        default=None, 
        description="오전 수업(1-4교시)을 선호하는지 여부. 사용자가 '오전' 또는 '아침' 수업을 명시적으로 언급할 때만 True로 설정합니다."
    )
    prefer_afternoon: Optional[bool] = Field(
        default=None, 
        description="오후 수업(5교시 이후)을 선호하는지 여부. 사용자가 '오후' 또는 '저녁' 수업을 명시적으로 언급할 때만 True로 설정합니다."
    )
    no_consecutive_classes: Optional[bool] = Field(
        default=None,
        description="연강(연속된 수업)을 피하고 싶은지 여부. 사용자가 '연강', '우주공강' 등을 명시적으로 언급할 때 True로 설정합니다."
    )
    target_credits: Optional[int] = Field(
        default=None,
        description="사용자가 원하는 목표 학점. 사용자가 '20학점'처럼 특정 학점을 언급할 때 해당 숫자를 추출합니다."
    )