<template>
  <el-menu
    :default-active="$route.path"
    router
    background-color="#16a34a"
    text-color="#ffffff"
    active-text-color="#22c55e"
    class="teacher-sidebar"
  >
    <el-menu-item index="/teacher/scores">
      <span>分值管理</span>
    </el-menu-item>
    <el-menu-item index="/teacher/rankings">
      <span>实时排名</span>
    </el-menu-item>
    <el-menu-item index="/teacher/details">
      <span>分值明细</span>
    </el-menu-item>
    <el-menu-item index="/teacher/class-scores">
      <span>班级分值</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup lang="ts">
</script>

<style scoped>
.teacher-sidebar {
  height: 100%;
  border-right: none;
}

.teacher-sidebar .el-menu-item {
  color: #ffffff;
}

.teacher-sidebar .el-menu-item:hover {
  background-color: #22c55e;
}

.teacher-sidebar .el-menu-item.is-active {
  background-color: #22c55e;
}
</style>
