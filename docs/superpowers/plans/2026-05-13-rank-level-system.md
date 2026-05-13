# 段位系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现段位系统，包括：段位数据管理（管理员）、分值明细时间+8小时修正、教师端班级分值页面显示段位图片和升级进度

**Architecture:**
- 新增 `rank` 表存储段位配置（段位名称、积分区间、图片路径、排序序号）
- 后端提供段位 CRUD API 和获取学生当前段位接口
- 前端管理员端新增段位管理页面，教师端新增"班级分值"页面
- 图片通过 Docker volume 挂载持久化存储

**Tech Stack:** Vue 3 + TypeScript + Element Plus (前端), FastAPI + SQLAlchemy 2.0 (后端), Docker (部署)

---

## File Structure

```
repos/
├── backend/
│   └── app/
│       ├── models/
│       │   └── models.py          # 新增 Rank 模型
│       ├── schemas/
│       │   └── rank_schema.py     # 新增 Rank Pydantic schemas
│       ├── routers/
│       │   └── rank_router.py     # 新增 Rank API 路由
│       └── main.py                # 注册新路由
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── admin/
│       │   │   └── RankManage.vue  # 新增 段位管理页面
│       │   └── teacher/
│       │       └── ClassScores.vue # 新增 班级分值页面（显示段位）
│       ├── router/
│       │   └── index.ts           # 添加新页面路由
│       └── api/
│           └── index.ts            # 添加 rank API 调用
├── pics/                           # Docker 宿主机挂载目录，存放段位图片
│   ├── 1.png
│   ├── 2.png
│   ├── 3.png
│   ├── 4.png
│   ├── 5.png
│   └── 6.png
```

---

## Task 1: 修复 ScoreDetail.vue 时间显示 (+8小时)

**Files:**
- Modify: `repos/frontend/src/views/teacher/Details.vue:191-202`

**Steps:**

- [ ] **Step 1: 修改 formatDate 函数**

将 `formatDate` 函数改为将 UTC 时间字符串显式加上 'Z' 后缀，使 JavaScript 将其解析为 UTC 时间，然后 `toLocaleString('zh-CN')` 会自动转换为本地时区时间（东八区）。

```javascript
// 替换 repos/frontend/src/views/teacher/Details.vue 中的 formatDate 函数
function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  // 加上 'Z' 表示这是 UTC 时间，toLocaleString 会自动转为本地时区
  const date = new Date(dateStr + 'Z')
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
```

- [ ] **Step 2: 验证改动**

确认代码修改正确，函数签名不变，仅内部逻辑处理 UTC 正确。

---

## Task 2: 新增 Rank 数据模型和 Schemas

**Files:**
- Modify: `repos/backend/app/models/models.py` — 添加 Rank 类
- Create: `repos/backend/app/schemas/rank_schema.py` — Pydantic schemas
- Modify: `repos/backend/app/main.py` — 注册路由（后续任务添加）

**Steps:**

- [ ] **Step 1: 在 models.py 添加 Rank 模型**

在 `teacher_class` 表之后添加：

```python
class Rank(Base):
    """段位表"""
    __tablename__ = "ranks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="段位名称")
    min_score = Column(Integer, nullable=False, comment="最低积分")
    max_score = Column(Integer, nullable=True, comment="最高积分，NULL表示无上限")
    image_url = Column(String(255), nullable=False, comment="段位图片路径")
    display_order = Column(Integer, nullable=False, default=0, comment="排序序号")
    created_at = Column(DateTime, default=datetime.now)
```

- [ ] **Step 2: 创建 rank_schema.py**

```python
# repos/backend/app/schemas/rank_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RankBase(BaseModel):
    name: str
    min_score: int
    max_score: Optional[int] = None
    image_url: str
    display_order: int = 0

class RankCreate(RankBase):
    pass

class RankUpdate(BaseModel):
    name: Optional[str] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None

class RankResponse(RankBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 验证 models.py 语法**

```bash
cd D:/Learning/MyCourse/repos/backend && python -c "from app.models.models import Rank; print('Rank model OK')"
```

---

## Task 3: 创建 Rank API 路由

**Files:**
- Create: `repos/backend/app/routers/rank_router.py`
- Modify: `repos/backend/app/main.py` — 注册路由

**Steps:**

- [ ] **Step 1: 创建 rank_router.py**

```python
# repos/backend/app/routers/rank_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Rank
from app.schemas.rank_schema import RankCreate, RankUpdate, RankResponse

router = APIRouter(prefix="/api/ranks", tags=["ranks"])

@router.get("", response_model=List[RankResponse])
def list_ranks(db: Session = Depends(get_db)):
    ranks = db.query(Rank).order_by(Rank.display_order).all()
    return ranks

@router.get("/{rank_id}", response_model=RankResponse)
def get_rank(rank_id: int, db: Session = Depends(get_db)):
    rank = db.query(Rank).filter(Rank.id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="段位不存在")
    return rank

@router.post("", response_model=RankResponse)
def create_rank(rank_data: RankCreate, db: Session = Depends(get_db)):
    rank = Rank(**rank_data.model_dump())
    db.add(rank)
    db.commit()
    db.refresh(rank)
    return rank

@router.put("/{rank_id}", response_model=RankResponse)
def update_rank(rank_id: int, rank_data: RankUpdate, db: Session = Depends(get_db)):
    rank = db.query(Rank).filter(Rank.id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="段位不存在")
    update_data = rank_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rank, key, value)
    db.commit()
    db.refresh(rank)
    return rank

@router.delete("/{rank_id}")
def delete_rank(rank_id: int, db: Session = Depends(get_db)):
    rank = db.query(Rank).filter(Rank.id == rank_id).first()
    if not rank:
        raise HTTPException(status_code=404, detail="段位不存在")
    db.delete(rank)
    db.commit()
    return {"message": "删除成功"}
```

- [ ] **Step 2: 在 main.py 注册路由**

在 `from app.routers import ...` 行添加 `rank_router`，在 `app.include_router(...)` 添加 `rank_router.router`。

- [ ] **Step 3: 验证路由注册**

```bash
cd D:/Learning/MyCourse/repos/backend && python -c "from app.main import app; print([r.path for r in app.routes if 'rank' in r.path])"
```
期望输出包含 `/api/ranks`。

---

## Task 4: 创建 Rank 初始化脚本

**Files:**
- Create: `repos/backend/scripts/init_ranks.py`

**Steps:**

- [ ] **Step 1: 创建初始化脚本**

```python
# repos/backend/scripts/init_ranks.py
"""初始化段位数据"""
import sys
sys.path.insert(0, '.')

from app.database import get_db, engine
from app.models.models import Base, Rank

def init_ranks():
    # 创建表
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import Session
    with Session(engine) as session:
        # 检查是否已有数据
        existing = session.query(Rank).count()
        if existing > 0:
            print(f"段位表已有 {existing} 条数据，跳过初始化")
            return

        ranks = [
            {"name": "启灵境", "min_score": 0, "max_score": 50, "image_url": "/pics/1.png", "display_order": 1},
            {"name": "凝光境", "min_score": 51, "max_score": 100, "image_url": "/pics/2.png", "display_order": 2},
            {"name": "逐风境", "min_score": 101, "max_score": 200, "image_url": "/pics/3.png", "display_order": 3},
            {"name": "凌云境", "min_score": 201, "max_score": 300, "image_url": "/pics/4.png", "display_order": 4},
            {"name": "摘星境", "min_score": 301, "max_score": 400, "image_url": "/pics/5.png", "display_order": 5},
            {"name": "扶摇境", "min_score": 401, "max_score": None, "image_url": "/pics/6.png", "display_order": 6},
        ]

        for r in ranks:
            session.add(Rank(**r))

        session.commit()
        print("段位初始化成功")

if __name__ == "__main__":
    init_ranks()
```

- [ ] **Step 2: 运行初始化脚本**

```bash
cd D:/Learning/MyCourse/repos/backend && python scripts/init_ranks.py
```
期望输出：`段位初始化成功`

---

## Task 5: 前端 API 添加 Rank 接口

**Files:**
- Modify: `repos/frontend/src/api/index.ts` — 添加 rank 相关 API

**Steps:**

- [ ] **Step 1: 添加 rank API 函数**

在 `repos/frontend/src/api/index.ts` 末尾添加：

```typescript
// 段位管理 API
export const rankApi = {
  list: () => api.get('/ranks'),
  get: (id: number) => api.get(`/ranks/${id}`),
  create: (data: { name: string; min_score: number; max_score: number | null; image_url: string; display_order: number }) =>
    api.post('/ranks', data),
  update: (id: number, data: Partial<{ name: string; min_score: number; max_score: number | null; image_url: string; display_order: number }>) =>
    api.put(`/ranks/${id}`, data),
  delete: (id: number) => api.delete(`/ranks/${id}`),
}
```

---

## Task 6: 创建管理员段位管理页面

**Files:**
- Create: `repos/frontend/src/views/admin/RankManage.vue`
- Modify: `repos/frontend/src/router/index.ts` — 添加路由
- Modify: `repos/frontend/src/views/admin/AdminMenu.vue` 或相关菜单配置 — 添加菜单入口（需要查看具体菜单实现方式）

**Steps:**

- [ ] **Step 1: 创建 RankManage.vue**

参考 `ClassManage.vue` 的 CRUD 模式，创建一个完整的段位管理页面：

```vue
<!-- repos/frontend/src/views/admin/RankManage.vue -->
<template>
  <div class="rank-manage">
    <div class="page-header">
      <h2>段位管理</h2>
      <el-button type="primary" @click="openAddDialog">新增段位</el-button>
    </div>

    <el-table :data="ranks" stripe v-loading="loading">
      <el-table-column prop="display_order" label="序号" width="80" />
      <el-table-column prop="name" label="段位名称" width="150" />
      <el-table-column label="积分区间" width="200">
        <template #default="{ row }">
          {{ row.min_score }}{{ row.max_score ? ' - ' + row.max_score : '+' }}
        </template>
      </el-table-column>
      <el-table-column prop="image_url" label="图片路径" min-width="200" />
      <el-table-column label="预览" width="100">
        <template #default="{ row }">
          <img :src="row.image_url" style="width:40px;height:40px;object-fit:contain;" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑段位' : '新增段位'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="段位名称">
          <el-input v-model="form.name" placeholder="如：启灵境" />
        </el-form-item>
        <el-form-item label="最低积分">
          <el-input-number v-model="form.min_score" :min="0" />
        </el-form-item>
        <el-form-item label="最高积分">
          <el-input-number v-model="form.max_score" :min="0" placeholder="留空表示无上限" />
        </el-form-item>
        <el-form-item label="图片路径">
          <el-input v-model="form.image_url" placeholder="/pics/1.png" />
        </el-form-item>
        <el-form-item label="排序序号">
          <el-input-number v-model="form.display_order" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { rankApi } from '@/api'

const ranks = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)

const form = ref({
  name: '',
  min_score: 0,
  max_score: null as number | null,
  image_url: '',
  display_order: 1,
})

async function fetchRanks() {
  loading.value = true
  try {
    const response = await rankApi.list()
    ranks.value = response.data
  } catch (error) {
    ElMessage.error('获取段位列表失败')
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  isEdit.value = false
  editingId.value = null
  form.value = { name: '', min_score: 0, max_score: null, image_url: '', display_order: 1 }
  dialogVisible.value = true
}

function openEditDialog(row: any) {
  isEdit.value = true
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    if (isEdit.value && editingId.value !== null) {
      await rankApi.update(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await rankApi.create(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchRanks()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除段位「${row.name}」吗？`, '提示', {
      type: 'warning',
    })
    await rankApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchRanks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchRanks()
})
</script>

<style scoped>
.rank-manage {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
}
</style>
```

- [ ] **Step 2: 添加路由**

在 `repos/frontend/src/router/index.ts` 的 admin 路由数组中添加：

```typescript
{
  path: '/admin/ranks',
  name: 'RankManage',
  component: () => import('../views/admin/RankManage.vue'),
  meta: { requiresAuth: true, role: 'admin' }
}
```

- [ ] **Step 3: 确认菜单入口位置**

查看 `repos/frontend/src/` 目录下的侧边栏/菜单组件，找到管理员菜单配置位置，将 "/admin/ranks" 添加到菜单中。

---

## Task 7: 创建教师班级分值页面 (ClassScores.vue)

**Files:**
- Create: `repos/frontend/src/views/teacher/ClassScores.vue`
- Modify: `repos/frontend/src/router/index.ts` — 添加路由
- Modify: `repos/frontend/src/views/teacher/` 下的菜单/侧边栏 — 添加菜单入口

**Steps:**

- [ ] **Step 1: 创建 ClassScores.vue**

此页面显示学生段位，去掉编号和分值列，显示段位图片和距离升级所需分值：

```vue
<!-- repos/frontend/src/views/teacher/ClassScores.vue -->
<template>
  <div class="class-scores">
    <div class="filter-bar">
      <el-select v-model="selectedClass" placeholder="请选择班级" @change="onClassChange">
        <el-option v-for="cls in classes" :key="cls.id" :label="cls.name" :value="cls.id" />
      </el-select>
    </div>

    <div class="score-grid" v-loading="loading">
      <div v-for="student in students" :key="student.id" class="score-card">
        <div class="student-name">{{ student.name }}</div>
        <div class="rank-image">
          <img :src="student.rank_image" :alt="student.rank_name" />
        </div>
        <div class="rank-name">{{ student.rank_name }}</div>
        <div class="next-rank" v-if="student.next_rank_name">
          距「{{ student.next_rank_name }}」还差 {{ student.score_to_next }} 分
        </div>
        <div class="next-rank achieved" v-else>
          已达最高段位
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

interface Rank {
  id: number
  name: string
  min_score: number
  max_score: number | null
  image_url: string
  display_order: number
}

interface Student {
  id: number
  name: string
  student_no: string
  current_score: number
  rank_id: number
  rank_name: string
  rank_image: string
  next_rank_name: string | null
  score_to_next: number | null
}

const classes = ref<any[]>([])
const ranks = ref<Rank[]>([])
const students = ref<Student[]>([])
const loading = ref(false)
const selectedClass = ref<number | null>(null)

async function fetchClasses() {
  const response = await api.get('/teacher/classes')
  classes.value = response.data
  if (classes.value.length > 0) {
    selectedClass.value = classes.value[0].id
    await fetchStudents()
  }
}

async function fetchRanks() {
  const response = await api.get('/ranks')
  ranks.value = response.data
}

async function fetchStudents() {
  if (!selectedClass.value) return
  loading.value = true
  try {
    const response = await api.get('/students', {
      params: { class_id: selectedClass.value }
    })
    // 为每个学生计算段位信息
    students.value = response.data.map((s: any) => calculateRank(s))
  } catch (error) {
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

function calculateRank(student: any): Student {
  const score = student.current_score || 0
  const sortedRanks = [...ranks.value].sort((a, b) => a.display_order - b.display_order)

  let currentRank = sortedRanks[0]
  let nextRank: Rank | null = null

  for (let i = 0; i < sortedRanks.length; i++) {
    const rank = sortedRanks[i]
    const max = rank.max_score
    if (max === null) {
      // 无上限段位
      if (score >= rank.min_score) {
        currentRank = rank
        nextRank = null
      }
    } else if (score >= rank.min_score && score <= max) {
      currentRank = rank
      nextRank = sortedRanks[i + 1] || null
      break
    } else if (score > max) {
      currentRank = sortedRanks[i + 1] || rank
      nextRank = sortedRanks[i + 2] || null
    }
  }

  let scoreToNext: number | null = null
  if (nextRank) {
    scoreToNext = nextRank.min_score - score
  }

  return {
    ...student,
    rank_id: currentRank.id,
    rank_name: currentRank.name,
    rank_image: currentRank.image_url,
    next_rank_name: nextRank?.name || null,
    score_to_next: scoreToNext,
  }
}

function onClassChange() {
  fetchStudents()
}

onMounted(async () => {
  await fetchRanks()
  await fetchClasses()
})
</script>

<style scoped>
.class-scores {
  padding: 20px;
}

.filter-bar {
  margin-bottom: 20px;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.score-card {
  background: #f9fafb;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.student-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.rank-image {
  width: 80px;
  height: 80px;
  margin: 0 auto 8px;
}

.rank-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.rank-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.next-rank {
  font-size: 12px;
  color: #999;
}

.next-rank.achieved {
  color: #22c55e;
  font-weight: 500;
}
</style>
```

- [ ] **Step 2: 添加路由**

在 teacher 路由数组中添加：

```typescript
{
  path: '/teacher/class-scores',
  name: 'ClassScores',
  component: () => import('../views/teacher/ClassScores.vue'),
  meta: { requiresAuth: true, role: 'teacher' }
}
```

- [ ] **Step 3: 添加菜单入口**

找到 `repos/frontend/src/views/teacher/` 目录下的侧边栏或布局组件，将"班级分值"菜单添加到教师菜单中。

---

## Task 8: 配置 Docker 部署（图片持久化）

**Files:**
- Modify: `deploy/docker-compose.yml` 或相关 Docker 配置（如果存在）
- Create: `deploy/pics/docker-compose.yml` 说明

**Steps:**

- [ ] **Step 1: 在 deploy 目录创建 docker-compose 配置示例**

创建 `deploy/docker-compose.example.yml` 或更新现有的 Docker 配置，添加 pics 卷的持久化：

```yaml
# deploy/docker-compose.yml 示例
version: '3.8'
services:
  backend:
    image: mycourse-backend
    volumes:
      - ./db:/app/db
      - ./pics:/app/pics  # 段位图片持久化
    environment:
      - DATABASE_URL=sqlite:///db/mycourse.db
    ports:
      - "8000:8000"

  frontend:
    image: mycourse-frontend
    ports:
      - "80:80"

volumes:
  pics:
    driver: local
```

- [ ] **Step 2: 创建 pics 目录并放入图片**

```bash
mkdir -p deploy/pics
# 将 repos/pic/ 下的 1.png-6.png 复制到 deploy/pics/
cp repos/pic/*.png deploy/pics/
```

---

## Task 9: 验证所有功能

**Steps:**

- [ ] **Step 1: 启动后端验证 API**

```bash
cd D:/Learning/MyCourse/repos/backend
export JWT_SECRET_KEY=test-secret-key
python -c "from app.main import app; print('Backend OK')"
```

- [ ] **Step 2: 初始化段位数据**

```bash
cd D:/Learning/MyCourse/repos/backend && python scripts/init_ranks.py
```

- [ ] **Step 3: 验证前端编译**

```bash
cd D:/Learning/MyCourse/repos/frontend && npm run build
```
期望：无编译错误

- [ ] **Step 4: 整体检查清单**

- [ ] 分值明细页面时间显示正确（+8小时）
- [ ] 管理员可以 CRUD 段位数据
- [ ] 教师班级分值页面正确显示段位图片和升级进度
- [ ] Docker 部署时图片路径正确配置

---

## 依赖关系

```
Task 2 (Rank模型) → Task 3 (Rank路由) → Task 4 (初始化脚本)
Task 3 → Task 5 (前端API) → Task 6 (管理员页面) → Task 9
Task 3 → Task 5 → Task 7 (教师页面) → Task 9
Task 1 (时间修复) → Task 9
Task 8 (Docker配置) 可并行
```

---

## 备选执行方式

如果 Task 6 (管理员页面) 和 Task 7 (教师页面) 合并到现有页面（ConfigManage.vue 和 Scores.vue）而不是创建新文件，可减少文件数量，但会增加单个文件的复杂度。建议按本计划创建独立页面，保持清晰的分界。
