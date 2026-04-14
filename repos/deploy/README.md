# Class Score 部署说明

## 环境要求

- Python 3.10+
- Node.js 18+
- Nginx

## 目录结构

```
/opt/class-score/
├── frontend/              # npm build 产物（静态资源）
├── backend/               # Python 代码
├── db/                    # SQLite .db 文件
└── nginx.conf             # Nginx 配置
```

## 前端构建步骤

1. 进入前端目录：
   ```bash
   cd repos/frontend
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 构建生产版本：
   ```bash
   npm run build
   ```

4. 将构建产物复制到部署目录：
   ```bash
   cp -r dist/* /opt/class-score/frontend/
   ```

## 后端启动步骤

1. 进入后端目录：
   ```bash
   cd repos/backend
   ```

2. 创建虚拟环境（推荐）：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   ```bash
   export JWT_SECRET_KEY="your-secret-key-here"  # Linux/Mac
   # set JWT_SECRET_KEY=your-secret-key-here  # Windows
   ```

5. 创建数据库目录：
   ```bash
   mkdir -p /opt/class-score/db
   ```

6. 初始化数据库（如需要）：
   ```bash
   python -m app.db.init_db
   ```

7. 后台运行 uvicorn：
   ```bash
   nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/class-score.log 2>&1 &
   ```

## Nginx 配置步骤

1. 复制 Nginx 配置文件到系统配置目录：
   ```bash
   sudo cp /opt/class-score/nginx.conf /etc/nginx/sites-available/class-score
   sudo ln -s /etc/nginx/sites-available/class-score /etc/nginx/sites-enabled/
   ```

2. 测试配置：
   ```bash
   sudo nginx -t
   ```

3. 重载 Nginx：
   ```bash
   sudo systemctl reload nginx
   ```

4. 或重启 Nginx：
   ```bash
   sudo systemctl restart nginx
   ```

## 环境变量配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| JWT_SECRET_KEY | JWT 签名密钥 | `your-super-secret-key-min-32-chars` |

## 启动命令汇总

```bash
# 1. 构建前端
cd repos/frontend && npm run build && cp -r dist/* /opt/class-score/frontend/

# 2. 启动后端（后台运行）
cd repos/backend && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/class-score.log 2>&1 &

# 3. 配置并启动 Nginx
sudo cp /opt/class-score/nginx.conf /etc/nginx/sites-available/class-score
sudo ln -s /etc/nginx/sites-available/class-score /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 验证部署

1. 检查后端是否运行：
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```

2. 检查 Nginx 是否正常：
   ```bash
   curl http://localhost/
   ```

3. 查看日志：
   ```bash
   tail -f /var/log/class-score.log
   ```
