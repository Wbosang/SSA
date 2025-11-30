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
    <v-col cols="12" md="2">
      <v-select
        v-model="selectedGrade"
        :items="grades"
        label="학년"
        dense
        variant="underlined"
        multiple
        clearable
      >
        <template v-slot:selection="{ item, index }">
          <v-chip v-if="index === 0">
            <span>{{ item.title }}</span>
          </v-chip>
          <span
            v-if="index === 1"
            class="text-grey text-caption align-self-center"
          >
            (+{{ selectedGrade.length - 1 }}개)
          </span>
        </template>
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
        clearable
      >
        <template v-slot:selection="{ item, index }">
          <v-chip v-if="index === 0">
            <span>{{ item.title }}</span>
          </v-chip>
          <span
            v-if="index === 1"
            class="text-grey text-caption align-self-center"
          >
            (+{{ selectedDay.length - 1 }}개)
          </span>
        </template>
        <template v-slot:item="{ props, item }">
          <v-list-item v-bind="props" :title="item.raw"></v-list-item>
        </template>
      </v-select>
    </v-col>
    <v-col cols="12" md="2">
      <v-select
        :model-value="selectedPeriod"
        @update:model-value="handlePeriodChange"
        :items="periods"
        label="교시"
        dense
        variant="underlined"
        multiple
        clearable
      >
        <template v-slot:selection="{ item, index }">
          <v-chip v-if="index === 0">
            <span>{{ item.title }}</span>
          </v-chip>
          <span
            v-if="index === 1"
            class="text-grey text-caption align-self-center"
          >
            (+{{ selectedPeriod.length - 1 }}개)
          </span>
        </template>
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
      clearable
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
  // 정렬만 수행 (로직은 handlePeriodChange에서 처리)
  newValue.sort((a, b) => {
    if (a === '전체') return -1;
    if (b === '전체') return 1;
    return parseInt(a, 10) - parseInt(b, 10);
  });
});

// --- 교시 선택 핸들러 (전체 선택 로직) ---
function handlePeriodChange(newVal) {
  const allOption = '전체';
  const allSpecifics = periods.filter(p => p !== allOption);
  
  const oldVal = selectedPeriod.value;
  const isAllInNew = newVal.includes(allOption);
  const isAllInOld = oldVal.includes(allOption);

  let finalSelection = [];

  // 1. '전체' 옵션이 방금 클릭되어 추가된 경우
  if (isAllInNew && !isAllInOld) {
    finalSelection = [...periods]; // 전체 선택
  }
  // 2. '전체' 옵션이 방금 클릭되어 해제된 경우
  else if (!isAllInNew && isAllInOld) {
    // 사용자가 '전체' 칩을 직접 삭제했거나 체크를 해제한 경우 -> 모두 해제
    // 단, 특정 항목 하나를 해제해서 '전체'가 빠진 경우는 아래 3번 로직에서 처리됨.
    // Vuetify에서 '전체'를 클릭해서 해제하면 newVal에는 나머지 항목들이 들어있음.
    // 하지만 우리는 '전체'를 클릭하면 모두 해제하고 싶음.
    
    // 만약 newVal의 길이가 oldVal보다 1 작다면(전체만 빠짐) -> 모두 해제 의도
    if (newVal.length === oldVal.length - 1) {
         finalSelection = [];
    } else {
        // 그 외(특정 항목 해제로 인해 전체가 빠진 경우 등) -> 그대로 둠 (3번 로직으로)
        finalSelection = newVal;
    }
  } 
  // 3. 개별 항목을 클릭한 경우
  else {
    const newSpecifics = newVal.filter(p => p !== allOption);
    
    // 모든 개별 항목이 선택되었는지 확인
    if (newSpecifics.length === allSpecifics.length) {
      // 모두 선택됨 -> '전체' 포함
      if (!isAllInNew) {
        finalSelection = [allOption, ...newSpecifics];
      } else {
        finalSelection = newVal;
      }
    } else {
      // 일부만 선택됨 -> '전체' 제외
      if (isAllInNew) {
        finalSelection = newSpecifics;
      } else {
        finalSelection = newVal;
      }
    }
  }
  
  selectedPeriod.value = finalSelection;
}


// --- API 호출 ---
onMounted(async () => {
  try {
    const response = await axios.get('/api/lectures');
    allLectures.value = response.data;
    console.log(`성공: ${allLectures.value.length}개의 분반을 모두 로드했습니다.`);
  } catch (error) {
    console.error("강의 목록을 불러오는 중 오류 발생:", error);
    alert("전체 강의 목록을 불러오는 데 실패했습니다.");
  }
});

// --- 필터링 로직 ---

// 각 필터의 선택지를 동적으로 생성하는 계산된 속성 (종속형 드롭다운 구현)
const departments = computed(() => [...new Set(allLectures.value.map(l => l.department))].sort());

const courseTypes = computed(() => {
  let lectures = allLectures.value;
  if (selectedDepartment.value) {
    lectures = lectures.filter(l => l.department === selectedDepartment.value);
  }
  return [...new Set(lectures.map(l => l.course_type))].sort();
});

const detailedAreas = computed(() => {
  let lectures = allLectures.value;
  if (selectedDepartment.value) {
    lectures = lectures.filter(l => l.department === selectedDepartment.value);
  }
  if (selectedCourseType.value) {
    lectures = lectures.filter(l => l.course_type === selectedCourseType.value);
  }
  return [...new Set(lectures.map(l => l.detailed_area))].sort();
});

const grades = computed(() => {
  let gradeOptions = new Set();
  
  if (selectedDepartment.value === '건축학전공') {
    // If '건축학전공' is selected, get all grades available for it
    allLectures.value.filter(l => l.department === '건축학전공')
                     .map(l => l.grade)
                     .forEach(g => gradeOptions.add(g));
  } else if (selectedDepartment.value) {
    // If any other department is selected, limit to 1-4
    gradeOptions.add('1');
    gradeOptions.add('2');
    gradeOptions.add('3');
    gradeOptions.add('4');
  } else {
    // If no department is selected, show all grades except '34' (current default)
    allLectures.value.map(l => l.grade)
                     .filter(g => g !== '34')
                     .forEach(g => gradeOptions.add(g));
  }

  return Array.from(gradeOptions).sort((a, b) => {
    const numA = parseInt(a, 10);
    const numB = parseInt(b, 10);
    return numA - numB;
  });
});

// --- 종속형 드롭다운 값 초기화 Watchers ---
watch(selectedDepartment, () => {
  selectedCourseType.value = null;
  selectedDetailedArea.value = null;
  selectedGrade.value = []; // 학부 변경 시 학년도 초기화
});

watch(selectedCourseType, () => {
  selectedDetailedArea.value = null;
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