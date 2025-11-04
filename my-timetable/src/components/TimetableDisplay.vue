<template>
  <div style="position: relative;">
    <!-- 로딩 오버레이 -->
    <v-overlay :model-value="loading" class="align-center justify-center" persistent>
      <v-progress-circular color="primary" indeterminate size="64"></v-progress-circular>
    </v-overlay>

    <v-card class="mt-6">
      <v-card-title class="d-flex justify-space-between align-center">
        <span>시간표 결과</span>
        <v-chip v-if="searchPerformed && tableItems.length > 0" color="primary" label>
          총 {{ totalCredits }}학점
        </v-chip>
      </v-card-title>
      <v-card-text>
        <!-- 1. 검색 수행되었고 결과가 있을 때: 시간표 테이블 -->
        <v-data-table
          v-if="searchPerformed && tableItems.length > 0"
          :headers="headers"
          :items="tableItems"
          hide-default-footer
          density="compact"
          class="timetable-table"
        >
          <template v-slot:item.monday="{ item }"><div v-html="item.monday"></div></template>
          <template v-slot:item.tuesday="{ item }"><div v-html="item.tuesday"></div></template>
          <template v-slot:item.wednesday="{ item }"><div v-html="item.wednesday"></div></template>
          <template v-slot:item.thursday="{ item }"><div v-html="item.thursday"></div></template>
          <template v-slot:item.friday="{ item }"><div v-html="item.friday"></div></template>
        </v-data-table>

        <!-- 2. 검색 수행되었지만 결과가 없을 때: 결과 없음 알림 -->
        <v-alert
          v-else-if="searchPerformed && tableItems.length === 0"
          type="warning"
          variant="outlined"
        >
          조건에 맞는 시간표 조합을 찾을 수 없습니다.
        </v-alert>

        <!-- 3. 아직 검색 전일 때: 안내 메시지 -->
        <div v-else class="text-center pa-4 text-grey">
          원하는 강의와 조건을 설정하고 '최적 시간표 생성하기' 버튼을 눌러주세요.
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, watch, computed, defineProps } from 'vue';

// 부모 컴포넌트로부터 props를 받습니다.
const props = defineProps({
  loading: Boolean,
  combination: Array, // 시간표 조합 데이터
  searchPerformed: Boolean, // 검색 버튼을 눌렀는지 여부
});

// 총 학점을 계산하는 계산된 속성
const totalCredits = computed(() => {
  if (!props.combination) return 0;
  return props.combination.reduce((sum, lecture) => sum + lecture.credits, 0);
});

const headers = [
  { title: '교시', value: 'period', sortable: false, width: '80px', align: 'center' },
  { title: '월', value: 'monday', sortable: false, align: 'center' },
  { title: '화', value: 'tuesday', sortable: false, align: 'center' },
  { title: '수', value: 'wednesday', sortable: false, align: 'center' },
  { title: '목', value: 'thursday', sortable: false, align: 'center' },
  { title: '금', value: 'friday', sortable: false, align: 'center' },
];

const tableItems = ref([]);

const generateTableData = (combination) => {
    if (!combination || combination.length === 0) return [];

    const timetable = Array.from({ length: 10 }, (_, i) => ({
        period: `${i + 1}교시`,
        monday: '',
        tuesday: '',
        wednesday: '',
        thursday: '',
        friday: ''
    }));

    const dayMap = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    const dayCharMap = { '월': 0, '화': 1, '수': 2, '목': 3, '금': 4 };

    combination.forEach(lecture => {
        const rawTimeLocation = lecture.raw_time_location || '';
        const parts = rawTimeLocation.split('/');
        const timePart = parts[0];
        const location = parts.length > 1 ? parts[1] : '온라인';

        const timeRegex = /([월화수목금])\[([\d,]+)\]/g;
        let match;
        while ((match = timeRegex.exec(timePart)) !== null) {
            const dayChar = match[1];
            const dayIndex = dayCharMap[dayChar];
            const periods = match[2].split(',');

            periods.forEach(periodStr => {
                const period = parseInt(periodStr, 10);
                if (period >= 1 && period <= 10) {
                    const dayKey = dayMap[dayIndex];
                    timetable[period - 1][dayKey] = `${lecture.course_name}<br><small>(${location})</small>`;
                }
            });
        }
    });

    return timetable;
};

// props.combination이 변경될 때마다 테이블 데이터를 다시 생성합니다.
watch(() => props.combination, (newCombination) => {
    tableItems.value = generateTableData(newCombination);
}, { immediate: true }); // 초기 로드 시에도 실행

</script>

<style scoped>
.timetable-table :deep(td) {
  height: 60px !important;
  text-align: center;
  vertical-align: middle;
  font-size: 0.8rem;
  line-height: 1.2;
}
.timetable-table :deep(th) {
  font-weight: bold !important;
}
</style>
