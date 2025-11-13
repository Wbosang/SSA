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

  <div class="d-flex align-center">
    <v-autocomplete
      class="flex-grow-1"
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
    <v-btn @click="toggleSelectAllFiltered" class="ml-4" size="small" variant="tonal">모두 선택</v-btn>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const SELECT_ALL_LIMIT = 100;

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

  // 시간 정보가 없는 강의는 필터링
  lectures = lectures.filter(l => l.raw_time_location);

  if (selectedDepartment.value) {
    lectures = lectures.filter(l => l.department === selectedDepartment.value);
  }
  if (selectedCourseType.value) {
    lectures = lectures.filter(l => l.course_type === selectedCourseType.value);
  }
  if (selectedDetailedArea.value) {
    lectures = lectures.filter(l => l.detailed_area === selectedDetailedArea.value);
  }
  if (selectedGrade.value && selectedGrade.value.length > 0) {
    lectures = lectures.filter(l => {
      return selectedGrade.value.some(grade => {
        if (grade === '3') return l.grade === '3' || l.grade === '34';
        if (grade === '4') return l.grade === '4' || l.grade === '34';
        return l.grade === grade;
      });
    });
  }
  if (selectedDay.value && selectedDay.value.length > 0) {
    lectures = lectures.filter(l => 
      l.raw_time_location && selectedDay.value.some(day => l.raw_time_location.includes(day))
    );
  }
  if (selectedPeriod.value && selectedPeriod.value.length > 0 && !selectedPeriod.value.includes('전체')) {
    lectures = lectures.filter(l => {
      if (!l.raw_time_location) return false;
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
  const selectedLectureObjects = allLectures.value.filter(l => 
    selectedLectures.value.includes(l.no)
  );
  const combined = new Map();
  filteredLectures.value.forEach(l => combined.set(l.no, l));
  selectedLectureObjects.forEach(l => combined.set(l.no, l));
  return Array.from(combined.values());
});

// --- 모두 선택/해제 로직 ---
const areAllFilteredSelected = computed(() => {
  const filteredIds = new Set(filteredLectures.value.map(l => l.no));
  if (filteredIds.size === 0) return false;
  return [...filteredIds].every(id => selectedLectures.value.includes(id));
});

function toggleSelectAllFiltered() {
  let filteredIds = filteredLectures.value.map(l => l.no);
  const selectedIds = new Set(selectedLectures.value);

  if (areAllFilteredSelected.value) {
    // 모두 해제
    filteredIds.forEach(id => selectedIds.delete(id));
  } else {
    // 모두 선택
    if (filteredIds.length > SELECT_ALL_LIMIT) {
      alert(`필터링된 강의가 ${SELECT_ALL_LIMIT}개를 초과하여, 처음 ${SELECT_ALL_LIMIT}개의 강의만 선택됩니다.`);
      filteredIds = filteredIds.slice(0, SELECT_ALL_LIMIT); // Limit to the first 100
    }
    filteredIds.forEach(id => selectedIds.add(id));
  }
  emit('update:modelValue', [...selectedIds]);
}

</script>