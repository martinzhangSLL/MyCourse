<template>
  <div class="class-scores">
    <div class="header">
      <h1 class="title">班级分值看板</h1>
      <p class="subtitle">弟子修为一览</p>
      <div class="divider"></div>
    </div>

    <div class="filter-bar">
      <el-select v-model="selectedClass" placeholder="请选择班级" @change="onClassChange">
        <el-option v-for="cls in classes" :key="cls.id" :label="cls.name" :value="cls.id" />
      </el-select>
      <el-select v-model="selectedCourse" placeholder="请选择课程" :disabled="!selectedClass" @change="onCourseChange" style="width: 200px; margin-left: 12px">
        <el-option label="所有课程" :value="null" />
        <el-option v-for="course in courses" :key="course.id" :label="course.name" :value="course.id" />
      </el-select>
    </div>

    <div class="score-grid" v-loading="loading">
      <div
        v-for="student in students"
        :key="student.id"
        class="score-card"
        :class="{ 'highest-rank': student.next_rank_name === null }"
        @click="openScoreDialog(student)"
      >
        <div class="halo"></div>
        <div class="rank-image">
          <img :src="student.rank_image" :alt="student.rank_name" />
        </div>
        <div class="student-name">{{ student.name }}</div>
        <div class="progress-section" v-if="student.next_rank_name">
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: getProgressWidth(student) + '%' }"
            ></div>
          </div>
          <div class="progress-text">
            距「{{ student.next_rank_name }}」还差 {{ student.score_to_next }} 分
          </div>
        </div>
        <div class="achieved-text" v-else>
          已达最高境界 ✦
        </div>
      </div>
    </div>

    <div class="footer-divider"></div>

    <ScoreDialog
      v-model="dialogVisible"
      :student-id="selectedStudent?.id || 0"
      :course-id="selectedCourse || 0"
      :course-name="selectedCourseName"
      :courses="selectedCourse === null ? courses : []"
      @success="onScoreSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import ScoreDialog from '@/components/ScoreDialog.vue'

interface Rank {
  id: number
  name: string
  min_score: number
  max_score: number | null
  image_url: string
  display_order: number
}

interface Student {
  id: number
  name: string
  student_no: string
  current_score: number
  rank_id: number
  rank_name: string
  rank_image: string
  next_rank_name: string | null
  score_to_next: number | null
}

interface Course {
  id: number
  name: string
}

const classes = ref<any[]>([])
const courses = ref<Course[]>([])
const ranks = ref<Rank[]>([])
const students = ref<Student[]>([])
const loading = ref(false)
const selectedClass = ref<number | null>(null)
const selectedCourse = ref<number | null>(null)
const dialogVisible = ref(false)
const selectedStudent = ref<Student | null>(null)

const selectedCourseName = computed(() => {
  if (selectedCourse.value === null) return ''
  const course = courses.value.find(c => c.id === selectedCourse.value)
  return course?.name || ''
})

async function fetchClasses() {
  const response = await api.get('/teacher/classes')
  classes.value = response.data
  if (classes.value.length > 0) {
    selectedClass.value = classes.value[0].id
    await fetchCourses()
    await fetchStudents()
  }
}

async function fetchRanks() {
  const response = await api.get('/ranks')
  ranks.value = response.data
}

async function fetchCourses() {
  if (!selectedClass.value) return
  const response = await api.get('/teacher/class-courses', {
    params: { class_id: selectedClass.value }
  })
  courses.value = response.data
}

async function fetchStudents() {
  if (!selectedClass.value) return
  loading.value = true
  try {
    const response = await api.get('/students', {
      params: { class_id: selectedClass.value }
    })
    students.value = response.data.map((s: any) => calculateRank(s))
  } catch (error) {
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

function calculateRank(student: any): Student {
  const score = student.current_score || 0
  const sortedRanks = [...ranks.value].sort((a, b) => a.display_order - b.display_order)

  let currentRank = sortedRanks[0]
  let nextRank: Rank | null = null

  for (let i = 0; i < sortedRanks.length; i++) {
    const rank = sortedRanks[i]
    const max = rank.max_score
    if (max === null) {
      if (score >= rank.min_score) {
        currentRank = rank
        nextRank = null
        break
      }
      if (i + 1 < sortedRanks.length) {
        continue
      }
      nextRank = sortedRanks[1] || null
    } else if (score >= rank.min_score && score <= max) {
      currentRank = rank
      nextRank = sortedRanks[i + 1] || null
      break
    } else if (score > max) {
      currentRank = sortedRanks[i + 1] || rank
      nextRank = sortedRanks[i + 2] || null
    }
  }

  let scoreToNext: number | null = null
  if (nextRank) {
    scoreToNext = nextRank.min_score - score
  }

  return {
    ...student,
    rank_id: currentRank.id,
    rank_name: currentRank.name,
    rank_image: currentRank.image_url,
    next_rank_name: nextRank?.name || null,
    score_to_next: scoreToNext,
  }
}

function onClassChange() {
  selectedCourse.value = null
  fetchCourses()
  fetchStudents()
}

function onCourseChange() {
  // 课程筛选可选，当前实现暂时只用班级筛选
}

function openScoreDialog(student: Student) {
  selectedStudent.value = student
  dialogVisible.value = true
}

async function onScoreSuccess() {
  await fetchStudents()
}

// 计算进度条宽度
function getProgressWidth(student: Student): number {
  if (!student.next_rank_name || !student.score_to_next) return 0
  const currentScore = student.current_score
  if (currentScore <= 0) return 0
  const nextRank = ranks.value.find(r => r.name === student.next_rank_name)
  if (!nextRank) return 0
  const nextMinScore = nextRank.min_score
  const progress = (currentScore / nextMinScore) * 100
  return Math.min(progress, 95)
}

onMounted(async () => {
  await fetchRanks()
  await fetchClasses()
})
</script>

<style scoped>
.class-scores {
  padding: 20px;
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #0a1a0d 0%, #0d2818 50%, #0a1a0d 100%);
}

/* 头部区域 */
.header {
  text-align: center;
  margin-bottom: 30px;
}

.title {
  font-size: 24px;
  color: #fff;
  margin: 0 0 8px;
  text-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
}

.subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.divider {
  margin: 16px auto;
  height: 2px;
  width: 300px;
  background: linear-gradient(90deg, transparent, #22c55e, transparent);
}

/* 筛选栏 */
.filter-bar {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.filter-bar :deep(.el-select) {
  width: 200px;
}

.filter-bar :deep(.el-input__wrapper) {
  background: rgba(10, 26, 13, 0.95);
  border: 1px solid rgba(34, 197, 94, 0.4);
  box-shadow: 0 0 15px rgba(34, 197, 94, 0.1);
}

.filter-bar :deep(.el-input__inner) {
  color: #fff;
}

.filter-bar :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

.filter-bar :deep(.el-select-dropdown__item) {
  background: rgba(10, 26, 13, 0.95);
  color: #fff;
}

.filter-bar :deep(.el-select-dropdown__item.hover),
.filter-bar :deep(.el-select-dropdown__item:hover) {
  background: rgba(34, 197, 94, 0.2);
}

.filter-bar :deep(.el-select-dropdown) {
  background: rgba(10, 26, 13, 0.95);
  border: 1px solid rgba(34, 197, 94, 0.4);
}

/* 卡片网格 */
.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

/* 卡片基础样式 */
.score-card {
  position: relative;
  background: linear-gradient(145deg, rgba(10, 26, 13, 0.95), rgba(34, 197, 94, 0.15));
  border: 1px solid rgba(34, 197, 94, 0.4);
  border-radius: 16px;
  padding: 24px 16px 20px;
  text-align: center;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.score-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(34, 197, 94, 0.15);
}

/* 最高境界卡片 */
.score-card.highest-rank {
  border: 2px solid #22c55e;
  box-shadow: 0 0 40px rgba(34, 197, 94, 0.3);
}

/* 顶部光晕 */
.halo {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, rgba(34, 197, 94, 0.3), transparent);
  border-radius: 50%;
  pointer-events: none;
}

/* 最高境界标签 */
.highest-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 10px;
  text-shadow: none;
}

/* 境界图片 */
.rank-image {
  width: 150px;
  height: 150px;
  margin: 0 auto 12px;
  position: relative;
  z-index: 1;
}

.rank-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 0 15px rgba(34, 197, 94, 0.5));
}

.highest-rank .rank-image img {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 境界角标 */
.rank-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  margin-bottom: 10px;
}

.rank-tag.tag-low {
  background: linear-gradient(#86efac, #22c55e);
  color: #052e16;
}

.rank-tag.tag-high {
  background: linear-gradient(#22c55e, #16a34a);
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* 学生姓名 */
.student-name {
  font-size: 18px;
  color: #fff;
  font-weight: 600;
  margin-bottom: 12px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 进度条区域 */
.progress-section {
  margin-top: 8px;
}

.progress-bar {
  height: 8px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(#22c55e, #86efac);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 11px;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

/* 已达最高境界文字 */
.achieved-text {
  font-size: 12px;
  color: #22c55e;
  font-weight: 500;
  text-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
  margin-top: 8px;
}

/* 底部装饰分隔线 */
.footer-divider {
  margin: 30px auto;
  height: 2px;
  width: 300px;
  background: linear-gradient(90deg, transparent, #22c55e, transparent);
  position: relative;
  text-align: center;
}

.footer-divider::before {
  content: '✦';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  background: #0a1a0d;
  padding: 0 15px;
  color: #22c55e;
  font-size: 14px;
}
</style>