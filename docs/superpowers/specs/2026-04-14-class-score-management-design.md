# 初中班级积分管理系统 — 设计文档

## 1. 项目概述

- **项目名称**：初中班级积分管理系统
- **项目类型**：前后端分离的全栈 Web 应用
- **核心功能**：教师针对学生正面/负面行为加减积分，查看积分排名，按周/月/学期统计，支持 Excel 导入导出
- **目标用户**：班级管理员（1 人）、班主任/科任教师（1 人/班级）

## 2. 视觉与交互风格

- **视觉风格**：活力绿色游戏风，以绿色为主色调，搭配积分/徽章元素，像游戏排行榜，激励感强
- **布局理念**：简洁大方，操作路径短，加分扣分页面按钮要大、输入框要大
- **响应式**：兼顾电脑（鼠标操作）和平板（触摸操作）

## 3. 系统架构

```
客户端（浏览器）
    │ HTTP/REST
    ▼
Nginx (端口 80)
    ├── 静态资源 / → repos/frontend (npm build 产物)
    └── /api/* → 反向代理 → Python FastAPI (127.0.0.1:8000)
                                        │
                                   SQLite 数据库
                                   (repos/db/*.db)
```

**目录结构**

```
repos/
├── frontend/          # Vue3 项目 (npm build 产物)
├── backend/           # Python FastAPI 项目
└── db/                # SQLite 数据库文件 (*.db)

docs/
└── superpowers/
    └── specs/         # 设计文档
```

## 4. 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + Composition API + TypeScript | `<script setup>` 写法 |
| UI 组件库 | Element Plus | 按需引入 |
| 路由 | Vue Router 4 | 页面导航 + 路由守卫 |
| 状态管理 | Pinia | 登录状态、全局配置 |
| 后端 | FastAPI | 异步，高性能，内置 Swagger 文档 |
| ORM | SQLAlchemy 2.0 | SQLite 原生支持 |
| 认证 | JWT (PyJWT) | 无状态 token |
| Excel 处理 | openpyxl | 导入/导出 |
| ASGI 服务器 | Uvicorn | 生产环境推荐 gunicorn |
| 反向代理 | Nginx | 静态托管 + API 代理 |

## 5. 数据库设计

> 数据库层面按多对多关系设计，为未来扩展预留空间。当前业务：教师与班级一对一，班级与课程多对多，课程与教师一对多。

### 5.1 ER 关系图

```
teacher ───< teacher_class >─── class
                              │
                              │
              class_course <───┼─── course
                              │
                              │
              student_class <──┘
                    │
                    │
              student <── score_record
```

### 5.2 表结构

**teacher（教师）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| name | VARCHAR(50) | 姓名 |
| password | VARCHAR(255) | 密码（ bcrypt 哈希） |
| created_at | DATETIME | 创建时间 |

**class（班级）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| name | VARCHAR(50) | 班级名称 |
| code | VARCHAR(20) | 班级编号（唯一） |
| is_active | BOOLEAN | 是否激活（激活后禁止 Excel 导入） |
| created_at | DATETIME | 创建时间 |

**teacher_class（教师-班级关联）**
| 字段 | 类型 | 说明 |
|------|------|------|
| teacher_id | INTEGER FK | 教师 ID |
| class_id | INTEGER FK | 班级 ID |
| PRIMARY KEY | (teacher_id, class_id) | |

**course（课程）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| name | VARCHAR(50) | 课程名称 |

**class_course（班级-课程关联）**
| 字段 | 类型 | 说明 |
|------|------|------|
| class_id | INTEGER FK | 班级 ID |
| course_id | INTEGER FK | 课程 ID |
| PRIMARY KEY | (class_id, course_id) | |

**student（学生）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| name | VARCHAR(50) | 姓名 |
| student_no | VARCHAR(20) | 学号 |
| created_at | DATETIME | 创建时间 |

**student_class（学生-班级关联）**
| 字段 | 类型 | 说明 |
|------|------|------|
| student_id | INTEGER FK | 学生 ID |
| class_id | INTEGER FK | 班级 ID |
| is_active | BOOLEAN | 是否激活 |
| current_score | INTEGER | 当前积分（冗余，加速查询） |
| PRIMARY KEY | (student_id, class_id) | |

**score_record（积分记录）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| student_id | INTEGER FK | 学生 ID |
| value | INTEGER | 分值（正数加分，负数扣分） |
| reason | VARCHAR(200) | 加减分原因 |
| course_id | INTEGER FK | 课程 ID |
| teacher_id | INTEGER FK | 教师 ID |
| score_at | DATETIME | 记录时间（加分/扣分发生的时间） |
| created_at | DATETIME | 创建时间 |

**term（学期）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| name | VARCHAR(50) | 学期名称，如 "2025-2026学年上学期" |
| year | VARCHAR(20) | 学年，如 "2025-2026" |

**term_setting（学期设置）**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增 ID |
| term_id | INTEGER FK | 学期 ID |
| start_date | DATE | 学期开始日期 |
| end_date | DATE | 学期结束日期 |

**config（系统配置）**
| 字段 | 类型 | 说明 |
|------|------|------|
| key | VARCHAR(50) PK | 配置键 |
| value | VARCHAR(255) | 配置值 |

> 初始配置项：
> - `settlement_code`：结算确认码
> - `init_code`：初始化确认码
> - `reasons`：加分/扣分原因列表（JSON 数组）

## 6. API 设计

> 所有 API 前缀 `/api`，认证通过 `Authorization: Bearer <token>` header。

### 6.1 认证

**POST /api/auth/login**
```json
// Request
{ "username": "admin", "password": "xxx", "role": "admin" }

// Response 200
{ "token": "eyJ...", "user": { "id": 1, "name": "管理员", "role": "admin" } }

// Response 401
{ "detail": "用户名或密码错误" }
```

**GET /api/auth/me**
```json
// Response 200
{ "id": 1, "name": "管理员", "role": "admin" }
```

### 6.2 班级管理

**GET /api/classes**
```json
// Response 200
[{ "id": 1, "name": "初三(2)班", "code": "C202601", "is_active": true }]
```

**POST /api/classes** — body: `{ "name": "", "code": "" }`

**PUT /api/classes/{id}** — body: `{ "name": "", "code": "" }`

**DELETE /api/classes/{id}** — 逻辑删除

### 6.3 学生管理

**GET /api/students?class_id=1**
```json
// Response 200
[{ "id": 1, "name": "张三", "student_no": "001", "current_score": 128 }]
```

**POST /api/students** — body: `{ "name": "", "student_no": "", "class_id": 1 }`

**POST /api/students/import** — body: `multipart/form-data`，字段 `file` (Excel)、`class_id`，返回导入数量（班级未激活才可导入）

**PUT /api/classes/{id}/activate** — 激活班级，激活后该班级禁止 Excel 导入

**PUT /api/students/{id}** — body: `{ "name": "", "student_no": "" }`

**DELETE /api/students/{id}**

### 6.4 分值管理

**POST /api/scores**
```json
// Request
{
  "student_id": 1,
  "value": 5,
  "reason": "作业优秀",
  "course_id": 1,
  "score_at": "2026-04-14T10:30:00"
}
// Response 200
{ "id": 1, "student_id": 1, "value": 5, "reason": "作业优秀", ... }
```

**GET /api/scores?student_id=1&course_id=1&start=2026-04-01&end=2026-04-30**
```json
// Response 200
[
  { "id": 1, "value": 5, "reason": "作业优秀", "course_name": "语文",
    "teacher_name": "李老师", "score_at": "2026-04-14T10:30:00" }
]
```

### 6.5 排名

**GET /api/rankings?class_id=1&period=total|week|month|term**
- `total`：所有积分（初始积分 + 所有加减分）
- `week`：本周加减分
- `month`：本月加减分
- `term`：本学期加减分

```json
// Response 200
[
  { "rank": 1, "student_id": 1, "student_name": "张三",
    "student_no": "001", "score": 128, "change": 5 },
  { "rank": 2, "student_id": 3, "student_name": "王五",
    "student_no": "003", "score": 112, "change": -3 }
]
```

**GET /api/rankings/export?class_id=1&period=total** — 返回 Excel 文件流

### 6.6 结算与初始化

**POST /api/settlement?class_id=1&code=XXXX**
- 导出该班级所有学生积分排名和加减分记录到 Excel
- 逻辑删除该班级所有积分记录
- 重置班级学生当前积分（student_class.current_score）

> 学期未结束时请求结算，需返回错误提示。

**POST /api/initialization?class_id=1&code=XXXX**
- body: `multipart/form-data`，字段 `file` (Excel，含学生姓名、学号、初始积分)
- 将对应学生的当前积分设置成初始积分

### 6.7 配置

**GET /api/config/reasons** → `["考试", "作业", "荣誉", "其他"]`

**PUT /api/config/reasons** → body: `["考试", "作业", "荣誉", "其他", "自定义原因"]`

**GET /api/config/terms**
```json
[{ "id": 1, "name": "2025-2026学年上学期", "year": "2025-2026",
   "start_date": "2026-02-10", "end_date": "2026-07-15" }]
```

**POST /api/config/terms** — body: `{ "name": "2025-2026学年上学期", "year": "2025-2026", "start_date": "2026-02-10", "end_date": "2026-07-15" }`

**PUT /api/config/terms/{id}** — body: `{ "start_date": "", "end_date": "" }`（学期名称和学年不可修改）

**GET /api/config/codes** — 仅管理员可访问

**PUT /api/config/codes** — body: `{ "settlement_code": "", "init_code": "" }`

### 6.8 教师管理（管理员）

**GET /api/teachers**

**POST /api/teachers** — body: `{ "name": "", "password": "" }`

**PUT /api/teachers/{id}**

**DELETE /api/teachers/{id}**

### 6.9 课程管理（管理员）

**GET /api/courses**

**POST /api/courses** — body: `{ "name": "" }`

**PUT /api/courses/{id}**

**DELETE /api/courses/{id}**

**GET /api/class-courses?class_id=1** — 获取班级已关联的课程

**PUT /api/class-courses** — body: `{ "class_id": 1, "course_ids": [1, 2, 3] }`

## 7. 前端页面结构

```
repos/frontend/
├── views/
│   ├── LoginView.vue              # 登录页
│   ├── admin/
│   │   ├── ClassManage.vue        # 班级管理
│   │   ├── StudentManage.vue      # 学生管理
│   │   ├── TeacherManage.vue      # 老师管理
│   │   ├── CourseManage.vue      # 课程管理
│   │   └── ConfigManage.vue       # 配置管理（学期、原因、确认码）
│   └── teacher/
│       ├── ScoreManage.vue        # 分值管理（方格展示）
│       ├── RankingView.vue        # 实时排名
│       └── ScoreDetail.vue        # 分值明细
├── router/
│   └── index.ts                   # 路由守卫
├── stores/
│   └── auth.ts                    # 登录状态 Pinia store
└── api/
    └── index.ts                   # Axios 封装，统一拦截器
```

**分值管理页面（ScoreManage.vue）布局**

```
┌─────────────────────────────────────────────────┐
│  [班级下拉]  [课程下拉]                            │
├─────────────────────────────────────────────────┤
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │  001   │  │  002   │  │  003   │  │  004   │   │
│  │ 张三   │  │ 李四   │  │ 王五   │  │ 赵六   │   │
│  │  128   │  │   95   │  │  112   │  │   78   │   │
│  └────────┘  └────────┘  └────────┘  └────────┘   │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │  005   │  │  006   │  │  ...   │  │  ...   │   │
│  │  ...   │  │  ...   │  │        │  │        │   │
│  └────────┘  └────────┘  └────────┘  └────────┘   │
└─────────────────────────────────────────────────┘
        点击方格 → 弹出加分/扣分弹窗
        加分时积分绿色字体，扣分时红色字体
```

**加分/扣分弹窗**

```
┌───────────────────────────────────┐
│        加分 / 扣分                 │
├───────────────────────────────────┤
│  学生：张三（学号 001）             │
│  当前积分：128                     │
├───────────────────────────────────┤
│  类型：[加分] [扣分]（默认加分）      │
│                                   │
│  分值：[____] 大输入框             │
│  （加分绿色，扣分红色）             │
│                                   │
│  原因：[预设下拉 ▼] 或 自填          │
│                                   │
│  [取消]            [确认]          │
└───────────────────────────────────┘
```

## 8. 排名规则

- **总排名**：初始积分 + 所有加减分，按降序排列
- **周排名**：以 term_setting.start_date 为起点，按自然周划分，统计选定周的加减分，按降序排列
- **月排名**：统计选定月份内的加减分，按降序排列
- **学期排名**：统计 term_setting.start_date 至 end_date 期间的加减分，按降序排列

## 9. 部署

**目录结构**

```
/opt/class-score/
├── frontend/              # npm build 产物
├── backend/               # Python 代码
├── db/                    # SQLite .db 文件
└── nginx.conf             # Nginx 配置
```

**Nginx 配置**

```nginx
server {
    listen 80;
    server_name _;

    location / {
        root /opt/class-score/frontend;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
    }
}
```

**后端启动**

```bash
cd /opt/class-score/backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

**初始化超级管理员**

首次部署时，通过命令行工具创建管理员账号（不在页面注册）。

## 10. 项目开发约定

- 前端代码提交到 `repos/frontend`
- 后端代码提交到 `repos/backend`
- 数据库文件存放在 `repos/db`
- 文档存放在 `docs`
- 前后端都需有 README.md 说明本地开发启动方式
