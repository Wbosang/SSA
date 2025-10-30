from typing import List, Dict, Set, Tuple
from .models import Lecture, UserPreferences, ScoringWeights
from .data_loader import load_lectures
from .utils import parse_time_location

def get_time_slots(lecture: Lecture) -> List[Dict[str, int]]:
    return parse_time_location(lecture.raw_time_location)

def do_lectures_conflict(lecture1: Lecture, lecture2: Lecture) -> bool:
    slots1 = get_time_slots(lecture1)
    slots2 = get_time_slots(lecture2)
    slot_set1 = {tuple(slot.items()) for slot in slots1}
    slot_set2 = {tuple(slot.items()) for slot in slots2}
    return not slot_set1.isdisjoint(slot_set2)

def find_combinations(selected_lecture_nos: List[int], max_combinations: int = 10000) -> List[List[Lecture]]:
    """
    선택된 강의 번호 목록을 기반으로 가능한 모든 시간표 조합을 찾습니다.
    시간이 겹치지 않는 모든 부분집합을 찾되, 최대 조합 개수를 제한합니다.
    """
    all_lectures = load_lectures()
    selected_lectures = [lec for lec in all_lectures if lec.no in selected_lecture_nos]

    if not selected_lectures:
        return []

    all_combinations = []
    seen_signatures = set()

    def backtrack(start_index: int, current_combination: List[Lecture]):
        if len(all_combinations) >= max_combinations:
            return

        if current_combination:
            # 사용자가 여러 과목을 선택한 경우, 단일 과목 조합은 추가하지 않음
            if len(selected_lectures) > 1 and len(current_combination) == 1:
                pass
            else:
                combo_signature = frozenset(lec.no for lec in current_combination)
                if combo_signature not in seen_signatures:
                    all_combinations.append(list(current_combination))
                    seen_signatures.add(combo_signature)

        for i in range(start_index, len(selected_lectures)):
            if len(all_combinations) >= max_combinations:
                break

            new_lecture = selected_lectures[i]
            is_compatible = True
            for existing_lecture in current_combination:
                if do_lectures_conflict(existing_lecture, new_lecture):
                    is_compatible = False
                    break
            
            if is_compatible:
                current_combination.append(new_lecture)
                backtrack(i + 1, current_combination)
                current_combination.pop()

    backtrack(0, [])
    return all_combinations

def rank_combinations(
    combinations: List[List[Lecture]], 
    preferences: UserPreferences,
    weights: ScoringWeights
) -> List[List[Lecture]]:
    """
    사용자 선호도와 가중치에 따라 시간표 조합의 순위를 매기고 정렬합니다.
    """
    filtered_combinations = [
        combo for combo in combinations 
        if sum(lec.credits for lec in combo) <= weights.credit_limit
    ]

    day_map_inv = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금'}

    # 1. 사용자 선호도에 따른 하드 필터링 (예: 공강 요일)
    hard_filtered_combinations = []
    if preferences.no_class_days:
        for combo in filtered_combinations:
            present_days = {slot['day'] for lecture in combo for slot in get_time_slots(lecture)}
            is_valid = True
            for day_str in preferences.no_class_days:
                day_num = next((k for k, v in day_map_inv.items() if v == day_str.replace('요일', '').upper()), -1)
                if day_num != -1 and day_num in present_days:
                    is_valid = False
                    break
            if is_valid:
                hard_filtered_combinations.append(combo)
    else:
        hard_filtered_combinations = filtered_combinations

    scored_combinations = []

    for combo in hard_filtered_combinations:
        score = 0
        all_slots = [slot for lecture in combo for slot in get_time_slots(lecture)]
        
        if not combo:
            scored_combinations.append((combo, -9999)) # 점수를 매우 낮게 설정
            continue

        # 기본 점수 계산
        score += sum(lec.credits for lec in combo) * weights.maximize_credits
        
        if all_slots:
            present_days = {slot['day'] for slot in all_slots}
            score += (5 - len(present_days)) * weights.more_empty_days
            
            morning_periods = {1, 2, 3, 4}
            morning_class_count = sum(1 for slot in all_slots if slot['period'] in morning_periods)
            score -= morning_class_count * weights.fewer_morning_classes

            consecutive_lectures = 0
            for day in present_days:
                day_slots = sorted([s['period'] for s in all_slots if s['day'] == day])
                if len(day_slots) > 1:
                    for i in range(len(day_slots) - 1):
                        if day_slots[i+1] == day_slots[i] + 1:
                            consecutive_lectures += 1
            score -= consecutive_lectures * weights.no_consecutive_classes

        # 사용자 선호도 적용
        user_preference_score = 0
        if preferences.no_class_days:
            has_class_on_preferred_empty_day = False
            for day_str in preferences.no_class_days:
                day_num = next((k for k, v in day_map_inv.items() if v == day_str.replace('요일', '').upper()), -1)
                if day_num != -1 and day_num in present_days:
                    has_class_on_preferred_empty_day = True
                    break
            if has_class_on_preferred_empty_day:
                user_preference_score -= 1 # 선호도 위반
            else:
                user_preference_score += 1 # 선호도 충족

        if preferences.prefer_morning and all_slots:
            morning_ratio = morning_class_count / len(all_slots)
            if morning_ratio > 0.5: # 50% 이상이 오전 수업일 경우
                user_preference_score += morning_ratio

        if preferences.prefer_afternoon and all_slots:
            afternoon_periods = {5, 6, 7, 8, 9, 10, 11, 12, 13, 14}
            afternoon_class_count = sum(1 for slot in all_slots if slot['period'] in afternoon_periods)
            afternoon_ratio = afternoon_class_count / len(all_slots)
            if afternoon_ratio > 0.5: # 50% 이상이 오후 수업일 경우
                user_preference_score += afternoon_ratio

        if preferences.no_consecutive_classes and consecutive_lectures > 0:
            user_preference_score -= 1 # 연강 선호도 위반

        score += user_preference_score * weights.user_preference_multiplier

        scored_combinations.append((combo, score))

    scored_combinations.sort(key=lambda x: x[1], reverse=True)
    return [combo for combo, score in scored_combinations]
