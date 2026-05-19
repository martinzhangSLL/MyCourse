<template>
  <div class="rank-manage-page">
    <div class="page-header">
      <h2 class="page-title">段位管理</h2>
      <el-button type="primary" @click="openAddDialog">
        新增段位
      </el-button>
    </div>

    <div class="table-container">
      <el-table :data="ranks" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="display_order" label="序号" width="80" />
        <el-table-column prop="name" label="段位名称" width="150" />
        <el-table-column label="积分区间" width="200">
          <template #default="{ row }">
            {{ row.min_score }}{{ row.max_score ? ' - ' + row.max_score : '+' }}
          </template>
        </el-table-column>
        <el-table-column prop="image_url" label="图片路径" min-width="200" />
        <el-table-column label="预览" width="100">
          <template #default="{ row }">
            <img
              v-if="row.image_url"
              :src="row.image_url"
              style="width:40px;height:40px;object-fit:contain;"
            />
            <span v-else class="text-muted">无</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
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
      :title="isEdit ? '编辑段位' : '新增段位'"
      width="500px"
      @close="resetForm"
    >
      <el-form :model="form" label-width="100px" ref="formRef">
        <el-form-item label="段位名称" required>
          <el-input v-model="form.name" placeholder="如：启灵境" />
        </el-form-item>
        <el-form-item label="最低积分">
          <el-input-number v-model="form.min_score" :min="0" />
        </el-form-item>
        <el-form-item label="最高积分">
          <el-input-number
            v-model="form.max_score"
            :min="0"
            placeholder="留空表示无上限"
          />
        </el-form-item>
        <el-form-item label="图片路径">
          <div class="upload-row">
            <el-input v-model="form.image_url" placeholder="/pics/xxx.png" style="flex: 1" />
            <el-upload
              :http-request="handleUpload"
              :show-file-list="false"
              accept="image/png,image/jpeg,image/gif"
            >
              <el-button type="primary" plain>上传图片</el-button>
            </el-upload>
          </div>
          <div class="image-preview" v-if="form.image_url">
            <img :src="form.image_url" alt="预览" />
          </div>
        </el-form-item>
        <el-form-item label="排序序号">
          <el-input-number v-model="form.display_order" :min="1" />
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

async function handleUpload(option) {
  const { file, onSuccess, onError } = option
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    form.image_url = response.data.url
    ElMessage.success('上传成功')
    onSuccess(response)
  } catch (err) {
    console.error('Upload failed:', err)
    ElMessage.error('上传失败')
    onError(err)
  }
}

interface RankItem {
  id: number
  name: string
  min_score: number
  max_score: number | null
  image_url: string
  display_order: number
}

const ranks = ref<RankItem[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const currentRankId = ref<number | null>(null)

const form = reactive({
  name: '',
  min_score: 0,
  max_score: null as number | null,
  image_url: '',
  display_order: 1
})

const formRef = ref()

onMounted(async () => {
  await fetchRanks()
})

async function fetchRanks() {
  loading.value = true
  try {
    const response = await api.get('/ranks')
    ranks.value = response.data
  } catch (err) {
    console.error('Failed to fetch ranks:', err)
    ElMessage.error('获取段位列表失败')
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  isEdit.value = false
  dialogVisible.value = true
}

function openEditDialog(row: RankItem) {
  isEdit.value = true
  currentRankId.value = row.id
  form.name = row.name
  form.min_score = row.min_score
  form.max_score = row.max_score
  form.image_url = row.image_url
  form.display_order = row.display_order
  dialogVisible.value = true
}

function resetForm() {
  form.name = ''
  form.min_score = 0
  form.max_score = null
  form.image_url = ''
  form.display_order = 1
  currentRankId.value = null
}

async function handleSubmit() {
  if (!form.name) {
    ElMessage.warning('请填写段位名称')
    return
  }

  submitLoading.value = true

  try {
    const payload = {
      name: form.name,
      min_score: form.min_score,
      max_score: form.max_score,
      image_url: form.image_url,
      display_order: form.display_order
    }

    if (isEdit.value && currentRankId.value !== null) {
      await api.put(`/ranks/${currentRankId.value}`, payload)
      ElMessage.success('编辑成功')
    } else {
      await api.post('/ranks', payload)
      ElMessage.success('新增成功')
    }

    dialogVisible.value = false
    await fetchRanks()
  } catch (err) {
    console.error('Submit failed:', err)
    ElMessage.error(isEdit.value ? '编辑失败' : '新增失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row: RankItem) {
  try {
    await ElMessageBox.confirm(
      `确定删除段位「${row.name}」吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.delete(`/ranks/${row.id}`)
    ElMessage.success('删除成功')
    await fetchRanks()
  } catch (err: any) {
    if (err !== 'cancel') {
      console.error('Delete failed:', err)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.rank-manage-page {
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

.upload-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.image-preview {
  margin-top: 10px;
}

.image-preview img {
  max-width: 100px;
  max-height: 100px;
  border-radius: 8px;
  border: 1px solid rgba(255, 215, 0, 0.3);
}
</style>