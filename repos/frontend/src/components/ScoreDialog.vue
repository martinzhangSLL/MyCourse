<template>
  <el-dialog
    v-model="visible"
    title="加减分"
    width="400px"
    :close-on-click-modal="false"
  >
    <div class="score-dialog-content">
      <div class="type-tabs">
        <button
          :class="{ active: scoreType === 'add' }"
          @click="scoreType = 'add'"
        >
          加分
        </button>
        <button
          :class="{ active: scoreType === 'subtract' }"
          @click="scoreType = 'subtract'"
        >
          扣分
        </button>
      </div>

      <div class="value-input-wrapper">
        <input
          v-model.number="value"
          type="number"
          class="value-input"
          :class="{ minus: scoreType === 'subtract' }"
          placeholder="请输入分值"
          min="1"
        />
      </div>

      <div class="reason-select">
        <el-select
          v-model="reason"
          placeholder="选择原因"
          filterable
          allow-create
          default-first-option
          style="width: 100%"
        >
          <el-option
            v-for="item in reasons"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="loading">
          确认
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const props = defineProps<{
  modelValue: boolean
  studentId: number
  courseId: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const scoreType = ref<'add' | 'subtract'>('add')
const value = ref<number | undefined>()
const reason = ref('')
const loading = ref(false)
const reasons = ref<string[]>(['考试', '作业', '荣誉', '其他'])

watch(visible, async (newVal) => {
  if (newVal) {
    // Reset form
    scoreType.value = 'add'
    value.value = undefined
    reason.value = ''
    // Fetch reasons from config
    await fetchReasons()
  }
})

async function fetchReasons() {
  try {
    const response = await api.get('/config/reasons')
    reasons.value = JSON.parse(response.data.value)
  } catch (err) {
    console.error('Failed to fetch reasons:', err)
  }
}

async function handleConfirm() {
  if (!value.value || value.value <= 0) {
    ElMessage.warning('请输入有效的分值')
    return
  }

  if (!reason.value) {
    ElMessage.warning('请选择或输入原因')
    return
  }

  loading.value = true

  try {
    const scoreValue = scoreType.value === 'subtract' ? -value.value : value.value

    await api.post('/scores', {
      student_id: props.studentId,
      value: scoreValue,
      reason: reason.value,
      course_id: props.courseId,
      score_at: new Date().toISOString()
    })

    ElMessage.success(scoreType.value === 'add' ? '加分成功' : '扣分成功')
    visible.value = false
    emit('success')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.score-dialog-content {
  padding: 10px 0;
}

.type-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.type-tabs button {
  flex: 1;
  padding: 12px;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  font-size: 16px;
  cursor: pointer;
  border-radius: var(--border-radius);
  transition: all 0.2s;
}

.type-tabs button.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.type-tabs button:first-child.active {
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-score-plus);
  border-color: var(--color-score-plus);
}

.type-tabs button:last-child.active {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-score-minus);
  border-color: var(--color-score-minus);
}

.value-input-wrapper {
  margin-bottom: 20px;
}

.value-input {
  width: 100%;
  padding: 16px;
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  outline: none;
  transition: border-color 0.2s;
  color: var(--color-score-plus);
}

.value-input:focus {
  border-color: var(--color-primary);
}

.value-input.minus {
  color: var(--color-score-minus);
}

.value-input::placeholder {
  font-size: 16px;
  font-weight: normal;
  color: var(--color-text-secondary);
}

.reason-select {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
