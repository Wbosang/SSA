<template>
  <v-app>
    <v-app-bar app color="primary">
      <v-app-bar-title>SSA 시간표 생성기</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container>
        <LectureSelector v-model="selectedCourseIds" />
        <ConditionInput v-model="preferenceText" :loading="loading" @generate="handleGenerate" />
        <TimetableDisplay 
          :loading="loading" 
          :combination="currentCombination" 
          :search-performed="searchPerformed" 
        />
      </v-container>
    </v-main>

    <v-footer app color="primary">
      <v-col class="text-center" cols="12">
        &copy; {{ new Date().getFullYear() }} — <strong>SSA Timetable</strong>
      </v-col>
    </v-footer>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios' // axios 임포트
import LectureSelector from './components/LectureSelector.vue'
import ConditionInput from './components/ConditionInput.vue'
import TimetableDisplay from './components/TimetableDisplay.vue'

// Axios 요청 인터셉터 추가
axios.interceptors.request.use(request => {
  console.log('Starting Request', JSON.stringify(request, null, 2))
  return request
})

const loading = ref(false)
const searchPerformed = ref(false)
const currentCombination = ref([]) // 최종 시간표 조합(1개)을 담을 상태

// 자식 컴포넌트와 v-model로 연동될 상태들
const selectedCourseIds = ref([])
const preferenceText = ref('')

// '생성하기' 버튼 클릭 시 실행될 함수
const handleGenerate = async () => {
  console.log("API 호출 시작!");
  loading.value = true;
  searchPerformed.value = true;
  currentCombination.value = []; // 이전 결과 초기화

  try {
    // 백엔드 API에 POST 요청 전송
    const response = await axios.post('http://localhost:8000/api/generate', {
      lecture_nos: selectedCourseIds.value,
      user_preference_text: preferenceText.value
    });
    
    // API로부터 받은 여러 조합 중 첫 번째 조합을 화면에 표시
    if (response.data && response.data.length > 0) {
      currentCombination.value = response.data[0];
    } else {
      currentCombination.value = [];
    }
    
  } catch (error) {
    console.error("API 호출 중 오류 발생:", error);
    alert("시간표 생성 중 오류가 발생했습니다. 자세한 내용은 콘솔을 확인하세요.");
    currentCombination.value = [];
  } finally {
    loading.value = false;
    console.log("API 호출 완료!");
  }
}
</script>

<style>
/* 전역 스타일 또는 이 컴포넌트에만 적용될 스타일 */
</style>