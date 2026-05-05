<template>
  <div class="rankings-container">
    <h2 class="page-title">实时排名</h2>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <label>班级：</label>
          <el-select
            v-model="selectedClassId"
            placeholder="请选择班级"
            @change="handleClassChange"
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
          <el-radio-group v-model="period" @change="handlePeriodChange">
            <el-radio-button label="total">总排名</el-radio-button>
            <el-radio-button label="week">周排名</el-radio-button>
            <el-radio-button label="month">月排名</el-radio-button>
            <el-radio-button label="term">学期排名</el-radio-button>
          </el-radio-group>
        </div>

        <div class="filter-item" v-if="period === 'week'">
          <label>周数：</label>
          <el-select
            v-model="selectedWeek"
            placeholder="请选择周"
            @change="fetchRankings"
            style="width: 120px"
          >
            <el-option
              v-for="week in availableWeeks"
              :key="week.week"
              :label="week.label"
              :value="week.week"
            />
          </el-select>
        </div>

        <div class="filter-item" v-if="period === 'month'">
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            placeholder="请选择月份"
            format="YYYY-MM"
            value-format="YYYY-MM"
            @change="fetchRankings"
            style="width: 150px"
          />
        </div>

        <div class="filter-item">
          <el-button type="primary" @click="exportExcel" :loading="exporting">
            导出 Excel
          </el-button>
        </div>
      </div>
    </div>

    <!-- Rankings Table -->
    <div class="table-section">
      <el-table :data="rankings" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="rank" label="排名" width="100" align="center">
          <template #default="{ row }">
            <span :class="getRankClass(row.rank)">{{ row.rank }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="student_no" label="学号" width="150" />
        <el-table-column prop="student_name" label="姓名" width="150" />
        <el-table-column prop="score" label="总积分" width="150" align="center" />
        <el-table-column prop="change" label="本周期变化" align="center">
          <template #default="{ row }">
            <span :class="getChangeClass(row.change)">
              {{ row.change >= 0 ? '+' : '' }}{{ row.change }}
            </span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && rankings.length === 0" class="empty-state">
        暂无排名数据
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface ClassItem {
  id: number
  name: string
  code: string
}

interface RankingItem {
  rank: number
  student_id: number
  student_name: string
  student_no: string
  score: number
  change: number
}

interface WeekOption {
  week: number
  label: string
  is_current: boolean
}

const classes = ref<ClassItem[]>([])
const selectedClassId = ref<number | null>(null)
const period = ref<'total' | 'week' | 'month' | 'term'>('total')
const selectedWeek = ref<number | null>(null)
const selectedMonth = ref<string>('')
const availableWeeks = ref<WeekOption[]>([])
const rankings = ref<RankingItem[]>([])
const loading = ref(false)
const exporting = ref(false)

async function fetchClasses() {
  try {
    const response = await api.get('/rankings/classes')
    classes.value = response.data
    if (classes.value.length > 0) {
      selectedClassId.value = classes.value[0].id
    }
  } catch (error) {
    ElMessage.error('获取班级列表失败')
  }
}

async function fetchAvailableWeeks() {
  try {
    const response = await api.get('/rankings/weeks')
    availableWeeks.value = response.data.weeks || []
    // Set current week as default
    const currentWeek = availableWeeks.value.find(w => w.is_current)
    if (currentWeek) {
      selectedWeek.value = currentWeek.week
    } else if (availableWeeks.value.length > 0) {
      selectedWeek.value = availableWeeks.value[0].week
    }
  } catch (error) {
    console.error('Failed to fetch weeks:', error)
    availableWeeks.value = []
  }
}

async function fetchRankings() {
  if (!selectedClassId.value) {
    rankings.value = []
    return
  }

  loading.value = true
  try {
    const params: Record<string, any> = {
      class_id: selectedClassId.value,
      period: period.value
    }

    if (period.value === 'week' && selectedWeek.value) {
      params.week = selectedWeek.value
    }

    if (period.value === 'month' && selectedMonth.value) {
      params.month = selectedMonth.value
    }

    const response = await api.get('/rankings', { params })
    rankings.value = response.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取排名失败')
    rankings.value = []
  } finally {
    loading.value = false
  }
}

async function exportExcel() {
  if (!selectedClassId.value) {
    ElMessage.warning('请先选择班级')
    return
  }

  exporting.value = true
  try {
    const params: Record<string, any> = {
      class_id: selectedClassId.value,
      period: period.value
    }

    if (period.value === 'week' && selectedWeek.value) {
      params.week = selectedWeek.value
    }

    if (period.value === 'month' && selectedMonth.value) {
      params.month = selectedMonth.value
    }

    const response = await api.get('/rankings/export', {
      params,
      responseType: 'blob'
    })

    // Create download link
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // Extract filename from Content-Disposition header
    const contentDisposition = response.headers['content-disposition']
    let filename = 'rankings.xlsx'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename\*?=['"]?(?:UTF-8'')?([^;\n"']+)/i)
      if (match) {
        filename = decodeURIComponent(match[1])
      }
    }
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '导出失败')
  } finally {
    exporting.value = false
  }
}

function handleClassChange() {
  fetchRankings()
}

function handlePeriodChange() {
  if (period.value === 'week') {
    fetchRankings()
  } else if (period.value === 'month') {
    if (!selectedMonth.value) {
      // Default to current month
      const now = new Date()
      selectedMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    }
    fetchRankings()
  } else {
    fetchRankings()
  }
}

function getRankClass(rank: number): string {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return ''
}

function getChangeClass(change: number): string {
  if (change > 0) return 'change-positive'
  if (change < 0) return 'change-negative'
  return 'change-zero'
}

onMounted(async () => {
  await fetchClasses()
  await fetchAvailableWeeks()
  if (selectedClassId.value) {
    fetchRankings()
  }
})
</script>

<style scoped>
.rankings-container {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.filter-section {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-weight: 500;
  color: #666;
}

.table-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
}

.rank-gold {
  font-weight: bold;
  color: #ffd700;
}

.rank-silver {
  font-weight: bold;
  color: #c0c0c0;
}

.rank-bronze {
  font-weight: bold;
  color: #cd7f32;
}

.change-positive {
  color: #67c23a;
  font-weight: 500;
}

.change-negative {
  color: #f56c6c;
  font-weight: 500;
}

.change-zero {
  color: #909399;
}
</style>
