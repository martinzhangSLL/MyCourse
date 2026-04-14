import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/views/teacher/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/student',
    name: 'Student',
    component: () => import('@/views/student/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'student' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' })
    return
  }

  if (to.meta.role && authStore.user?.role !== to.meta.role) {
    if (authStore.user?.role === 'admin') {
      next({ name: 'Admin' })
    } else if (authStore.user?.role === 'teacher') {
      next({ name: 'Teacher' })
    } else if (authStore.user?.role === 'student') {
      next({ name: 'Student' })
    } else {
      next({ name: 'Login' })
    }
    return
  }

  if (to.name === 'Login' && authStore.isAuthenticated) {
    const role = authStore.user?.role
    if (role === 'admin') {
      next({ name: 'Admin' })
    } else if (role === 'teacher') {
      next({ name: 'Teacher' })
    } else {
      next({ name: 'Student' })
    }
    return
  }

  next()
})

export default router
