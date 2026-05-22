# 实时排名班级选择权限控制实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现实时排名页面的班级选择权限控制：admin看到所有班级，teacher只能看到自己关联的班级

**Architecture:** 后端新增 `/api/rankings/classes` 接口根据用户角色返回不同范围的班级列表；前端修改 Rankings.vue 调用新接口

**Tech Stack:** FastAPI (Python), Vue 3 + TypeScript, SQLAlchemy

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `repos/backend/app/routers/ranking_router.py` | 新增 `/api/rankings/classes` 接口 |
| `repos/frontend/src/views/teacher/Rankings.vue` | 调用新接口获取班级列表 |

---

## Task 1: 后端新增 Rankings Classes 接口

**Files:**
- Modify: `repos/backend/app/routers/ranking_router.py`
- Test: `repos/backend/tests/test_scores.py` (复用现有测试模式)

- [ ] **Step 1: 添加 get_rankings_classes 函数**

在 `ranking_router.py` 文件末尾添加以下代码：

```python
@router.get("/classes")
def get_rankings_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前用户可访问的班级列表

    - admin: 返回所有班级
    - teacher: 返回仅关联的班级

    返回：
        List[ClassBasic]: 班级基本信息列表
    """
    from app.schemas.class_schema import ClassBasic
    from app.models.models import TeacherClass

    if current_user["role"] == "admin":
        # admin: 查询所有班级
        classes = db.query(ClassModel).all()
    else:
        # teacher: 只查询关联的班级
        teacher_id = current_user["id"]
        teacher_classes = db.query(TeacherClass).filter(
            TeacherClass.teacher_id == teacher_id
        ).all()
        class_ids = [tc.class_id for tc in teacher_classes]
        classes = db.query(ClassModel).filter(
            ClassModel.id.in_(class_ids)
        ).all()

    return [
        ClassBasic(id=c.id, name=c.name, code=c.code)
        for c in classes
    ]
```

- [ ] **Step 2: 验证后端服务运行中**

运行：`curl http://127.0.0.1:8000/api/v1/rankings/classes -H "Authorization: Bearer <admin_token>"`
预期：admin 返回所有班级列表

运行：`curl http://127.0.0.1:8000/api/v1/rankings/classes -H "Authorization: Bearer <teacher_token>"`
预期：teacher 返回仅关联的班级列表

- [ ] **Step 3: 提交代码**

```bash
git add repos/backend/app/routers/ranking_router.py
git commit -m "feat: add /api/rankings/classes endpoint for permission-based class list"
```

---

## Task 2: 前端修改 Rankings.vue

**Files:**
- Modify: `repos/frontend/src/views/teacher/Rankings.vue:134-144`

- [ ] **Step 1: 修改 fetchClasses 函数调用新接口**

将 `fetchClasses` 函数中的：
```typescript
const response = await api.get('/classes')
```

修改为：
```typescript
const response = await api.get('/rankings/classes')
```

- [ ] **Step 2: 验证前端页面**

1. admin 登录后访问 Rankings 页面，检查班级下拉框显示所有班级
2. teacher 登录后访问 Rankings 页面，检查班级下拉框只显示关联的班级

- [ ] **Step 3: 提交代码**

```bash
git add repos/frontend/src/views/teacher/Rankings.vue
git commit -m "feat: Rankings page fetches classes from /api/rankings/classes for permission control"
```

---

## 验证清单

| 验证项 | admin | teacher |
|--------|-------|---------|
| 班级下拉框选项数量 | 所有班级 | 仅关联班级 |
| 默认选中第一个班级 | ✓ | ✓ |
| 排名数据正确显示 | ✓ | ✓ |
