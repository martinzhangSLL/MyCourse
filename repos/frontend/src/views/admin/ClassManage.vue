<template>
  <div class="class-manage-page">
    <div class="page-header">
      <h2 class="page-title">班级管理</h2>
      <el-button type="primary" @click="openAddDialog">
        新增班级
      </el-button>
    </div>

    <div class="table-container">
      <el-table :data="classes" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="班级名称" min-width="150" />
        <el-table-column prop="code" label="班级编号" width="150" />
        <el-table-column label="关联教师" min-width="200">
          <template #default="{ row }">
            <span v-if="row.teachers && row.teachers.length">
              {{ row.teachers.map((t: any) => t.name).join(', ') }}
            </span>
            <span v-else class="text-muted">暂无</span>
          </template>
        </el-table-column>
        <el-table-column label="关联课程" min-width="200">
          <template #default="{ row }">
            <span v-if="row.courses && row.courses.length">
              {{ row.courses.map((c: any) => c.name).join(', ') }}
            </span>
            <span v-else class="text-muted">暂无</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success">已激活</el-tag>
            <el-tag v-else type="info">未激活</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" align="center">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              type="success"
              size="small"
              @click="handleActivate(row)"
            >
              激活
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑班级' : '新增班级'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" label-width="100px" ref="formRef">
        <el-form-item label="班级名称" required>
          <el-input v-model="form.name" placeholder="请输入班级名称" />
        </el-form-item>
        <el-form-item label="班级编号" required>
          <el-input v-model="form.code" placeholder="请输入班级编号" />
        </el-form-item>
        <el-form-item label="关联教师">
          <el-select
            v-model="form.teacherIds"
            multiple
            placeholder="请选择关联教师"
            style="width: 100%"
          >
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联课程">
          <el-select
            v-model="form.courseIds"
            multiple
            placeholder="请选择关联课程"
            style="width: 100%"
          >
            <el-option
              v-for="course in courses"
              :key="course.id"
              :label="course.name"
              :value="course.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

interface ClassItem {
  id: number
  name: string
  code: string
  is_active: boolean
  teachers: { id: number; name: string }[]
  courses: { id: number; name: string }[]
}

interface Teacher {
  id: number
  name: string
}

interface Course {
  id: number
  name: string
}

const classes = ref<ClassItem[]>([])
const teachers = ref<Teacher[]>([])
const courses = ref<Course[]>([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const currentClassId = ref<number | null>(null)

const form = reactive({
  name: '',
  code: '',
  teacherIds: [] as number[],
  courseIds: [] as number[]
})

const formRef = ref()

onMounted(async () => {
  await Promise.all([
    fetchClasses(),
    fetchTeachers(),
    fetchCourses()
  ])
})

async function fetchClasses() {
  try {
    const response = await api.get('/classes')
    classes.value = response.data
  } catch (err) {
    console.error('Failed to fetch classes:', err)
    ElMessage.error('获取班级列表失败')
  }
}

async function fetchTeachers() {
  try {
    const response = await api.get('/teachers')
    teachers.value = response.data
  } catch (err) {
    console.error('Failed to fetch teachers:', err)
  }
}

async function fetchCourses() {
  try {
    const response = await api.get('/courses')
    courses.value = response.data
  } catch (err) {
    console.error('Failed to fetch courses:', err)
  }
}

function openAddDialog() {
  isEdit.value = false
  dialogVisible.value = true
}

function openEditDialog(row: ClassItem) {
  isEdit.value = true
  currentClassId.value = row.id
  form.name = row.name
  form.code = row.code
  form.teacherIds = row.teachers?.map((t: any) => t.id) || []
  form.courseIds = row.courses?.map((c: any) => c.id) || []
  dialogVisible.value = true
}

function resetForm() {
  form.name = ''
  form.code = ''
  form.teacherIds = []
  form.courseIds = []
  currentClassId.value = null
}

async function handleSubmit() {
  if (!form.name || !form.code) {
    ElMessage.warning('请填写班级名称和编号')
    return
  }

  submitLoading.value = true

  try {
    const payload = {
      name: form.name,
      code: form.code,
      teacher_ids: form.teacherIds,
      course_ids: form.courseIds
    }

    if (isEdit.value && currentClassId.value) {
      await api.put(`/classes/${currentClassId.value}`, payload)
      ElMessage.success('编辑成功')
    } else {
      await api.post('/classes', payload)
      ElMessage.success('新增成功')
    }

    dialogVisible.value = false
    await fetchClasses()
  } catch (err) {
    console.error('Submit failed:', err)
    ElMessage.error(isEdit.value ? '编辑失败' : '新增失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleActivate(row: ClassItem) {
  try {
    await ElMessageBox.confirm('确认激活该班级？激活后即可使用。', '激活确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.put(`/classes/${row.id}/activate`)
    ElMessage.success('激活成功')
    await fetchClasses()
  } catch (err: any) {
    if (err !== 'cancel') {
      console.error('Activate failed:', err)
      ElMessage.error('激活失败')
    }
  }
}

async function handleDelete(row: ClassItem) {
  try {
    await ElMessageBox.confirm('确认删除该班级？此操作不可恢复。', '删除确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.delete(`/classes/${row.id}`)
    ElMessage.success('删除成功')
    await fetchClasses()
  } catch (err: any) {
    if (err !== 'cancel') {
      console.error('Delete failed:', err)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.class-manage-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  color: var(--color-text);
  font-size: 20px;
  font-weight: 600;
}

.table-container {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.text-muted {
  color: var(--color-text-secondary);
  font-size: 14px;
}

:deep(.el-table) {
  --el-table-border-color: var(--color-border);
  --el-table-header-bg-color: #f8fafc;
}

:deep(.el-button--success) {
  --el-button-bg-color: #22c55e;
  --el-button-border-color: #22c55e;
  --el-button-hover-bg-color: #16a34a;
  --el-button-hover-border-color: #16a34a;
}

:deep(.el-tag--success) {
  --el-tag-bg-color: #86efac;
  --el-tag-border-color: #86efac;
  --el-tag-text-color: #15803d;
}
</style>
