<template>
  <v-row dense>
    <v-col cols="12" md="2">
      <v-autocomplete
        v-model="selectedDepartment"
        :items="departments"
        label="학부(과) (입력하여 검색)"
        dense
        variant="underlined"
        clearable
      ></v-autocomplete>
    </v-col>
    <v-col cols="12" md="2">
      <v-select
        v-model="selectedCourseType"
        :items="courseTypes"
        label="교과구분"
        dense
        variant="underlined"
        clearable
      ></v-select>
    </v-col>
    <v-col cols="12" md="2">
      <v-select
        v-model="selectedDetailedArea"
        :items="detailedAreas"
        label="세부영역"
        dense
        variant="underlined"
        clearable
      ></v-select>
    </v-col>
    <v-col cols="12" md="1">
      <v-select
        v-model="selectedGrade"
        :items="grades"
        label="학년"
        dense
        variant="underlined"
        multiple
        chips
        closable-chips
        clearable
      >
        <template v-slot:item="{ props, item }">
          <v-list-item v-bind="props" :title="item.raw"></v-list-item>
        </template>
      </v-select>
    </v-col>
    <v-col cols="12" md="2">
      <v-select
        v-model="selectedDay"
        :items="days"
        label="요일"
        dense
        variant="underlined"
        multiple
        chips
        closable-chips
        clearable
      >
        <template v-slot:item="{ props, item }">
          <v-list-item v-bind="props" :title="item.raw"></v-list-item>
        </template>
      </v-select>
    </v-col>
    <v-col cols="12" md="2">
      <v-select
        v-model="selectedPeriod"
        :items="periods"
        label="교시"
        dense
        variant="underlined"
        multiple
        chips
        closable-chips
        clearable
      >
        <template v-slot:item="{ props, item }">
          <v-list-item v-bind="props" :title="item.raw"></v-list-item>
        </template>
      </v-select>
    </v-col>
  </v-row>

  <v-autocomplete
    v-model="selectedLectures"
    :items="autocompleteItems"
    :item-title="lecture => `${lecture.course_name} (${lecture.course_id}) - ${lecture.class_section}분반`"
    item-value="no"
    chips
    closable-chips
    multiple
    label="원하는 강의(분반)를 선택하세요 (과목명 또는 교과번호로 검색)"
    variant="underlined"
    :menu-props="{ maxHeight: '400px' }"
  >
    <template v-slot:chip="{ props, item }">
      <v-chip v-bind="props" :text="`${item.raw.course_name} (${item.raw.class_section}분반)`"></v-chip>
    </template>

    <template v-slot:item="{ props, item }">
      <v-list-item
        v-bind="props"
        :title="`${item.raw.course_name} (${item.raw.class_section}분반)`"
        :subtitle="`${item.raw.department} / ${item.raw.grade}학년 / ${item.raw.course_id} / ${item.raw.credits}학점 / ${item.raw.raw_time_location || '시간정보없음'}`"
      ></v-list-item>
    </template>
  </v-autocomplete>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

// v-model을 위한 props와 emit 정의
const props = defineProps({
  modelValue: Array
})
const emit = defineEmits(['update:modelValue'])

// v-autocomplete는 내부적으로 값을 업데이트하므로, computed를 사용해 양방향 바인딩을 구현
const selectedLectures = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// --- 필터링 관련 상태 ---
const allLectures = ref([])
const selectedDepartment = ref(null)
const selectedCourseType = ref(null)
const selectedDetailedArea = ref(null)
const selectedGrade = ref([])
const selectedDay = ref([])
const selectedPeriod = ref([])

const days = ['월', '화', '수', '목', '금']
const periods = ['전체', ...Array.from({ length: 10 }, (_, i) => `${i + 1}교시`)]

// --- 선택된 필터 값 정렬을 위한 Watchers ---
watch(selectedGrade, (newValue) => {
  // nextTick을 사용하거나, 값을 직접 재할당하기보다 sort()를 사용하여 내부 순서만 변경
  newValue.sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
});

watch(selectedDay, (newValue) => {
  newValue.sort((a, b) => days.indexOf(a) - days.indexOf(b));
});

watch(selectedPeriod, (newValue) => {
  newValue.sort((a, b) => {
    if (a === '전체') return -1;
    if (b === '전체') return 1;
    return parseInt(a, 10) - parseInt(b, 10);
  });
});


// --- API 호출 ---
onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/lectures');
    allLectures.value = response.data;
    console.log(`성공: ${allLectures.value.length}개의 분반을 모두 로드했습니다.`);
  } catch (error) {
    console.error("강의 목록을 불러오는 중 오류 발생:", error);
    alert("전체 강의 목록을 불러오는 데 실패했습니다.");
  }
});

// --- 필터링 로직 ---

// 각 필터의 선택지를 동적으로 생성하는 계산된 속성
const departments = computed(() => [...new Set(allLectures.value.map(l => l.department))].sort());
const courseTypes = computed(() => [...new Set(allLectures.value.map(l => l.course_type))].sort());
const detailedAreas = computed(() => [...new Set(allLectures.value.map(l => l.detailed_area))].sort());
const grades = computed(() => {
  const gradeSet = new Set(allLectures.value.map(l => l.grade));
  // '34'와 같은 복합 학년은 선택지에서 제외
  gradeSet.delete('34');
  return Array.from(gradeSet).sort((a, b) => {
    const numA = parseInt(a, 10);
    const numB = parseInt(b, 10);
    return numA - numB;
  });
});

// 모든 필터를 적용하여 최종 강의 목록을 반환하는 계산된 속성
const filteredLectures = computed(() => {
  let lectures = allLectures.value;

  // 1. 학부(과) 필터
  if (selectedDepartment.value) {
    lectures = lectures.filter(l => l.department === selectedDepartment.value);
  }

  // 2. 교과구분 필터
  if (selectedCourseType.value) {
    lectures = lectures.filter(l => l.course_type === selectedCourseType.value);
  }

  // 3. 세부영역 필터
  if (selectedDetailedArea.value) {
    lectures = lectures.filter(l => l.detailed_area === selectedDetailedArea.value);
  }

  // 4. 학년 필터 ( 다중 선택 가능, '3' 또는 '4' 선택 시 '34' 포함 )
  if (selectedGrade.value && selectedGrade.value.length > 0) {
    lectures = lectures.filter(l => {
      // 어떤 학년 조건이라도 만족하는지 확인
      return selectedGrade.value.some(grade => {
        if (grade === '3') return l.grade === '3' || l.grade === '34';
        if (grade === '4') return l.grade === '4' || l.grade === '34';
        return l.grade === grade;
      });
    });
  }

  // 5. 요일 필터 (다중 선택 가능)
  if (selectedDay.value && selectedDay.value.length > 0) {
    lectures = lectures.filter(l => 
      l.raw_time_location && selectedDay.value.some(day => l.raw_time_location.includes(day))
    );
  }

  // 6. 교시 필터 (다중 선택 가능)
  if (selectedPeriod.value && selectedPeriod.value.length > 0 && !selectedPeriod.value.includes('전체')) {
    lectures = lectures.filter(l => {
      if (!l.raw_time_location) return false;
      // 선택된 교시 중 하나라도 강의 시간에 포함되는지 확인
      return selectedPeriod.value.some(period => {
        const periodNum = parseInt(period, 10);
        const matches = l.raw_time_location.matchAll(/\[([\d,]+)\]/g);
        for (const match of matches) {
          const periodsInBracket = match[1].split(',').map(p => parseInt(p, 10));
          if (periodsInBracket.includes(periodNum)) {
            return true;
          }
        }
        return false;
      });
    });
  }

  return lectures;
});

// 필터링된 목록과 현재 선택된 강의 목록을 합쳐, 선택된 항목이 사라지지 않도록 보장
const autocompleteItems = computed(() => {
  // 현재 선택된 강의의 전체 객체 정보
  const selectedLectureObjects = allLectures.value.filter(l => 
    selectedLectures.value.includes(l.no)
  );

  // Map을 사용하여 중복을 제거하면서 두 리스트를 합침
  const combined = new Map();
  
  // 필터링된 강의를 먼저 추가
  filteredLectures.value.forEach(l => combined.set(l.no, l));
  
  // 그 다음, 선택된 강의를 추가 (필터링된 리스트에 없더라도 포함됨)
  selectedLectureObjects.forEach(l => combined.set(l.no, l));
  
  return Array.from(combined.values());
});

</script>