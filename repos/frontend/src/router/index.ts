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
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: '',
        redirect: { name: 'AdminDashboard' }
      },
      {
        path: 'classes',
        name: 'AdminClasses',
        component: () => import('@/views/admin/ClassManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
      },
      {
        path: 'students',
        name: 'AdminStudents',
        component: () => import('@/views/admin/StudentManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
      },
      {
        path: 'teachers',
        name: 'AdminTeachers',
        component: () => import('@/views/admin/TeacherManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
      },
      {
        path: 'courses',
        name: 'AdminCourses',
        component: () => import('@/views/admin/CourseManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
      },
      {
        path: 'config',
        name: 'AdminConfig',
        component: () => import('@/views/admin/ConfigManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
      },
      {
        path: 'ranks',
        name: 'AdminRanks',
        component: () => import('@/views/admin/RankManage.vue'),
        meta: { requiresAuth: true, role: 'admin' }
      },
      {
        path: 'settlement',
        name: 'AdminSettlement',
        component: () => import('@/views/admin/Settlement.vue'),
        meta: { requiresAuth: true, role: 'admin' }
      }
    ]
  },
  {
    path: '/admin-dashboard',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/teacher',
    name: 'Teacher',
    component: () => import('@/layouts/TeacherLayout.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    children: [
      {
        path: '',
        redirect: { name: 'TeacherDashboard' }
      },
      {
        path: 'scores',
        name: 'TeacherScores',
        component: () => import('@/views/teacher/Scores.vue'),
        meta: { requiresAuth: true, role: 'teacher' }
      },
      {
        path: 'rankings',
        name: 'TeacherRankings',
        component: () => import('@/views/teacher/Rankings.vue'),
        meta: { requiresAuth: true, role: 'teacher' }
      },
      {
        path: 'details',
        name: 'TeacherDetails',
        component: () => import('@/views/teacher/Details.vue'),
        meta: { requiresAuth: true, role: 'teacher' }
      },
      {
        path: 'class-scores',
        name: 'ClassScores',
        component: () => import('../views/teacher/ClassScores.vue'),
        meta: { requiresAuth: true, role: 'teacher' }
      },
      {
        path: 'dashboard',
        name: 'TeacherDashboard',
        component: () => import('@/views/teacher/Dashboard.vue'),
        meta: { requiresAuth: true, role: 'teacher' }
      }
    ]
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
