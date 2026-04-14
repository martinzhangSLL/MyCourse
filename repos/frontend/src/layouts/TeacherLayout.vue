<template>
  <el-container class="teacher-layout">
    <el-aside width="220px">
      <TeacherSidebar />
    </el-aside>
    <el-container>
      <el-header class="teacher-header">
        <span class="title">{{ authStore.user?.name || '教师' }} - 初中班级积分管理系统</span>
        <el-button @click="handleLogout" type="danger" size="small">退出</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import TeacherSidebar from '@/components/TeacherSidebar.vue'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.clearAuth()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.teacher-layout {
  height: 100vh;
}

.teacher-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}
</style>
