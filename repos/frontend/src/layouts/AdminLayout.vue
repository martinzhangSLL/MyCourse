<template>
  <el-container class="admin-layout">
    <el-aside width="220px">
      <AdminSidebar />
    </el-aside>
    <el-container>
      <el-header class="admin-header">
        <div class="header-left">
          <span class="system-title">初中班级积分管理系统 - 管理员</span>
        </div>
        <div class="header-right">
          <span class="admin-name">{{ authStore.user?.username }}</span>
          <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AdminSidebar from '@/components/AdminSidebar.vue'

const router = useRouter()
const authStore = useAuthStore()

function handleLogout() {
  authStore.clearAuth()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
}

.system-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-name {
  color: #6b7280;
  font-size: 14px;
}

.admin-main {
  background-color: #f0fdf4;
  padding: 24px;
  overflow-y: auto;
}
</style>
