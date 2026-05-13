<template>
  <div class="admin-sidebar">
    <div class="sidebar-header">
      <h2>管理菜单</h2>
    </div>
    <el-menu
      :default-active="$route.path"
      router
      background-color="#16a34a"
      text-color="#ffffff"
      active-text-color="#ffffff"
    >
      <el-menu-item index="/admin/classes">
        <span>班级管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/students">
        <span>学生管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/teachers">
        <span>教师管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/courses">
        <span>课程管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/config">
        <span>配置管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/ranks">
        <span>段位管理</span>
      </el-menu-item>
      <el-menu-item index="/admin/settlement">
        <span>结算/初始化</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.admin-sidebar {
  height: 100%;
  background-color: #16a34a;
}

.sidebar-header {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-header h2 {
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-menu-item:hover) {
  background-color: #22c55e !important;
}

:deep(.el-menu-item.is-active) {
  background-color: #22c55e !important;
}
</style>
