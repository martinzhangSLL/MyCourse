<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">初中班级积分管理系统</h1>

      <div class="role-tabs">
        <button
          :class="{ active: form.role === 'admin' }"
          @click="form.role = 'admin'"
        >
          管理员
        </button>
        <button
          :class="{ active: form.role === 'teacher' }"
          @click="form.role = 'teacher'"
        >
          教师
        </button>
      </div>

      <input
        v-model="form.username"
        type="text"
        placeholder="账号"
        class="large-input"
      />
      <input
        v-model="form.password"
        type="password"
        placeholder="密码"
        class="large-input"
        @keyup.enter="handleLogin"
      />

      <p v-if="error" class="error">{{ error }}</p>

      <button @click="handleLogin" class="login-btn" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
  role: 'admin'
})

const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true

  try {
    const response = await api.post('/auth/login', {
      username: form.username,
      password: form.password,
      role: form.role
    })

    const { token, user } = response.data

    authStore.setAuth(token, {
      id: user.id,
      username: user.name,
      role: user.role
    })

    if (user.role === 'admin') {
      router.push({ name: 'Admin' })
    } else {
      router.push({ name: 'Teacher' })
    }
  } catch (err: any) {
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail
    } else {
      error.value = '登录失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--color-bg);
}

.login-box {
  background: var(--color-surface);
  padding: 40px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.title {
  color: var(--color-primary);
  font-size: 28px;
  margin-bottom: 30px;
  font-weight: 600;
}

.role-tabs {
  display: flex;
  margin-bottom: 24px;
  gap: 8px;
}

.role-tabs button {
  flex: 1;
  padding: 12px;
  border: 2px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 16px;
  cursor: pointer;
  border-radius: var(--border-radius);
  transition: all 0.2s;
}

.role-tabs button.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.role-tabs button:hover:not(.active) {
  border-color: var(--color-primary);
}

.large-input {
  width: 100%;
  padding: 14px 16px;
  margin-bottom: 16px;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s;
}

.large-input:focus {
  border-color: var(--color-primary);
}

.error {
  color: var(--color-score-minus);
  margin-bottom: 16px;
  font-size: 14px;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.login-btn:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
