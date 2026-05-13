<template>
  <div class="class-scores">
    <div class="filter-bar">
      <el-select v-model="selectedClass" placeholder="请选择班级" @change="onClassChange">
        <el-option v-for="cls in classes" :key="cls.id" :label="cls.name" :value="cls.id" />
      </el-select>
    </div>

    <div class="score-grid" v-loading="loading">
      <div v-for="student in students" :key="student.id" class="score-card">
        <div class="student-name">{{ student.name }}</div>
        <div class="rank-image">
          <img :src="student.rank_image" :alt="student.rank_name" />
        </div>
        <div class="rank-name">{{ student.rank_name }}</div>
        <div class="next-rank" v-if="student.next_rank_name">
          距「{{ student.next_rank_name }}」还差 {{ student.score_to_next }} 分
        </div>
        <div class="next-rank achieved" v-else>
          已达最高段位
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

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

const classes = ref<any[]>([])
const ranks = ref<Rank[]>([])
const students = ref<Student[]>([])
const loading = ref(false)
const selectedClass = ref<number | null>(null)

async function fetchClasses() {
  const response = await api.get('/teacher/classes')
  classes.value = response.data
  if (classes.value.length > 0) {
    selectedClass.value = classes.value[0].id
    await fetchStudents()
  }
}

async function fetchRanks() {
  const response = await api.get('/ranks')
  ranks.value = response.data
}

async function fetchStudents() {
  if (!selectedClass.value) return
  loading.value = true
  try {
    const response = await api.get('/students', {
      params: { class_id: selectedClass.value }
    })
    // 为每个学生计算段位信息
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
      // 无上限段位
      if (score >= rank.min_score) {
        currentRank = rank
        nextRank = null
      }
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
  fetchStudents()
}

onMounted(async () => {
  await fetchRanks()
  await fetchClasses()
})
</script>

<style scoped>
.class-scores {
  padding: 20px;
}

.filter-bar {
  margin-bottom: 20px;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.score-card {
  background: #f9fafb;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.student-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.rank-image {
  width: 80px;
  height: 80px;
  margin: 0 auto 8px;
}

.rank-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.rank-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.next-rank {
  font-size: 12px;
  color: #999;
}

.next-rank.achieved {
  color: #22c55e;
  font-weight: 500;
}
</style>