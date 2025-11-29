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
    각 교과목 그룹에서 하나씩 선택하거나, 선택하지 않는 경우를 모두 고려하여
    시간이 겹치지 않는 모든 조합을 찾습니다.
    """
    all_lectures = load_lectures()
    selected_lectures = [lec for lec in all_lectures if lec.no in selected_lecture_nos]

    if not selected_lectures:
        return []

    course_groups: Dict[str, List[Lecture]] = {}
    for lec in selected_lectures:
        if lec.course_id not in course_groups:
            course_groups[lec.course_id] = []
        course_groups[lec.course_id].append(lec)

    grouped_courses = list(course_groups.values())
    all_combinations = []
    seen_signatures = set()

    def backtrack(group_index: int, current_combination: List[Lecture]):
        # 최대 조합 개수 도달 시, 더 이상의 재귀를 막기 위해 함수 맨 위에서 확인
        if len(all_combinations) >= max_combinations:
            return

        # 모든 그룹을 다 고려한 경우, 현재 조합을 최종 결과에 추가
        if group_index == len(grouped_courses):
            if current_combination:
                combo_signature = frozenset(lec.no for lec in current_combination)
                if combo_signature not in seen_signatures:
                    all_combinations.append(list(current_combination))
                    seen_signatures.add(combo_signature)
            return

        # --- 재귀 호출 (순서 변경) --- #

        # 1. 현재 그룹의 각 과목(분반)을 포함하는 경우를 먼저 시도 (학점 높은 조합 우선 탐색)
        for lecture_to_add in grouped_courses[group_index]:
            # 루프 중간에도 최대 조합 개수를 확인하여 불필요한 계산 방지
            if len(all_combinations) >= max_combinations:
                break

            is_compatible = True
            for existing_lecture in current_combination:
                if do_lectures_conflict(existing_lecture, lecture_to_add):
                    is_compatible = False
                    break
            
            if is_compatible:
                current_combination.append(lecture_to_add)
                backtrack(group_index + 1, current_combination)
                current_combination.pop()
        
        # 2. 현재 그룹의 과목을 포함하지 않고 다음 그룹으로 넘어가는 경우
        backtrack(group_index + 1, current_combination)

    backtrack(0, [])
    return all_combinations


def find_combinations_with_preferences(
    selected_lecture_nos: List[int], 
    preferences: UserPreferences,
    max_combinations: int = 10000
) -> List[List[Lecture]]:
    """
    사용자 선호도를 조합 생성 과정에 직접 반영하여 시간표 조합을 찾습니다.
    불필요한 탐색을 줄여(pruning) 더 나은 결과를 찾을 확률을 높입니다.
    """
    all_lectures = load_lectures()
    selected_lectures = [lec for lec in all_lectures if lec.no in selected_lecture_nos]

    if not selected_lectures:
        return []

    course_groups: Dict[str, List[Lecture]] = {}
    for lec in selected_lectures:
        if lec.course_id not in course_groups:
            course_groups[lec.course_id] = []
        course_groups[lec.course_id].append(lec)

    grouped_courses = list(course_groups.values())
    all_combinations = []
    seen_signatures = set()
    
    day_map_inv = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금'}
    
    # 선호도에서 공강 희망 요일 숫자 목록 미리 만들기
    no_class_day_nums = []
    if preferences.no_class_days:
        for day_str in preferences.no_class_days:
            day_num = next((k for k, v in day_map_inv.items() if v == day_str.replace('요일', '').upper()), -1)
            if day_num != -1:
                no_class_day_nums.append(day_num)

    def backtrack(group_index: int, current_combination: List[Lecture]):
        if len(all_combinations) >= max_combinations:
            return

        if group_index == len(grouped_courses):
            if current_combination:
                combo_signature = frozenset(lec.no for lec in current_combination)
                if combo_signature not in seen_signatures:
                    all_combinations.append(list(current_combination))
                    seen_signatures.add(combo_signature)
            return

        for lecture_to_add in grouped_courses[group_index]:
            if len(all_combinations) >= max_combinations:
                break

            # --- 사용자 선호도에 따른 탐색 가지치기(Pruning) ---
            lecture_slots = get_time_slots(lecture_to_add)
            
            # 1. 오전/오후 선호도 체크
            if preferences.avoid_morning and any(slot['period'] <= 4 for slot in lecture_slots):
                continue # 오전 수업 회피 시, 이 강의는 건너뜀
            if preferences.avoid_afternoon and any(slot['period'] >= 5 for slot in lecture_slots):
                continue # 오후 수업 회피 시, 이 강의는 건너뜀
            if preferences.prefer_morning and any(slot['period'] >= 5 for slot in lecture_slots):
                continue # 오전 수업 선호 시, 오후 수업이 포함된 이 강의는 건너뜀
            if preferences.prefer_afternoon and any(slot['period'] <= 4 for slot in lecture_slots):
                continue # 오후 수업 선호 시, 오전 수업이 포함된 이 강의는 건너뜀

            # 2. 공강 선호도 체크
            if no_class_day_nums:
                is_on_off_day = any(slot['day'] in no_class_day_nums for slot in lecture_slots)
                if is_on_off_day:
                    continue # 공강 희망 요일에 수업이 있으면 이 강의는 건너뜀
            # --- 가지치기 끝 ---

            # 시간 충돌 체크
            is_compatible = True
            for existing_lecture in current_combination:
                if do_lectures_conflict(existing_lecture, lecture_to_add):
                    is_compatible = False
                    break
            
            if is_compatible:
                current_combination.append(lecture_to_add)
                backtrack(group_index + 1, current_combination)
                current_combination.pop()
        
        backtrack(group_index + 1, current_combination)

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

    # 사용자 선호도에 따른 하드 필터링
    current_combos = filtered_combinations

    # 1. 공강 요일 필터링
    if preferences.no_class_days:
        temp_combos = []
        for combo in current_combos:
            present_days = {slot['day'] for lecture in combo for slot in get_time_slots(lecture)}
            is_valid = True
            for day_str in preferences.no_class_days:
                day_num = next((k for k, v in day_map_inv.items() if v == day_str.replace('요일', '').upper()), -1)
                if day_num != -1 and day_num in present_days:
                    is_valid = False
                    break
            if is_valid:
                temp_combos.append(combo)
        current_combos = temp_combos

    # 1-1. 특정 교시 회피 필터링 (New)
    if preferences.avoid_periods:
        temp_combos = []
        for combo in current_combos:
            has_avoided_period = False
            for lecture in combo:
                for slot in get_time_slots(lecture):
                    if slot['period'] in preferences.avoid_periods:
                        has_avoided_period = True
                        break
                if has_avoided_period:
                    break
            
            if not has_avoided_period:
                temp_combos.append(combo)
        current_combos = temp_combos

    # 1-1. 특정 교시 회피 필터링 (New)
    if preferences.avoid_periods:
        temp_combos = []
        for combo in current_combos:
            has_avoided_period = False
            for lecture in combo:
                for slot in get_time_slots(lecture):
                    if slot['period'] in preferences.avoid_periods:
                        has_avoided_period = True
                        break
                if has_avoided_period:
                    break
            
            if not has_avoided_period:
                temp_combos.append(combo)
        current_combos = temp_combos

    # 2. 오전/오후 수업 회피 필터링
    if preferences.avoid_morning:
        temp_combos = []
        for combo in current_combos:
            has_morning_class = any(slot['period'] in {1, 2, 3, 4} for lecture in combo for slot in get_time_slots(lecture))
            if not has_morning_class:
                temp_combos.append(combo)
        current_combos = temp_combos

    if preferences.avoid_afternoon:
        temp_combos = []
        for combo in current_combos:
            has_afternoon_class = any(slot['period'] >= 5 for lecture in combo for slot in get_time_slots(lecture))
            if not has_afternoon_class:
                temp_combos.append(combo)
        current_combos = temp_combos
    
    # 2-1. 오전/오후 수업 선호 필터링 (강화)
    if preferences.prefer_morning:
        temp_combos = []
        for combo in current_combos:
            has_afternoon_class = any(slot['period'] >= 5 for lecture in combo for slot in get_time_slots(lecture))
            if not has_afternoon_class:
                temp_combos.append(combo)
        current_combos = temp_combos

    if preferences.prefer_afternoon:
        temp_combos = []
        for combo in current_combos:
            has_morning_class = any(slot['period'] <= 4 for lecture in combo for slot in get_time_slots(lecture))
            if not has_morning_class:
                temp_combos.append(combo)
        current_combos = temp_combos

    # 3. 연강 회피는 점수 계산에서 페널티를 부여하는 방식으로 처리합니다.

    scored_combinations = []

    for combo in current_combos:
        score = 0
        
        if not combo:
            scored_combinations.append((combo, -9999)) # 점수를 매우 낮게 설정
            continue

        # 학점 점수 계산 (목표 학점 우선)
        total_credits = sum(lec.credits for lec in combo)
        if preferences.target_credits is not None:
            credit_diff = abs(total_credits - preferences.target_credits)
            score += (1 / (1 + credit_diff)) * 10 * weights.user_preference_multiplier 
        else:
            score += total_credits * weights.maximize_credits
        
        # 강의 시간과 관련된 점수 계산을 위한 슬롯 정보
        all_slots_with_id = [
            {'day': slot['day'], 'period': slot['period'], 'id': lecture.no}
            for lecture in combo
            for slot in get_time_slots(lecture)
        ]
        
        present_days = {slot['day'] for slot in all_slots_with_id}

        if all_slots_with_id:
            score += (5 - len(present_days)) * weights.more_empty_days
            
            morning_periods = {1, 2, 3, 4}
            morning_class_count = sum(1 for slot in all_slots_with_id if slot['period'] in morning_periods)
            score -= morning_class_count * weights.fewer_morning_classes

        # 사용자 선호도 적용
        user_preference_score = 0
        # 1. 공강 선호도
        if preferences.no_class_days:
            has_class_on_preferred_empty_day = False
            for day_str in preferences.no_class_days:
                day_num = next((k for k, v in day_map_inv.items() if v == day_str.replace('요일', '').upper()), -1)
                if day_num != -1 and day_num in present_days:
                    has_class_on_preferred_empty_day = True
                    break
            if has_class_on_preferred_empty_day:
                user_preference_score -= 5
            else:
                user_preference_score += 1

        # 2. 연강 회피 선호도 (정의 수정 및 페널티 강화)
        if preferences.no_consecutive_classes:
            consecutive_count = 0
            for day in present_days:
                day_slots_with_id = sorted(
                    [s for s in all_slots_with_id if s['day'] == day], 
                    key=lambda x: x['period']
                )
                
                if len(day_slots_with_id) > 1:
                    for i in range(len(day_slots_with_id) - 1):
                        slot1 = day_slots_with_id[i]
                        slot2 = day_slots_with_id[i+1]
                        
                        # 다른 강의가 연속으로 붙어있는 경우 (연강)
                        if slot2['period'] == slot1['period'] + 1 and slot2['id'] != slot1['id']:
                            consecutive_count += 1
            
            if consecutive_count > 0:
                user_preference_score -= consecutive_count * 10

        # 3. 점심시간 확보 선호도
        if preferences.prefer_empty_lunch:
            for day in present_days:
                day_periods = {s['period'] for s in all_slots_with_id if s['day'] == day}
                # 4교시와 5교시가 모두 수업인 경우 페널티
                if 4 in day_periods and 5 in day_periods:
                    user_preference_score -= 10 # 큰 페널티

        score += user_preference_score * weights.user_preference_multiplier

        scored_combinations.append((combo, score))

    scored_combinations.sort(key=lambda x: x[1], reverse=True)
    return [combo for combo, score in scored_combinations]
