<template>
  <div class="score-details">
    <h2>分值明细</h2>

    <!-- Filter Section -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="班级">
          <el-select
            v-model="filterForm.class_id"
            placeholder="请选择班级"
            clearable
            style="width: 200px"
            @change="handleClassChange"
          >
            <el-option
              v-for="cls in classList"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="filterForm.start"
            type="datetime"
            placeholder="选择开始日期"
            style="width: 200px"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="filterForm.end"
            type="datetime"
            placeholder="选择结束日期"
            style="width: 200px"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table Section -->
    <el-card class="table-card" shadow="hover">
      <el-table :data="scoreList" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="student_name" label="学生姓名" width="120" />
        <el-table-column prop="student_no" label="学号" width="100" />
        <el-table-column label="分值" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.value >= 0 ? '#22c55e' : '#ef4444', fontWeight: 'bold' }">
              {{ row.value >= 0 ? '+' : '' }}{{ row.value }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="150" />
        <el-table-column prop="course_name" label="课程" width="120" />
        <el-table-column prop="teacher_name" label="操作教师" width="120" />
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.score_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface ClassItem {
  id: number
  name: string
}

interface ScoreDetail {
  id: number
  student_id: number
  student_name: string
  student_no: string
  value: number
  reason: string
  course_name: string
  teacher_name: string
  score_at: string
}

const classList = ref<ClassItem[]>([])
const scoreList = ref<ScoreDetail[]>([])
const loading = ref(false)

const filterForm = reactive({
  class_id: null as number | null,
  start: '',
  end: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

async function fetchClasses() {
  try {
    const response = await api.get('/teacher/classes')
    classList.value = response.data
    // 默认选择第一个班级
    if (classList.value.length > 0) {
      filterForm.class_id = classList.value[0].id
      fetchScoreDetails()
    }
  } catch (error: any) {
    ElMessage.error('获取班级列表失败')
  }
}

async function fetchScoreDetails() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (filterForm.class_id) params.class_id = filterForm.class_id
    if (filterForm.start) params.start = filterForm.start
    if (filterForm.end) params.end = filterForm.end
    params.page = pagination.page
    params.page_size = pagination.pageSize

    const response = await api.get('/scores', { params })
    scoreList.value = response.data

    // Extract total from response header or set based on data length
    pagination.total = response.data.length
  } catch (error: any) {
    ElMessage.error('获取分值明细失败')
  } finally {
    loading.value = false
  }
}

function handleClassChange() {
  // Optionally handle class change
}

function handleSearch() {
  pagination.page = 1
  fetchScoreDetails()
}

function handleReset() {
  filterForm.class_id = null
  filterForm.start = ''
  filterForm.end = ''
  pagination.page = 1
  fetchScoreDetails()
}

function handleSizeChange() {
  pagination.page = 1
  fetchScoreDetails()
}

function handlePageChange() {
  fetchScoreDetails()
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  fetchClasses()
})
</script>

<style scoped>
.score-details {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
