<template>
  <div class="student-manage">
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

        <div class="filter-actions">
          <el-tag v-if="selectedClass?.is_active" type="success" size="large">
            已激活
          </el-tag>
          <template v-else>
            <el-button type="primary" @click="showAddDialog">
              添加学生
            </el-button>
            <el-button type="success" @click="showImportDialog">
              导入学生
            </el-button>
          </template>
        </div>
      </div>
    </div>

    <el-card class="table-card" shadow="hover">
      <el-table
        :data="students"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="student_no" label="学号" width="150" />
        <el-table-column prop="name" label="姓名" width="150" />
        <el-table-column prop="current_score" label="当前积分" width="120">
          <template #default="{ row }">
            <span
              :style="{
                color: row.current_score >= 0 ? '#22c55e' : '#ef4444',
                fontWeight: 'bold'
              }"
            >
              {{ row.current_score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container" v-if="students.length > 0">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="pagination.total"
          :page-size="pagination.pageSize"
          :current-page="pagination.page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑学生' : '添加学生'"
      width="400px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="学生姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="学生学号" prop="student_no">
          <el-input v-model="form.student_no" placeholder="请输入学生学号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- Import Dialog -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入学生"
      width="500px"
    >
      <div class="import-content">
        <div class="template-download">
          <el-button type="success" @click="downloadTemplate">
            <el-icon><Download /></el-icon>
            下载导入模板
          </el-button>
        </div>
        <el-upload
          ref="uploadRef"
          class="upload-demo"
          drag
          :action="importUrl"
          :headers="uploadHeaders"
          :data="{ class_id: selectedClassId }"
          :limit="1"
          accept=".xlsx,.xls"
          :auto-upload="false"
          :on-success="handleImportSuccess"
          :on-error="handleImportError"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">只能上传 xlsx 文件</div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImport" :loading="importing">
          导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Download } from '@element-plus/icons-vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

interface ClassItem {
  id: number
  name: string
  is_active: boolean
}

interface StudentItem {
  id: number
  name: string
  student_no: string
  current_score: number
}

const authStore = useAuthStore()

const classes = ref<ClassItem[]>([])
const students = ref<StudentItem[]>([])
const loading = ref(false)
const selectedClassId = ref<number | undefined>()

const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const importing = ref(false)
const formRef = ref()

const editingId = ref<number | undefined>()

const form = reactive({
  name: '',
  student_no: ''
})

const rules = {
  name: [{ required: true, message: '请输入学生姓名', trigger: 'blur' }],
  student_no: [{ required: true, message: '请输入学生学号', trigger: 'blur' }]
}

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const uploadRef = ref()

const importUrl = '/api/students/import'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${authStore.token}`
}))

const selectedClass = computed(() =>
  classes.value.find(cls => cls.id === selectedClassId.value)
)

onMounted(async () => {
  await fetchClasses()
})

async function fetchClasses() {
  try {
    const response = await api.get('/classes')
    classes.value = response.data
  } catch (err) {
    ElMessage.error('获取班级列表失败')
  }
}

async function onClassChange() {
  pagination.page = 1
  await fetchStudents()
}

async function fetchStudents() {
  if (!selectedClassId.value) return

  loading.value = true
  try {
    const response = await api.get('/students', {
      params: {
        class_id: selectedClassId.value,
        page: pagination.page,
        page_size: pagination.pageSize
      }
    })
    students.value = response.data.items || response.data
    pagination.total = response.data.total || students.value.length
  } catch (err) {
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

function openEditDialog(student: StudentItem) {
  isEditing.value = true
  editingId.value = student.id
  form.name = student.name
  form.student_no = student.student_no
  dialogVisible.value = true
}

function showAddDialog() {
  isEditing.value = false
  editingId.value = undefined
  form.name = ''
  form.student_no = ''
  dialogVisible.value = true
}

function showImportDialog() {
  importDialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditing.value && editingId.value) {
        await api.put(`/students/${editingId.value}`, {
          name: form.name,
          student_no: form.student_no
        })
        ElMessage.success('更新成功')
      } else {
        await api.post('/students', {
          name: form.name,
          student_no: form.student_no,
          class_id: selectedClassId.value
        })
        ElMessage.success('添加成功')
      }
      dialogVisible.value = false
      await fetchStudents()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(student: StudentItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生「${student.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.delete(`/students/${student.id}`)
    ElMessage.success('删除成功')
    await fetchStudents()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

async function handleImport() {
  if (!uploadRef.value) return

  uploadRef.value.submit()
}

async function downloadTemplate() {
  try {
    const response = await api.get('/students/template', {
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'student_import_template.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    ElMessage.error('下载模板失败')
  }
}

function handleImportSuccess(response: any) {
  ElMessage.success('导入成功')
  importDialogVisible.value = false
  uploadRef.value?.clearFiles()
  fetchStudents()
}

function handleImportError(err: any) {
  ElMessage.error(err.response?.data?.detail || '导入失败')
}

function handlePageChange(page: number) {
  pagination.page = page
  fetchStudents()
}
</script>

<style scoped>
.student-manage {
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
  align-items: center;
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

.filter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.import-content {
  padding: 20px 0;
}

.template-download {
  margin-bottom: 20px;
}

.upload-demo {
  text-align: center;
}

.el-icon--upload {
  font-size: 67px;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
}
</style>
