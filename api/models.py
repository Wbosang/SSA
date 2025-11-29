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
        description="수업이 없는 공강 요일을 한국어로 반환합니다. 사용자가 '금공강', '금요일 수업 빼줘', '주 4일제 하고 싶어(이 경우 하루를 임의로 선택하거나 문맥상 가능한 요일)' 등 다양한 표현으로 공강을 원할 때 요일을 추출합니다. 출력은 반드시 ['월', '화', '수', '목', '금'] 중 하나여야 합니다. 예: '금요일 공강 원해요' -> ['금']"
    )
    avoid_periods: Optional[List[int]] = Field(
        default=None,
        description="피하고 싶은 특정 교시를 정수 리스트로 반환합니다. 사용자가 '1교시 싫어', '1교시는 제외해줘', '9교시 수업 빼줘' 등 특정 교시를 명시적으로 언급할 때 해당 교시 번호를 추출합니다. 예: '1교시 안 듣고 싶어' -> [1], '1, 9교시 제외' -> [1, 9]"
    )
    avoid_morning: Optional[bool] = Field(
        default=None, 
        description="오전 수업(1-4교시)을 피하고 싶은지 여부. 사용자가 '오전 수업 싫어', '아침 수업 없애줘' 등 명시적으로 언급할 때만 True로 설정합니다."
    )
    avoid_afternoon: Optional[bool] = Field(
        default=None, 
        description="오후 수업(5교시 이후)을 피하고 싶은지 여부. 사용자가 '오후 수업 싫어', '저녁 수업 없애줘' 등 명시적으로 언급할 때만 True로 설정합니다."
    )
    prefer_morning: Optional[bool] = Field(
        default=None, 
        description="오전 수업(1-4교시)을 선호하는지 여부. 사용자가 '오전' 또는 '아침' 수업을 선호한다고 명시적으로 언급할 때만 True로 설정합니다."
    )
    prefer_afternoon: Optional[bool] = Field(
        default=None, 
        description="오후 수업(5교시 이후)을 선호하는지 여부. 사용자가 '오후' 또는 '저녁' 수업을 선호한다고 명시적으로 언급할 때만 True로 설정합니다."
    )
    no_consecutive_classes: Optional[bool] = Field(
        default=None,
        description="연강(연속된 수업)을 피하고 싶은지 여부. 사용자가 '연강 싫어', '연강 없게', '우주공강' 등을 명시적으로 언급할 때 True로 설정합니다."
    )
    target_credits: Optional[int] = Field(
        default=None,
        description="사용자가 원하는 목표 학점. 사용자가 '20학점'처럼 특정 학점을 언급할 때 해당 숫자를 추출합니다."
    )
    must_include_lectures: Optional[List[int]] = Field(
        default=None,
        description="반드시 포함해야 하는 강의의 번호(NO.) 목록. 사용자가 '컴퓨터 구조는 꼭 넣어줘' 와 같이 특정 과목을 지정하면, 해당 과목의 모든 분반(강의 번호)을 추출합니다. 또는 '12345 강의는 필수로' 와 같이 강의 번호를 직접 언급할 때 해당 번호를 추출합니다."
    )
    prefer_empty_lunch: Optional[bool] = Field(
        default=None,
        description="점심시간(4교시 또는 5교시)을 비우고 싶은지 여부. '점심시간 확보', '밥 먹을 시간' 등의 언급이 있을 때 True로 설정합니다."
    )