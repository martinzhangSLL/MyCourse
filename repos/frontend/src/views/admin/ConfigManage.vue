<template>
  <div class="config-manage-container">
    <h2 class="page-title">系统配置</h2>

    <div class="config-content">
      <el-tabs v-model="activeTab" class="config-tabs">
        <!-- Tab 1: 学期设置 -->
        <el-tab-pane label="学期设置" name="terms">
          <div class="tab-header">
            <el-button type="primary" @click="openTermDialog()">
              新增学期
            </el-button>
          </div>

          <el-table :data="terms" stripe v-loading="termsLoading">
            <el-table-column prop="name" label="学期名称" />
            <el-table-column prop="school_year" label="学年" width="150" align="center" />
            <el-table-column prop="start_date" label="开始日期" width="150" align="center" />
            <el-table-column prop="end_date" label="结束日期" width="150" align="center" />
            <el-table-column label="操作" width="200" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="openTermDialog(row)">
                  编辑
                </el-button>
                <el-button type="danger" link @click="deleteTerm(row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-dialog
            v-model="termDialogVisible"
            :title="editingTerm ? '编辑学期' : '新增学期'"
            width="500px"
            @close="resetTermForm"
          >
            <el-form :model="termForm" :rules="termRules" ref="termFormRef" label-width="90px">
              <el-form-item label="学期名称" prop="name">
                <el-input v-model="termForm.name" placeholder="如：2024春季学期" />
              </el-form-item>
              <el-form-item label="学年" prop="school_year">
                <el-input v-model="termForm.school_year" placeholder="如：2023-2024" />
              </el-form-item>
              <el-form-item label="开始日期" prop="start_date">
                <el-date-picker
                  v-model="termForm.start_date"
                  type="date"
                  placeholder="选择开始日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="结束日期" prop="end_date">
                <el-date-picker
                  v-model="termForm.end_date"
                  type="date"
                  placeholder="选择结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-form>
            <template #footer>
              <el-button @click="termDialogVisible = false">取消</el-button>
              <el-button type="primary" @click="submitTerm" :loading="termSubmitting">
                确定
              </el-button>
            </template>
          </el-dialog>
        </el-tab-pane>

        <!-- Tab 2: 积分原因 -->
        <el-tab-pane label="积分原因" name="reasons">
          <div class="reasons-section">
            <div class="add-reason">
              <el-input
                v-model="newReason"
                placeholder="输入新的积分原因"
                style="width: 300px"
                @keyup.enter="addReason"
              />
              <el-button type="primary" @click="addReason" :disabled="!newReason.trim()">
                添加
              </el-button>
            </div>

            <div class="reasons-list" v-loading="reasonsLoading">
              <el-tag
                v-for="reason in reasons"
                :key="reason"
                closable
                @close="deleteReason(reason)"
                type="success"
                class="reason-tag"
              >
                {{ reason }}
              </el-tag>
              <div v-if="!reasonsLoading && reasons.length === 0" class="empty-state">
                暂无积分原因配置
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 3: 确认码 -->
        <el-tab-pane label="确认码" name="codes">
          <div class="codes-section" v-loading="codesLoading">
            <el-form :model="codesForm" label-width="140px" style="max-width: 500px">
              <el-form-item label="结算确认码">
                <el-input
                  v-model="codesForm.settlement_code"
                  placeholder="请输入结算确认码"
                  type="password"
                  show-password
                />
              </el-form-item>
              <el-form-item label="初始化确认码">
                <el-input
                  v-model="codesForm.init_code"
                  placeholder="请输入初始化确认码"
                  type="password"
                  show-password
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveCodes" :loading="codesSubmitting">
                  保存确认码
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import api from '@/api'

const activeTab = ref('terms')

// ============ Terms Tab ============
interface Term {
  id: number
  name: string
  school_year: string
  start_date: string
  end_date: string
}

const terms = ref<Term[]>([])
const termsLoading = ref(false)
const termDialogVisible = ref(false)
const editingTerm = ref<Term | null>(null)
const termSubmitting = ref(false)
const termFormRef = ref<FormInstance>()

const termForm = reactive({
  name: '',
  school_year: '',
  start_date: '',
  end_date: ''
})

const termRules: FormRules = {
  name: [{ required: true, message: '请输入学期名称', trigger: 'blur' }],
  school_year: [{ required: true, message: '请输入学年', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }]
}

async function fetchTerms() {
  termsLoading.value = true
  try {
    const response = await api.get('/config/terms')
    terms.value = response.data
  } catch (error) {
    ElMessage.error('获取学期列表失败')
  } finally {
    termsLoading.value = false
  }
}

function openTermDialog(term?: Term) {
  if (term) {
    editingTerm.value = term
    termForm.name = term.name
    termForm.school_year = term.school_year
    termForm.start_date = term.start_date
    termForm.end_date = term.end_date
  } else {
    editingTerm.value = null
    termForm.name = ''
    termForm.school_year = ''
    termForm.start_date = ''
    termForm.end_date = ''
  }
  termDialogVisible.value = true
}

async function submitTerm() {
  if (!termFormRef.value) return

  try {
    await termFormRef.value.validate()
  } catch {
    return
  }

  termSubmitting.value = true
  try {
    if (editingTerm.value) {
      await api.put(`/config/terms/${editingTerm.value.id}`, termForm)
      ElMessage.success('更新成功')
    } else {
      await api.post('/config/terms', termForm)
      ElMessage.success('新增成功')
    }
    termDialogVisible.value = false
    await fetchTerms()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    termSubmitting.value = false
  }
}

async function deleteTerm(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该学期吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.delete(`/config/terms/${id}`)
    ElMessage.success('删除成功')
    await fetchTerms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

function resetTermForm() {
  termForm.name = ''
  termForm.school_year = ''
  termForm.start_date = ''
  termForm.end_date = ''
  termFormRef.value?.resetFields()
}

// ============ Reasons Tab ============
const reasons = ref<string[]>([])
const reasonsLoading = ref(false)
const newReason = ref('')

async function fetchReasons() {
  reasonsLoading.value = true
  try {
    const response = await api.get('/config/reasons')
    reasons.value = response.data.reasons || []
  } catch (error) {
    ElMessage.error('获取积分原因失败')
  } finally {
    reasonsLoading.value = false
  }
}

async function addReason() {
  const reason = newReason.value.trim()
  if (!reason) return

  if (reasons.value.includes(reason)) {
    ElMessage.warning('该原因已存在')
    return
  }

  const newReasons = [...reasons.value, reason]
  try {
    await api.put('/config/reasons', { reasons: newReasons })
    reasons.value = newReasons
    newReason.value = ''
    ElMessage.success('添加成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

async function deleteReason(reason: string) {
  try {
    await ElMessageBox.confirm(`确定要删除原因 "${reason}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const newReasons = reasons.value.filter(r => r !== reason)
    await api.put('/config/reasons', { reasons: newReasons })
    reasons.value = newReasons
    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// ============ Codes Tab ============
const codesForm = reactive({
  settlement_code: '',
  init_code: ''
})
const codesLoading = ref(false)
const codesSubmitting = ref(false)

async function fetchCodes() {
  codesLoading.value = true
  try {
    const response = await api.get('/config/codes')
    codesForm.settlement_code = response.data.settlement_code || ''
    codesForm.init_code = response.data.init_code || ''
  } catch (error) {
    ElMessage.error('获取确认码失败')
  } finally {
    codesLoading.value = false
  }
}

async function saveCodes() {
  codesSubmitting.value = true
  try {
    await api.put('/config/codes', {
      settlement_code: codesForm.settlement_code,
      init_code: codesForm.init_code
    })
    ElMessage.success('保存成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    codesSubmitting.value = false
  }
}

// ============ Init ============
onMounted(() => {
  fetchTerms()
})
</script>

<style scoped>
.config-manage-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 20px;
}

.config-content {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  padding: 20px;
}

.config-tabs {
  margin-top: 0;
}

.tab-header {
  margin-bottom: 16px;
}

.reasons-section {
  padding: 10px 0;
}

.add-reason {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.reasons-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  min-height: 100px;
}

.reason-tag {
  font-size: 14px;
  padding: 8px 12px;
}

.codes-section {
  padding: 20px 0;
  min-height: 200px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-text-secondary);
  font-size: 16px;
  width: 100%;
}
</style>
