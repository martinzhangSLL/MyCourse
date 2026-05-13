# 实时排名班级选择权限控制设计

## 概述

在 Rankings 页面，班级下拉框根据用户角色显示不同的选项：
- **admin**：能看到所有班级
- **teacher**：只能看到自己关联的班级，默认选择第一个

## 后端改动

### 新增接口

**`GET /api/rankings/classes`** - 获取当前用户可访问的班级列表

| 用户角色 | 返回数据 |
|---------|---------|
| admin | 所有班级列表 |
| teacher | 仅关联的班级列表（通过 TeacherClass 表） |

**实现位置**：`repos/backend/app/routers/ranking_router.py`

**响应格式**：

```json
[
  { "id": 1, "name": "班级1", "code": "C001" },
  { "id": 2, "name": "班级2", "code": "C002" }
]
```

**业务逻辑**：
1. 获取当前用户信息（通过 `get_current_user` 依赖）
2. 如果是 admin 角色，查询所有班级
3. 如果是 teacher 角色，通过 `TeacherClass` 表筛选只关联自己的班级
4. 返回班级基本信息列表（id, name, code）

## 前端改动

### Rankings.vue

**文件**：`repos/frontend/src/views/teacher/Rankings.vue`

**改动点**：
1. `fetchClasses()` 函数调用 `/api/rankings/classes` 替代 `/api/classes`
2. 默认选择第一个班级作为展示（已有逻辑，保持不变）

**改动前**：
```typescript
async function fetchClasses() {
  const response = await api.get('/classes')
  // ...
}
```

**改动后**：
```typescript
async function fetchClasses() {
  const response = await api.get('/rankings/classes')
  // ...
}
```

## 文件清单

| 文件 | 改动类型 |
|------|---------|
| `repos/backend/app/routers/ranking_router.py` | 新增接口 |
| `repos/frontend/src/views/teacher/Rankings.vue` | 修改 API 调用 |

## 验证要点

1. admin 登录后可以看到所有班级
2. teacher 登录后只能看到自己关联的班级
3. 页面加载后自动选中第一个班级并展示排名
4. 切换班级后排名数据正确更新
