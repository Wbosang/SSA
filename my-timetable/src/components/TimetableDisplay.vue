<template>
  <div style="position: relative;">
    <!-- 로딩 오버레이 -->
    <v-overlay :model-value="loading" class="align-center justify-center" persistent>
      <v-progress-circular color="primary" indeterminate size="64"></v-progress-circular>
    </v-overlay>

    <v-card class="mt-6">
      <v-card-title class="d-flex justify-space-between align-center">
        <span>시간표 결과</span>
        <v-chip v-if="searchPerformed && combination.length > 0" color="primary" label>
          총 {{ totalCredits }}학점
        </v-chip>
      </v-card-title>
      <v-card-text>
        <!-- 1. 검색 수행되었고 결과가 있을 때: 커스텀 테이블 (Rowspan 적용) -->
        <div v-if="searchPerformed && combination.length > 0" class="table-container">
          <v-table class="timetable-custom">
            <thead>
              <tr>
                <th class="text-center fixed-header" style="width: 40px; min-width: 40px;">교시</th>
                <th v-for="day in days" :key="day" class="text-center fixed-header" style="min-width: 60px; width: 60px;">
                  {{ day }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rIndex) in displayGrid" :key="rIndex">
                <!-- 교시 표시 -->
                <td class="text-center font-weight-bold bg-grey-lighten-4">
                  {{ rIndex + 1 }}{{ mobile ? '' : '교시' }}
                </td>
                
                <!-- 요일별 셀 (병합 로직 적용) -->
                <template v-for="(cell, cIndex) in row" :key="cIndex">
                  <!-- show가 true인 경우에만 렌더링 (병합된 셀은 show=false로 숨김) -->
                  <td 
                    v-if="cell.show" 
                    :rowspan="cell.rowspan"
                    class="text-center lecture-cell"
                    :class="cell.hasLecture ? 'bg-blue-lighten-5' : ''"
                    style="vertical-align: middle; position: relative;"
                  >
                    <div v-if="cell.hasLecture" class="lecture-content">
                      <div class="font-weight-bold text-body-2">{{ cell.name }}</div>
                      <div class="text-caption text-grey-darken-2">{{ cell.location }}</div>
                    </div>
                  </td>
                </template>
              </tr>
            </tbody>
          </v-table>
        </div>

        <!-- 2. 검색 수행되었지만 결과가 없을 때 -->
        <v-alert
          v-else-if="searchPerformed && combination.length === 0"
          type="warning"
          variant="outlined"
        >
          조건에 맞는 시간표 조합을 찾을 수 없습니다.
        </v-alert>

        <!-- 3. 아직 검색 전일 때 -->
        <div v-else class="text-center pa-4 text-grey">
          원하는 강의와 조건을 설정하고 '최적 시간표 생성하기' 버튼을 눌러주세요.
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, watch, computed, defineProps } from 'vue';
import { useDisplay } from 'vuetify'; // Vuetify의 useDisplay composable 임포트

const props = defineProps({
  loading: Boolean,
  combination: Array,
  searchPerformed: Boolean,
});

const { mobile } = useDisplay(); // 현재 화면이 모바일인지 감지

const days = ['월', '화', '수', '목', '금'];
const dayIndexMap = { '월': 0, '화': 1, '수': 2, '목': 3, '금': 4 };

// 총 학점 계산
const totalCredits = computed(() => {
  if (!props.combination) return 0;
  return props.combination.reduce((sum, lecture) => sum + lecture.credits, 0);
});

// 그리드 데이터 (반응형)
const displayGrid = ref([]);

// 시간표 데이터를 그리드 형태(10행 5열)로 변환하는 함수
const generateGrid = (combination) => {
  // 1. 10교시 x 5요일 빈 그리드 생성
  // show: 렌더링 여부, rowspan: 병합 줄 수, hasLecture: 강의 존재 여부
  const grid = Array.from({ length: 10 }, () => 
    Array.from({ length: 5 }, () => ({ 
      show: true, 
      rowspan: 1, 
      hasLecture: false, 
      name: '', 
      location: '' 
    }))
  );

  if (!combination || combination.length === 0) return grid;

  // 2. 강의 배치
  combination.forEach(lecture => {
    const rawTimeLocation = lecture.raw_time_location || '';
    // 예: "월[1,2]/301 화[3,4]/402" -> 분리
    const parts = rawTimeLocation.split(' '); 
    
    parts.forEach(part => {
      // 시간과 장소 분리 (예: "월[1,2]" 와 "301" 또는 "월[1,2]/301")
      // 데이터 형식에 따라 '/' 로 구분될 수도 있고 없을 수도 있음. 
      // 유연하게 처리: '/' 기준으로 나누되, 없으면 뒷부분은 빈 문자열
      const locSplit = part.split('/');
      const timeStr = locSplit[0]; // "월[1,2]"
      const location = locSplit.length > 1 ? locSplit[1] : '';

      // 요일과 교시 파싱
      const match = /([월화수목금])\[([\d,]+)\]/.exec(timeStr);
      if (match) {
        const dayChar = match[1];
        const periodsStr = match[2]; // "1,2"
        const dayIdx = dayIndexMap[dayChar];
        
        if (dayIdx !== undefined) {
          // 교시들을 숫자로 변환하고 정렬
          const periods = periodsStr.split(',')
                                  .map(p => parseInt(p, 10))
                                  .filter(p => p >= 1 && p <= 10)
                                  .sort((a, b) => a - b);

          // 연속된 교시들을 그룹화 (예: 1,2,3 -> 하나의 블록 / 1,2, 5,6 -> 두 개의 블록)
          // 하지만 보통 대학 강의는 하루에 한 블록이거나, 떨어져 있어도 별개로 처리하면 됨.
          // 여기서는 연속된 구간을 찾아서 병합
          
          let i = 0;
          while (i < periods.length) {
            const startPeriod = periods[i];
            let duration = 1;
            
            // 다음 교시가 현재 교시 + 1 인지 확인하여 연속성 체크
            while (i + duration < periods.length && periods[i + duration] === startPeriod + duration) {
              duration++;
            }

            const rowIndex = startPeriod - 1; // 0-based index

            // 그리드 업데이트
            if (rowIndex < 10) {
              // 시작 셀 설정
              const cell = grid[rowIndex][dayIdx];
              cell.hasLecture = true;
              cell.name = lecture.course_name;
              cell.location = location;
              cell.rowspan = duration;

              // 병합된 나머지 셀들은 숨김 처리
              for (let d = 1; d < duration; d++) {
                if (rowIndex + d < 10) {
                  grid[rowIndex + d][dayIdx].show = false;
                }
              }
            }

            // 다음 그룹으로 이동
            i += duration;
          }
        }
      }
    });
  });

  return grid;
};

watch(() => props.combination, (newVal) => {
  displayGrid.value = generateGrid(newVal);
}, { immediate: true });

</script>

<style scoped>
.table-container {
  overflow-x: auto; /* 가로 스크롤 활성화 */
  width: 100%;
}

.timetable-custom {
  min-width: 340px; /* 모바일 화면 너비에 맞춤 */
  border-collapse: separate; /* 테두리 스타일링을 위해 */
  border-spacing: 0;
}

.timetable-custom th {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  border-right: 1px solid rgba(0, 0, 0, 0.12);
}

.timetable-custom td {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  border-right: 1px solid rgba(0, 0, 0, 0.12);
  height: 60px !important;
}

.timetable-custom th:first-child,
.timetable-custom td:first-child {
  border-left: 1px solid rgba(0, 0, 0, 0.12);
}

/* 상단 헤더 고정 (옵션) */
.timetable-custom thead th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.lecture-cell {
  padding: 4px;
}

.lecture-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  line-height: 1.2;
}

@media (max-width: 600px) {
  .lecture-cell {
    padding: 0 2px !important; /* 모바일에서 좌우 여백을 줄여 글씨 공간 확보 */
  }
  .lecture-content .font-weight-bold {
    font-size: 0.65rem !important; /* 모바일에서 강의명 글씨 크기 줄임 */
  }
  .lecture-content .text-caption {
    font-size: 0.6rem !important; /* 모바일에서 장소 글씨 크기 줄임 */
  }
}

</style>
