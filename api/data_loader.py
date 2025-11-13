import csv
import os
from typing import List
from .models import Lecture

# 이 파일의 절대 경로를 기준으로 data 폴더의 경로를 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.join(current_dir, '..', 'data', '시간표.csv')

def load_lectures(file_path: str = DEFAULT_CSV_PATH) -> List[Lecture]:
    """
    CSV 파일에서 강의 목록을 로드하여 Lecture 객체 리스트로 변환합니다.

    :param file_path: 강의 데이터 CSV 파일 경로
    :return: Lecture 객체 리스트
    """
    lectures = []
    try:
        # utf-8-sig 인코딩으로 BOM(Byte Order Mark)이 있는 파일도 처리
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # 일부 숫자 필드가 비어있을 경우를 대비하여 기본값 0으로 처리
                    if not row.get('학점'):
                        row['학점'] = 0
                    
                    # Pydantic 모델을 사용하여 데이터 유효성 검사 및 객체 생성
                    lectures.append(Lecture(**row))
                except Exception as e:
                    # 특정 행에서 데이터 변환 오류 발생 시, 해당 행의 정보와 함께 오류를 출력
                    print(f"데이터 변환 오류 (행: {reader.line_num}): {row}")
                    print(f"오류 내용: {e}")

    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    
    return lectures

# --- 테스트를 위한 실행 블록 (핵심 원칙 4) ---
if __name__ == '__main__':
    """
    이 스크립트가 직접 실행될 때, load_lectures 함수를 테스트합니다.
    """
    print("--- 데이터 로더 테스트 시작 ---")
    
    # 데이터 로드 함수 실행
    # data_loader.py는 api 폴더 안에 있으므로, data 폴더에 접근하려면 상위 폴더(../)로 가야 합니다.
    lectures_list = load_lectures(file_path='../data/시간표.csv')
    
    # 테스트 결과 출력
    if lectures_list:
        print(f"성공: 총 {len(lectures_list)}개의 강의를 로드했습니다.")
        print("\n--- 첫 3개 강의 정보 ---")
        for lecture in lectures_list[:3]:
            # Pydantic V2에서는 model_dump_json에 ensure_ascii가 없습니다.
            # model_dump()를 사용하여 dict로 변환 후 출력합니다.
            print(lecture.model_dump())
    else:
        print("실패: 강의 정보를 로드하지 못했습니다.")
        
    print("\n--- 데이터 로더 테스트 종료 ---")