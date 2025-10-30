<template>
  <v-autocomplete
    v-model="selectedLectures"
    :items="allLectures"
    :item-title="lecture => `${lecture.course_name} (${lecture.class_section}분반) - ${lecture.raw_time_location || '시간정보없음'}`"
    item-value="no" 
    chips
    closable-chips
    multiple
    label="원하는 강의(분반)를 선택하세요"
    variant="underlined"
  >
    <template v-slot:chip="{ props, item }">
      <v-chip v-bind="props" :text="`${item.raw.course_name} (${item.raw.class_section}분반)`"></v-chip>
    </template>

    <template v-slot:item="{ props, item }">
      <v-list-item
        v-bind="props"
        :title="`${item.raw.course_name} (${item.raw.class_section}분반)`"
        :subtitle="`${item.raw.department} / ${item.raw.credits}학점 / ${item.raw.raw_time_location || '시간정보없음'}`"
      ></v-list-item>
    </template>
  </v-autocomplete>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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

// API로부터 받아올 전체 강의 목록
const allLectures = ref([])

// 컴포넌트가 마운트될 때, 백엔드로부터 전체 강의 목록을 가져옵니다.
onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/lectures');
    allLectures.value = response.data;
    console.log(`성공: ${allLectures.value.length}개의 분반을 모두 선택지에 표시합니다.`);
  } catch (error) {
    console.error("강의 목록을 불러오는 중 오류 발생:", error);
    alert("전체 강의 목록을 불러오는 데 실패했습니다.");
  }
});
</script>