<template>
  <el-dialog
    v-model="visible"
    title="加减分"
    width="400px"
    :close-on-click-modal="false"
  >
    <div class="score-dialog-content">
      <!-- 课程选择（当选择了"所有"时显示） -->
      <div v-if="showCourseSelect" class="course-select">
        <el-select
          v-model="selectedCourseId"
          placeholder="请选择课程"
          style="width: 100%"
        >
          <el-option
            v-for="course in courses"
            :key="course.id"
            :label="course.name"
            :value="course.id"
          />
        </el-select>
      </div>

      <!-- 已选课程显示 -->
      <div v-else class="course-display">
        <span class="course-label">课程：{{ courseName }}</span>
      </div>

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

interface CourseItem {
  id: number
  name: string
}

const props = defineProps<{
  modelValue: boolean
  studentId: number
  courseId: number
  courseName: string
  courses: CourseItem[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 是否显示课程选择器（当从"所有"进入时需要选择课程）
const showCourseSelect = computed(() => {
  return props.courses && props.courses.length > 0
})

// 内部选中的课程ID（用于在对话框内选择课程）
const selectedCourseId = ref<number | undefined>()

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
    selectedCourseId.value = undefined
    // Fetch reasons from config
    await fetchReasons()
  }
})

async function fetchReasons() {
  try {
    const response = await api.get('/config/reasons')
    reasons.value = response.data.reasons
  } catch (err) {
    console.error('Failed to fetch reasons:', err)
  }
}

async function handleConfirm() {
  // 如果需要选择课程，则验证
  if (showCourseSelect.value && !selectedCourseId.value) {
    ElMessage.warning('请选择课程')
    return
  }

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
    // 优先使用对话框内选择的课程，否则使用外部传入的课程ID
    const finalCourseId = selectedCourseId.value || props.courseId

    await api.post('/scores', {
      student_id: props.studentId,
      value: scoreValue,
      reason: reason.value,
      course_id: finalCourseId,
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

.course-select {
  margin-bottom: 20px;
}

.course-display {
  margin-bottom: 20px;
  padding: 12px;
  background: var(--color-surface);
  border-radius: var(--border-radius);
}

.course-label {
  font-weight: 500;
  color: var(--color-primary);
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
