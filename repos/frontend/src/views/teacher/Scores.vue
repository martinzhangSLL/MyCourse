<template>
  <div class="scores-page">
    <div class="page-header">
      <div class="filter-row">
        <div class="filter-item">
          <span class="filter-label">班级：</span>
          <el-select
            v-model="selectedClassId"
            placeholder="请选择班级"
            @change="onClassChange"
            style="width: 200px"
          >
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="filter-label">课程：</span>
          <el-select
            v-model="selectedCourseId"
            placeholder="请选择课程"
            :disabled="!selectedClassId"
            @change="onCourseChange"
            style="width: 200px"
          >
            <el-option
              label="--所有--"
              :value="null"
            />
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            />
          </el-select>
        </div>
      </div>
    </div>

    <div class="students-grid" v-if="students.length > 0">
      <ScoreCard
        v-for="student in students"
        :key="student.id"
        :student="student"
        :is-selected="selectedStudentId === student.id"
        @click="onStudentClick(student)"
      />
    </div>

    <el-empty v-else-if="selectedClassId" description="该班级暂无学生">
    </el-empty>

    <el-empty v-else description="请先选择班级">
    </el-empty>

    <ScoreDialog
      v-model="dialogVisible"
      :student-id="selectedStudentId || 0"
      :course-id="selectedCourseId || 0"
      :course-name="selectedCourseName"
      :courses="selectedCourseId === null ? courses : []"
      @success="onScoreSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import ScoreCard from '@/components/ScoreCard.vue'
import ScoreDialog from '@/components/ScoreDialog.vue'

interface ClassItem {
  id: number
  name: string
}

interface CourseItem {
  id: number
  name: string
}

interface Student {
  id: number
  name: string
  student_no: string
  current_score: number
}

const classes = ref<ClassItem[]>([])
const courses = ref<CourseItem[]>([])
const students = ref<Student[]>([])

const selectedClassId = ref<number | undefined>()
const selectedCourseId = ref<number | null>(null)
const selectedStudentId = ref<number | undefined>()

const dialogVisible = ref(false)

// 当前选中课程的名称（用于在"所有"模式下显示在popup中）
const selectedCourseName = computed(() => {
  if (selectedCourseId.value === null) return ''
  const course = courses.value.find(c => c.id === selectedCourseId.value)
  return course?.name || ''
})

onMounted(async () => {
  await fetchTeacherClasses()
})

async function fetchTeacherClasses() {
  try {
    const response = await api.get('/teacher/classes')
    classes.value = response.data

    // 默认选中第一个班级
    if (classes.value.length > 0) {
      selectedClassId.value = classes.value[0].id
      await fetchClassCourses()
    }
  } catch (err) {
    console.error('Failed to fetch classes:', err)
  }
}

async function onClassChange() {
  selectedCourseId.value = null // 重置为"所有"
  students.value = []

  if (selectedClassId.value) {
    await fetchClassCourses()
  }
}

async function fetchClassCourses() {
  if (!selectedClassId.value) return

  try {
    const response = await api.get('/teacher/class-courses', {
      params: { class_id: selectedClassId.value }
    })
    courses.value = response.data

    // 默认选中"所有"选项
    selectedCourseId.value = null
    // 自动加载学生列表
    await fetchStudents()
  } catch (err) {
    console.error('Failed to fetch courses:', err)
  }
}

async function onCourseChange() {
  students.value = []

  if (selectedClassId.value) {
    await fetchStudents()
  }
}

async function fetchStudents() {
  if (!selectedClassId.value) return

  try {
    const response = await api.get('/students', {
      params: { class_id: selectedClassId.value }
    })
    students.value = response.data
  } catch (err) {
    console.error('Failed to fetch students:', err)
  }
}

function onStudentClick(student: Student) {
  selectedStudentId.value = student.id
  dialogVisible.value = true
}

async function onScoreSuccess() {
  // Refresh students to get updated scores
  await fetchStudents()
}
</script>

<style scoped>
.scores-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
}

.filter-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-weight: 500;
  color: var(--color-text);
}

.students-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  padding: 10px 0;
}
</style>
