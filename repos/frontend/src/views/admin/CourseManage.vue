<template>
  <div class="course-manage-container">
    <div class="page-header">
      <h2 class="page-title">课程管理</h2>
      <el-button type="primary" @click="openAddDialog">
        新增课程
      </el-button>
    </div>

    <div class="table-section">
      <el-table :data="courses" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="100" align="center" />
        <el-table-column prop="name" label="课程名称" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && courses.length === 0" class="empty-state">
        暂无课程数据
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑课程' : '新增课程'"
      width="400px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="课程名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入课程名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import api from '@/api'

interface Course {
  id: number
  name: string
}

const courses = ref<Course[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入课程名称', trigger: 'blur' },
    { min: 1, max: 50, message: '课程名称长度为 1-50 个字符', trigger: 'blur' }
  ]
}

async function fetchCourses() {
  loading.value = true
  try {
    const response = await api.get('/courses')
    courses.value = response.data
  } catch (error) {
    ElMessage.error('获取课程列表失败')
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  isEditing.value = false
  editingId.value = null
  dialogVisible.value = true
}

function openEditDialog(course: Course) {
  isEditing.value = true
  editingId.value = course.id
  form.name = course.name
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEditing.value && editingId.value !== null) {
      await api.put(`/courses/${editingId.value}`, { name: form.name })
      ElMessage.success('更新成功')
    } else {
      await api.post('/courses', { name: form.name })
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    await fetchCourses()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm(
      '确定要删除该课程吗？删除后无法恢复。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await api.delete(`/courses/${id}`)
    ElMessage.success('删除成功')
    await fetchCourses()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

function resetForm() {
  form.name = ''
  formRef.value?.resetFields()
}

onMounted(() => {
  fetchCourses()
})
</script>

<style scoped>
.course-manage-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.table-section {
  background: var(--color-surface);
  padding: 20px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-text-secondary);
  font-size: 16px;
}
</style>
