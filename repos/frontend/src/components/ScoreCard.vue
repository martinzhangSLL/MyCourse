<template>
  <div class="score-card" :class="{ selected: isSelected }" @click="$emit('click')">
    <div class="student-no">{{ student.student_no }}</div>
    <div class="student-name">{{ student.name }}</div>
    <div class="current-score">{{ student.current_score }}</div>
  </div>
</template>

<script setup lang="ts">
interface Student {
  id: number
  name: string
  student_no: string
  current_score: number
}

defineProps<{
  student: Student
  isSelected?: boolean
}>()

defineEmits<{
  click: []
}>()
</script>

<style scoped>
.score-card {
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 120px;
}

.score-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2);
}

.score-card.selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.3);
}

.student-no {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.student-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.current-score {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-primary-dark);
}
</style>
