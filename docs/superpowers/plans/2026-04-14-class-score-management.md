# 初中班级积分管理系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建设完整的初中班级积分管理系统，包含前后端分离的 Vue3+FastAPI 应用，支持班级/学生/教师/课程管理、积分加减排名、结算初始化等功能。

**Architecture:** 单服务器部署，Nginx 反向代理。前端 Vue3 + Element Plus 静态托管，后端 FastAPI + SQLAlchemy + SQLite，提供 RESTful API，JWT 无状态认证。

**Tech Stack:** Vue 3 + Element Plus + TypeScript + Vite (前端) | FastAPI + SQLAlchemy 2.0 + PyJWT + openpyxl + Uvicorn (后端) | SQLite (数据库) | Nginx (反向代理)

---

## 阶段一：项目骨架搭建

### 1.1 后端项目初始化

**目标：** 建立 `repos/backend/` Python 项目结构，安装依赖，配置 SQLAlchemy 连接 SQLite。

**文件：**
- 创建: `repos/backend/` 目录结构
- 创建: `repos/backend/requirements.txt`
- 创建: `repos/backend/app/__init__.py`
- 创建: `repos/backend/app/database.py` — 数据库连接配置
- 创建: `repos/backend/app/models/__init__.py`
- 创建: `repos/backend/app/models/models.py` — 所有数据库模型
- 创建: `repos/backend/app/main.py` — FastAPI 入口

**依赖（requirements.txt）：**
```
fastapi==0.115.*
uvicorn[standard]==0.30.*
sqlalchemy==2.0.*
pyjwt==2.9.*
passlib[bcrypt]==1.7.*
python-multipart==0.0.9
openpyxl==3.1.*
pydantic==2.9.*
```

**数据库连接配置（database.py）：**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./repos/db/scores.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
```

**TODO:**
- [ ] 1.1.1 创建目录结构和 requirements.txt
- [ ] 1.1.2 编写 database.py
- [ ] 1.1.3 创建所有数据库模型（11张表：teacher, class, teacher_class, course, class_course, student, student_class, score_record, term, term_setting, config）
- [ ] 1.1.4 创建 FastAPI main.py 入口
- [ ] 1.1.5 安装依赖并验证 `uvicorn app.main:app --reload` 启动成功
- [ ] 1.1.6 初始化数据库表（启动时自动创建）

---

### 1.2 前端项目初始化

**目标：** 建立 `repos/frontend/` Vue3 + TypeScript + Element Plus 项目。

**文件：**
- 创建: `repos/frontend/package.json`
- 创建: `repos/frontend/vite.config.ts`
- 创建: `repos/frontend/tsconfig.json`
- 创建: `repos/frontend/index.html`
- 创建: `repos/frontend/src/main.ts`
- 创建: `repos/frontend/src/App.vue`
- 创建: `repos/frontend/src/router/index.ts` — 路由配置（含路由守卫）
- 创建: `repos/frontend/src/stores/auth.ts` — Pinia 认证状态
- 创建: `repos/frontend/src/api/index.ts` — Axios 封装（请求拦截器 + 响应拦截器 + JWT token）
- 创建: `repos/frontend/src/styles/` — 全局样式（绿色游戏风主题变量）

**Element Plus 按需引入配置（vite.config.ts）：**
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({ resolvers: [ElementPlusResolver()] }),
    Components({ resolvers: [ElementPlusResolver()] }),
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
```

**TODO:**
- [ ] 1.2.1 创建 Vue3 + Vite + TypeScript 项目（使用 npm create vite@latest 或手动创建 package.json）
- [ ] 1.2.2 配置 Element Plus 按需引入
- [ ] 1.2.3 配置 Axios 封装（JWT token 自动附加，401 自动跳转登录）
- [ ] 1.2.4 配置 Vue Router（含管理员/教师角色路由守卫）
- [ ] 1.2.5 配置 Pinia auth store
- [ ] 1.2.6 配置绿色游戏风全局 CSS 变量和基础样式
- [ ] 1.2.7 启动开发服务器验证 `npm run dev` 无报错

---

### 1.3 登录页面与 JWT 认证

**目标：** 实现管理员/教师登录功能，后端签发 JWT，前端保存 token 并根据角色跳转。

**后端文件：**
- 创建: `repos/backend/app/schemas/auth.py` — Pydantic 登录/响应模型
- 创建: `repos/backend/app/routers/auth.py` — 认证路由（login, me）
- 创建: `repos/backend/app/auth.py` — JWT 工具函数（签发/验证 token）
- 创建: `repos/backend/app/dependencies.py` — FastAPI 依赖（get_current_user）

**API：**
```
POST /api/auth/login      → { token, user }
GET  /api/auth/me         → { id, name, role }
```

**前端文件：**
- 创建: `repos/frontend/src/views/LoginView.vue` — 登录页（角色选择 + 账号密码）

**登录页要求：**
- 顶部绿色游戏风标题
- 角色切换 Tab（管理员 / 教师）
- 账号、密码输入框（大输入框）
- 登录按钮（大按钮）
- 错误提示

**TODO:**
- [ ] 1.3.1 创建 Pydantic schemas（LoginRequest, LoginResponse, UserResponse）
- [ ] 1.3.2 创建 JWT 工具函数（create_access_token, verify_token）
- [ ] 1.3.3 创建 auth 路由（登录接口，密码 bcrypt 校验，签发 JWT）
- [ ] 1.3.4 创建 FastAPI 依赖 get_current_user（从 Authorization header 解析 JWT）
- [ ] 1.3.5 创建 LoginView.vue（管理员/教师 Tab 切换，大输入框，表单验证）
- [ ] 1.3.6 登录成功保存 token 到 localStorage，跳转到对应角色首页
- [ ] 1.3.7 路由守卫：未登录访问其他页面 → 跳转登录页
- [ ] 1.3.8 测试登录流程（管理员账号能登录，教师账号能登录）

---

### 1.4 管理员首页框架

**目标：** 搭建管理员端 layout，包含侧边菜单和顶部导航。

**前端文件：**
- 创建: `repos/frontend/src/layouts/AdminLayout.vue` — 管理员布局（侧边栏 + 主内容区）
- 创建: `repos/frontend/src/components/AdminSidebar.vue` — 侧边栏菜单

**侧边栏菜单项（管理员）：**
- 班级管理
- 学生管理
- 教师管理
- 课程管理
- 配置管理
- 结算 / 初始化（放在配置管理同级或子级）

**TODO:**
- [ ] 1.4.1 创建 AdminLayout.vue（左侧侧边栏 + 右侧内容区，绿色游戏风配色）
- [ ] 1.4.2 创建 AdminSidebar.vue（Element Plus Menu，显示菜单项，顶部显示管理员名称，底部退出按钮）
- [ ] 1.4.3 配置管理员路由（/admin/*），未登录 → /login
- [ ] 1.4.4 测试页面加载、菜单点击路由切换、退出登录

---

### 1.5 教师首页框架

**目标：** 搭建教师端 layout。

**前端文件：**
- 创建: `repos/frontend/src/layouts/TeacherLayout.vue` — 教师布局
- 创建: `repos/frontend/src/components/TeacherSidebar.vue` — 教师侧边栏

**侧边栏菜单项（教师）：**
- 分值管理
- 实时排名
- 分值明细

**TODO:**
- [ ] 1.5.1 创建 TeacherLayout.vue
- [ ] 1.5.2 创建 TeacherSidebar.vue
- [ ] 1.5.3 配置教师路由（/teacher/*），未登录 → /login
- [ ] 1.5.4 测试页面加载、菜单切换

---

## 阶段二：管理员基础功能 CRUD

### 2.1 班级管理

**目标：** 实现班级的增删改查 + 激活 + 关联教师/课程配置。

**后端文件：**
- 创建: `repos/backend/app/schemas/class.py` — 班级 Pydantic 模型
- 创建: `repos/backend/app/routers/class_router.py` — 班级 CRUD 路由

**API：**
```
GET    /api/classes                 → 班级列表（含关联教师、课程）
POST   /api/classes                 → 新增班级
PUT    /api/classes/{id}            → 编辑班级（含关联教师、课程）
DELETE /api/classes/{id}            → 删除班级
PUT    /api/classes/{id}/activate   → 激活班级
```

**关联配置请求体：**
```json
{
  "name": "初三(2)班",
  "code": "C202601",
  "teacher_ids": [1],
  "course_ids": [1, 2, 3]
}
```

**前端文件：**
- 创建: `repos/frontend/src/views/admin/ClassManage.vue` — 班级管理页面

**页面要求：**
- 顶部：班级列表（Element Plus Table）+ 新增按钮
- 每行操作：编辑、删除、激活
- 新增/编辑：Dialog 弹窗，填写班级名称、编号，选择关联教师（多选）、关联课程（多选）
- 激活按钮：仅未激活班级显示，点击后班级 is_active=true
- 激活后：导入按钮禁用，显示"已激活"标签

**TODO:**
- [ ] 2.1.1 创建班级 Pydantic schemas
- [ ] 2.1.2 实现班级 CRUD API 路由
- [ ] 2.1.3 实现激活班级 API
- [ ] 2.1.4 创建 ClassManage.vue（Table 列表 + 新增/编辑 Dialog + 激活操作）
- [ ] 2.1.5 测试：新增班级 → 编辑关联教师/课程 → 激活班级 → 激活后验证导入禁用

---

### 2.2 教师管理

**目标：** 实现教师增删改查。

**后端文件：**
- 创建: `repos/backend/app/schemas/teacher.py`
- 创建: `repos/backend/app/routers/teacher_router.py`

**API：**
```
GET    /api/teachers
POST   /api/teachers
PUT    /api/teachers/{id}
DELETE /api/teachers/{id}
```

**前端文件：**
- 创建: `repos/frontend/src/views/admin/TeacherManage.vue`

**TODO:**
- [ ] 2.2.1 创建教师 Pydantic schemas
- [ ] 2.2.2 实现教师 CRUD API（密码 bcrypt 哈希存储）
- [ ] 2.2.3 创建 TeacherManage.vue
- [ ] 2.2.4 测试：增删改查教师

---

### 2.3 课程管理

**目标：** 实现课程增删改查。

**后端文件：**
- 创建: `repos/backend/app/schemas/course.py`
- 创建: `repos/backend/app/routers/course_router.py`

**API：**
```
GET    /api/courses
POST   /api/courses
PUT    /api/courses/{id}
DELETE /api/courses/{id}
GET    /api/class-courses?class_id=1   → 获取班级已关联的课程
PUT    /api/class-courses              → 更新班级关联课程
```

**前端文件：**
- 创建: `repos/frontend/src/views/admin/CourseManage.vue`

**TODO:**
- [ ] 2.3.1 创建课程 Pydantic schemas
- [ ] 2.3.2 实现课程 CRUD API + 班级课程关联 API
- [ ] 2.3.3 创建 CourseManage.vue（Table + Dialog + 班级课程关联配置）
- [ ] 2.3.4 测试：增删改查课程，班级编辑时配置课程关联

---

### 2.4 学生管理

**目标：** 实现学生增删改查 + Excel 导入。

**后端文件：**
- 创建: `repos/backend/app/schemas/student.py`
- 创建: `repos/backend/app/routers/student_router.py`
- 创建: `repos/backend/app/utils/excel.py` — Excel 读取工具函数

**API：**
```
GET    /api/students?class_id=1
POST   /api/students
POST   /api/students/import          → Excel 导入（仅未激活班级）
PUT    /api/students/{id}
DELETE /api/students/{id}
```

**Excel 导入校验：**
- 班级已激活 → 返回 400 错误"班级已激活，禁止导入"
- Excel 第一列姓名，第二列学号
- 学号唯一校验（同一班级内学号不能重复）
- 返回导入成功数量

**前端文件：**
- 创建: `repos/frontend/src/views/admin/StudentManage.vue`

**页面要求：**
- 顶部：班级下拉选择 + 学生 Table（学号、姓名、当前积分、操作列）
- 操作：编辑（Dialog）、删除
- 未激活班级：显示导入按钮（上传 Excel）
- 已激活班级：显示"已激活"标签，禁用导入按钮

**TODO:**
- [ ] 2.4.1 创建学生 Pydantic schemas
- [ ] 2.4.2 实现学生 CRUD API
- [ ] 2.4.3 实现 Excel 导入 API（openpyxl 读取，检查班级激活状态）
- [ ] 2.4.4 创建 StudentManage.vue（含班级选择、Table、导入 Excel 功能）
- [ ] 2.4.5 测试：导入学生 → 激活班级 → 验证激活后禁止导入

---

### 2.5 配置管理

**目标：** 实现学期设置、积分原因配置、确认码配置。

**后端文件：**
- 创建: `repos/backend/app/schemas/config.py`
- 创建: `repos/backend/app/routers/config_router.py`
- 创建: `repos/backend/app/routers/term_router.py`

**API：**
```
GET    /api/config/reasons
PUT    /api/config/reasons
GET    /api/config/terms
POST   /api/config/terms
PUT    /api/config/terms/{id}
GET    /api/config/codes          → 仅管理员
PUT    /api/config/codes
```

**初始化配置数据（启动时写入 config 表）：**
```json
{
  "settlement_code": "ADMIN123",
  "init_code": "INIT456",
  "reasons": ["考试", "作业", "荣誉", "其他"]
}
```

**前端文件：**
- 创建: `repos/frontend/src/views/admin/ConfigManage.vue` — Tab 页：学期设置 | 积分原因 | 确认码

**页面要求：**
- Tab 1 学期设置：Table（学期名、学年、开始日期、结束日期）+ 新增/编辑/删除
- Tab 2 积分原因：Tag 列表（可删除）+ 新增输入框
- Tab 3 确认码：修改结算确认码、初始化确认码（大输入框 + 保存）

**TODO:**
- [ ] 2.5.1 实现 config 相关 API（reasons、codes 的读写）
- [ ] 2.5.2 实现 term 相关 API（CRUD）
- [ ] 2.5.3 启动时检查并初始化默认配置数据
- [ ] 2.5.4 创建 ConfigManage.vue（3个 Tab 页）
- [ ] 2.5.5 测试：增删改查学期，配置积分原因，修改确认码

---

### 2.6 结算与初始化

**目标：** 实现结算（导出 Excel + 清零）和积分初始化（按 Excel 重置积分）。

**后端文件：**
- 创建: `repos/backend/app/routers/settlement_router.py`
- 创建: `repos/backend/app/utils/settlement.py` — 结算 Excel 生成逻辑

**API：**
```
POST /api/settlement?class_id=1&code=xxx   → 结算（导Excel+清零+逻辑删除记录）
POST /api/initialization?class_id=1&code=xxx  → 初始化（按Excel重置积分）
```

**结算逻辑：**
1. 校验确认码
2. 检查学期结束日期（当前日期 >= 学期结束日期，未设置则跳过）
3. 生成 Excel（含"排名"和"明细"两个 Sheet）
4. 逻辑删除该班级所有 score_record
5. 重置 student_class.current_score 为 0

**结算导出 Excel 结构：**
- Sheet1「排名」：排名、学号、姓名、当前积分
- Sheet2「明细」：学生姓名、学号、分值、原因、课程、操作教师、时间

**前端文件：**
- 创建: `repos/frontend/src/views/admin/SettlementView.vue`

**页面要求：**
- 班级下拉选择 + 结算按钮
- 点击结算 → 输入确认码（Dialog） → 确认后下载 Excel
- 初始化 Tab：班级下拉 + 上传 Excel + 确认码输入 → 执行初始化

**TODO:**
- [ ] 2.6.1 实现结算 API（校验确认码 + 学期日期 + 生成 Excel + 清零）
- [ ] 2.6.2 实现初始化 API（校验确认码 + 按 Excel 重置积分）
- [ ] 2.6.3 创建结算 Excel 生成工具（openpyxl，两个 Sheet）
- [ ] 2.6.4 创建 SettlementView.vue（含结算和初始化两个 Tab）
- [ ] 2.6.5 测试：结算导出 Excel，积分清零；初始化重置积分

---

## 阶段三：教师核心功能

### 3.1 分值管理页面（方格展示）

**目标：** 实现分值管理页面，教师选择班级+课程后以方格展示学生，点击加分/扣分。

**前端文件：**
- 创建: `repos/frontend/src/views/teacher/ScoreManage.vue`
- 创建: `repos/frontend/src/components/ScoreCard.vue` — 单个学生方格组件
- 创建: `repos/frontend/src/components/ScoreDialog.vue` — 加减分弹窗组件

**API：**
```
GET /api/class-courses?class_id=1       → 获取班级已关联的课程（教师用）
GET /api/students?class_id=1            → 获取班级学生列表（含当前积分）
POST /api/scores                        → 加减分
```

**加分/扣分弹窗（ScoreDialog.vue）要求：**
- 顶部：学生姓名（学号）、当前积分
- 类型切换：加分 / 扣分 Tab（Element Plus Radio 或 Tab 组件）
  - 默认选中「加分」
- 分值输入：大输入框（大字号），仅允许输入数字
  - 加分时字体绿色 (#22c55e)
  - 扣分时字体红色 (#ef4444)
- 原因下拉：预设原因列表（从 /api/config/reasons 获取）+ 可手动填写
- 底部：取消 / 确认按钮

**分值管理页面（ScoreManage.vue）布局：**
```
┌──────────────────────────────────────────────┐
│  班级：[(    班级下拉    )]                    │
│  课程：[(    课程下拉    )]                    │
├──────────────────────────────────────────────┤
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐ │
│  │ 001    │  │ 002    │  │ 003    │  │ 004    │ │
│  │ 张三   │  │ 李四   │  │ 王五   │  │ 赵六   │ │
│  │  128   │  │   95   │  │  112   │  │   78   │ │
│  └────────┘  └────────┘  └────────┘  └────────┘ │
│  ...（响应式排列，每行4-6个方格）                │
└──────────────────────────────────────────────┘
        点击方格 → ScoreDialog 加减分弹窗
```

**绿色游戏风配色：**
- 页面背景：#f0fdf4（淡绿色）
- 方格背景：白色，边框 #86efac
- 当前积分：#16a34a（深绿色）
- 加分字体：#22c55e
- 扣分字体：#ef4444
- 按钮：#22c55e 背景色

**TODO:**
- [ ] 3.1.1 创建 ScoreCard.vue（学生方格，显示学号/姓名/积分，点击触发事件）
- [ ] 3.1.2 创建 ScoreDialog.vue（加分/扣分 Tab + 颜色区分 + 预设原因下拉）
- [ ] 3.1.3 实现 POST /api/scores API（保存积分记录 + 更新 student_class.current_score）
- [ ] 3.1.4 创建 ScoreManage.vue（班级/课程下拉 + 方格网格布局 + 响应式）
- [ ] 3.1.5 测试：选择班级/课程 → 显示学生方格 → 点击加分 → 验证积分更新

---

### 3.2 实时排名页面

**目标：** 实现排名展示，支持总排名、周排名、月排名、学期排名，支持导出 Excel。

**后端文件：**
- 创建: `repos/backend/app/routers/ranking_router.py`
- 创建: `repos/backend/app/utils/ranking.py` — 排名计算逻辑

**排名计算逻辑（ranking.py）：**
```python
# 总排名：初始积分 + 所有加减分
# 周排名：以 term_setting.start_date 为起点，按自然周划分
# 月排名：按月份筛选
# 学期排名：term_setting.start_date 到 end_date
```

**API：**
```
GET /api/rankings?class_id=1&period=total|week|month|term&week=1&month=2026-04
GET /api/rankings/export?class_id=1&period=total  → Excel 文件流
```

**前端文件：**
- 创建: `repos/frontend/src/views/teacher/RankingView.vue`

**页面要求：**
- 顶部：班级下拉 + 排名维度切换（总排名/周排名/月排名/学期排名 Tab）
- 周排名：显示第几周下拉
- 月排名：显示月份选择
- 排名 Table：排名、姓名、学号、积分（总排名显示总分，周/月/学期显示该期间加减分）
- 导出 Excel 按钮

**TODO:**
- [ ] 3.2.1 实现排名计算逻辑（ranking.py）
- [ ] 3.2.2 实现 GET /api/rankings API（支持 total/week/month/term 多维度）
- [ ] 3.2.3 实现 GET /api/rankings/export API（返回 Excel 文件流）
- [ ] 3.2.4 创建 RankingView.vue（排名维度 Tab + Table + 导出按钮）
- [ ] 3.2.5 测试：总排名、周排名、月排名、学期排名，导出 Excel

---

### 3.3 分值明细页面

**目标：** 查看积分明细记录。

**API：**
```
GET /api/scores?student_id=&course_id=&start=&end=
```

**前端文件：**
- 创建: `repos/frontend/src/views/teacher/ScoreDetail.vue`

**页面要求：**
- 顶部：班级下拉 + 时间范围筛选
- 明细 Table：学生姓名、学号、分值（绿/红）、原因、课程、操作教师、时间
- 分值列颜色：正数绿色，负数红色

**TODO:**
- [ ] 3.3.1 实现 GET /api/scores API（支持多条件筛选）
- [ ] 3.3.2 创建 ScoreDetail.vue（Table + 筛选 + 分值颜色）
- [ ] 3.3.3 测试：查看分值明细，按时间筛选

---

## 阶段四：收尾与部署

### 4.1 Nginx 部署配置

**文件：**
- 创建: `repos/deploy/nginx.conf` — Nginx 配置文件

**TODO:**
- [ ] 4.1.1 编写 Nginx 配置（静态资源托管 + /api 反向代理）
- [ ] 4.1.2 编写部署脚本或 README 说明部署步骤

---

### 4.2 管理员初始化工具

**目标：** 提供命令行工具创建首个管理员账号。

**文件：**
- 创建: `repos/backend/scripts/init_admin.py`

**TODO:**
- [ ] 4.2.1 编写 init_admin.py（交互式创建管理员账号）
- [ ] 4.2.2 编写 README.md（前后端本地开发说明 + 部署说明）

---

### 4.3 最终验收

**TODO:**
- [ ] 4.3.1 端到端测试完整管理员流程
- [ ] 4.3.2 端到端测试完整教师流程
- [ ] 4.3.3 检查所有页面 UI 是否符合绿色游戏风
- [ ] 4.3.4 验证响应式布局（电脑 + 平板）

---

## 规范与约定

### Git 提交规范
```
feat: add class management
fix: correct score color display in dialog
refactor: extract score calculation logic
docs: add deployment guide
test: add score API integration tests
```

### 分支策略
- 主分支：`main`
- 功能分支：`feature/class-management`、`feature/score-grid`
- 每个阶段完成后提交 PR 到 main

### 代码位置
| 内容 | 路径 |
|------|------|
| 后端代码 | `repos/backend/` |
| 前端代码 | `repos/frontend/` |
| 数据库文件 | `repos/db/` |
| 设计文档 | `docs/superpowers/specs/` |
| 实施计划 | `docs/superpowers/plans/` |
| 需求文档 | `docs/需求规格说明书.md` |
