import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flush } from '@vue/test-utils'
import { ref } from 'vue'
import Login from '../Login.vue'
import { createPinia, setActivePinia } from 'pinia'

// Mock the API
vi.mock('@/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

// Mock router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

describe('Login.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('renders login form correctly', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-input': true,
          'el-button': true,
          'el-tabs': true,
          'el-tab-pane': true,
          'el-form': true,
          'el-form-item': true
        }
      }
    })

    expect(wrapper.find('.login-container').exists()).toBe(true)
  })

  it('has admin and teacher tab options', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-tabs': {
            template: '<div><slot /></div>',
            props: ['modelValue']
          },
          'el-tab-pane': { template: '<div />' },
          'el-input': { template: '<input />' },
          'el-button': { template: '<button />' },
          'el-form': { template: '<form><slot /></form>' },
          'el-form-item': { template: '<div><slot /></div>' }
        }
      }
    })

    // Check that tabs exist for admin and teacher
    expect(wrapper.text()).toContain('管理员')
    expect(wrapper.text()).toContain('教师')
  })
})
