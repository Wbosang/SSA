<template>
  <v-textarea
    v-model="preferenceText"
    label="선호 조건을 입력하세요"
    placeholder="예: 금요일은 비워주세요. 오전 수업으로만 듣고 싶어요."
    rows="3"
    variant="underlined"
    auto-grow
    class="mt-4"
  ></v-textarea>
  <v-btn
    :loading="loading"
    :disabled="loading"
    color="primary"
    block
    size="large"
    @click="generate"
  >
    최적 시간표 생성하기
  </v-btn>
</template>

<script setup>
import { computed } from 'vue'

// v-model 및 loading prop을 위한 정의
const props = defineProps({
  loading: Boolean,
  modelValue: String
})
const emit = defineEmits(['generate', 'update:modelValue'])

// v-textarea의 입력을 부모와 양방향 바인딩
const preferenceText = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const generate = () => {
  // 부모에게 'generate' 이벤트를 전달
  emit('generate')
}
</script>
