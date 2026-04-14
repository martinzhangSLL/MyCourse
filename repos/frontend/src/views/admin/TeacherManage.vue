<template>
  <div class="teacher-manage-page">
    <div class="page-header">
      <h2>教师管理</h2>
      <el-button type="primary" @click="openAddDialog">
        新增教师
      </el-button>
    </div>

    <div class="table-container">
      <el-table :data="teachers" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="教师姓名" />
        <el-table-column prop="username" label="账号" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑教师' : '新增教师'"
      width="400px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="教师姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入教师姓名" />
        </el-form-item>
        <el-form-item :label="isEdit ? '密码' : '密码'" :prop="isEdit ? '' : 'password'">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import api from '@/api'

interface Teacher {
  id: number
  name: string
  username: string
}

const teachers = ref<Teacher[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  password: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入教师姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

onMounted(async () => {
  await fetchTeachers()
})

async function fetchTeachers() {
  loading.value = true
  try {
    const response = await api.get('/teachers')
    teachers.value = response.data
  } catch (err) {
    console.error('Failed to fetch teachers:', err)
    ElMessage.error('获取教师列表失败')
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  isEdit.value = false
  editingId.value = null
  dialogVisible.value = true
}

function openEditDialog(teacher: Teacher) {
  isEdit.value = true
  editingId.value = teacher.id
  form.name = teacher.name
  form.password = ''
  dialogVisible.value = true
}

function resetForm() {
  form.name = ''
  form.password = ''
  formRef.value?.resetFields()
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true

    try {
      if (isEdit.value && editingId.value) {
        const payload: { name: string; password?: string } = { name: form.name }
        if (form.password) {
          payload.password = form.password
        }
        await api.put(`/teachers/${editingId.value}`, payload)
        ElMessage.success('教师信息更新成功')
      } else {
        await api.post('/teachers', {
          name: form.name,
          password: form.password
        })
        ElMessage.success('新增教师成功')
      }

      dialogVisible.value = false
      await fetchTeachers()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(teacher: Teacher) {
  try {
    await ElMessageBox.confirm(
      `确定要删除教师「${teacher.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.delete(`/teachers/${teacher.id}`)
    ElMessage.success('删除成功')
    await fetchTeachers()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}
</script>

<style scoped>
.teacher-manage-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: var(--color-text);
}

.table-container {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: 20px;
  box-shadow: var(--shadow);
}
</style>
