<template>
  <div class="settlement-page">
    <div class="page-header">
      <h1>结算与初始化</h1>
    </div>

    <el-tabs v-model="activeTab" class="settlement-tabs">
      <!-- Tab 1: Settlement -->
      <el-tab-pane label="结算" name="settlement">
        <div class="tab-content">
          <div class="form-section">
            <div class="form-item">
              <span class="form-label">选择班级：</span>
              <el-select
                v-model="selectedClassId"
                placeholder="请选择班级"
                style="width: 240px"
              >
                <el-option
                  v-for="cls in classes"
                  :key="cls.id"
                  :label="cls.name"
                  :value="cls.id"
                />
              </el-select>
            </div>

            <div class="form-actions">
              <el-button
                type="primary"
                size="large"
                :disabled="!selectedClassId"
                @click="onSettleClick"
              >
                结算
              </el-button>
            </div>
          </div>

          <div class="info-note">
            <p>结算将下载班级学生积分Excel，并清零所有积分记录</p>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: Initialization -->
      <el-tab-pane label="积分初始化" name="initialization">
        <div class="tab-content">
          <div class="form-section">
            <div class="form-item">
              <span class="form-label">选择班级：</span>
              <el-select
                v-model="initClassId"
                placeholder="请选择班级"
                style="width: 240px"
              >
                <el-option
                  v-for="cls in classes"
                  :key="cls.id"
                  :label="cls.name"
                  :value="cls.id"
                />
              </el-select>
            </div>

            <div class="form-item">
              <span class="form-label">上传文件：</span>
              <el-upload
                ref="uploadRef"
                class="excel-uploader"
                :auto-upload="false"
                :limit="1"
                accept=".xlsx,.xls"
                :on-change="onFileChange"
                :on-remove="onFileRemove"
              >
                <template #trigger>
                  <el-button type="primary" plain>
                    选择Excel文件
                  </el-button>
                </template>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .xlsx, .xls 格式，包含姓名、学号、初始积分
                  </div>
                </template>
              </el-upload>
            </div>

            <div class="form-actions">
              <el-button
                type="success"
                size="large"
                :disabled="!canInitialize"
                :loading="initializing"
                @click="onInitializeClick"
              >
                执行初始化
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Confirmation Code Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="420px"
      :close-on-click-modal="false"
    >
      <div class="dialog-content">
        <p class="dialog-message">{{ dialogMessage }}</p>
        <el-input
          v-model="confirmCode"
          type="password"
          placeholder="请输入确认码"
          size="large"
          @keyup.enter="onDialogConfirm"
        />
        <p v-if="codeError" class="code-error">{{ codeError }}</p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="onDialogCancel">取消</el-button>
          <el-button type="primary" @click="onDialogConfirm" :loading="dialogLoading">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import api from '@/api'

interface ClassItem {
  id: number
  name: string
}

const activeTab = ref('settlement')
const classes = ref<ClassItem[]>([])

// Settlement state
const selectedClassId = ref<number | undefined>()

// Initialization state
const initClassId = ref<number | undefined>()
const uploadRef = ref()
const selectedFile = ref<UploadFile | null>(null)

// Dialog state
const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const confirmCode = ref('')
const codeError = ref('')
const dialogLoading = ref(false)
const initializing = ref(false)

// Dialog action type: 'settle' | 'initialize'
const dialogAction = ref<'settle' | 'initialize'>('settle')

const canInitialize = computed(() => {
  return initClassId.value && selectedFile.value
})

onMounted(async () => {
  await fetchClasses()
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

function onSettleClick() {
  if (!selectedClassId.value) {
    ElMessage.warning('请选择班级')
    return
  }
  dialogTitle.value = '结算确认'
  dialogMessage.value = '确定要进行结算吗？这将下载Excel并清零积分。'
  confirmCode.value = ''
  codeError.value = ''
  dialogAction.value = 'settle'
  dialogVisible.value = true
  fetchConfigCode()
}

function onInitializeClick() {
  if (!initClassId.value) {
    ElMessage.warning('请选择班级')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请上传Excel文件')
    return
  }
  dialogTitle.value = '初始化确认'
  dialogMessage.value = '确定要执行积分初始化吗？这将覆盖班级现有积分。'
  confirmCode.value = ''
  codeError.value = ''
  dialogAction.value = 'initialize'
  dialogVisible.value = true
  fetchConfigCode()
}

async function fetchConfigCode() {
  try {
    const response = await api.get('/config/codes')
    // Pre-fill the code if available
    if (response.data?.value) {
      confirmCode.value = response.data.value
    }
  } catch (err) {
    // Silently fail, user can still enter code manually
    console.error('Failed to fetch config code:', err)
  }
}

function onFileChange(file: UploadFile) {
  selectedFile.value = file
}

function onFileRemove() {
  selectedFile.value = null
}

async function onDialogConfirm() {
  if (!confirmCode.value) {
    codeError.value = '请输入确认码'
    return
  }

  codeError.value = ''
  dialogLoading.value = true

  try {
    if (dialogAction.value === 'settle') {
      await handleSettlement()
    } else {
      await handleInitialization()
    }
    dialogVisible.value = false
  } catch (err: any) {
    codeError.value = err.response?.data?.detail || '操作失败，请检查确认码'
  } finally {
    dialogLoading.value = false
  }
}

function onDialogCancel() {
  dialogVisible.value = false
  confirmCode.value = ''
  codeError.value = ''
}

async function handleSettlement() {
  if (!selectedClassId.value || !confirmCode.value) return

  try {
    const response = await api.post(
      `/settlement?class_id=${selectedClassId.value}&code=${confirmCode.value}`,
      {},
      { responseType: 'blob' }
    )

    // Extract filename from content-disposition header
    const contentDisposition = response.headers['content-disposition']
    let filename = 'settlement.xlsx'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '')
      }
    }

    // Create blob and download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('结算成功，Excel已下载')
    selectedClassId.value = undefined
  } catch (err: any) {
    if (err.response?.status === 400) {
      const errorText = await err.response.data.text()
      const errorData = JSON.parse(errorText)
      throw new Error(errorData.detail || '结算失败')
    }
    throw err
  }
}

async function handleInitialization() {
  if (!initClassId.value || !selectedFile.value || !confirmCode.value) return

  const file = selectedFile.value.raw
  if (!file) {
    ElMessage.error('文件无效')
    return
  }

  initializing.value = true

  try {
    const formData = new FormData()
    formData.append('file', file)

    await api.post(
      `/initialization?class_id=${initClassId.value}&code=${confirmCode.value}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    ElMessage.success('初始化成功')
    dialogVisible.value = false
    initClassId.value = undefined
    selectedFile.value = null
    uploadRef.value?.clearFiles()
  } catch (err: any) {
    throw new Error(err.response?.data?.detail || '初始化失败')
  } finally {
    initializing.value = false
  }
}
</script>

<style scoped>
.settlement-page {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.settlement-tabs {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: 20px;
  box-shadow: var(--shadow);
}

.tab-content {
  padding: 20px 0;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-label {
  font-weight: 500;
  color: var(--color-text);
  min-width: 80px;
}

.form-actions {
  margin-top: 12px;
  padding-left: 92px;
}

.info-note {
  margin-top: 24px;
  padding: 16px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: var(--border-radius);
  border-left: 4px solid var(--color-primary);
}

.info-note p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.excel-uploader {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.el-upload__tip {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.dialog-content {
  padding: 10px 0;
}

.dialog-message {
  margin: 0 0 20px 0;
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.6;
}

.code-error {
  margin: 12px 0 0 0;
  color: var(--color-score-minus, #ef4444);
  font-size: 13px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
