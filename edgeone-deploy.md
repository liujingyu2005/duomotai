# 腾讯云EdgeOne部署指南

## 部署步骤

### 1. 准备代码仓库
- 将项目代码上传到GitHub/Gitee仓库
- 确保包含以下文件：
  - `Dockerfile`
  - `requirements.txt`
  - `app.py`
  - `backend/` 目录
  - `static/` 目录
  - `index.html`

### 2. EdgeOne控制台配置

#### 2.1 创建边缘函数应用
1. 登录腾讯云EdgeOne控制台
2. 选择"边缘函数"服务
3. 点击"新建应用"
4. 选择"容器镜像部署"模式

#### 2.2 配置应用信息
- **应用名称**: teaching-agent-ai
- **运行环境**: Python 3.11
- **部署方式**: 容器镜像

#### 2.3 镜像配置
- **镜像来源**: GitHub/Gitee
- **仓库地址**: [你的仓库地址]
- **Dockerfile路径**: Dockerfile
- **构建上下文**: 项目根目录

### 3. 环境变量配置
在EdgeOne控制台设置以下环境变量：

```bash
# 应用配置
APP_HOST=0.0.0.0
APP_PORT=5000
APP_DEBUG=false
DATABASE_PATH=instance/teaching_agent.db
REQUEST_TIMEOUT=60
LOG_LEVEL=INFO

# API密钥（可选，也可以在前端设置）
DEEPSEEK_API_KEY=your_deepseek_key
ZHIPU_API_KEY=your_zhipu_key
TYQW_API_KEY=your_tyqw_key
```

### 4. 域名配置
1. 在EdgeOne中添加自定义域名
2. 配置DNS解析指向EdgeOne
3. 启用HTTPS（自动配置SSL证书）

### 5. 部署验证
- 点击"部署"按钮
- 等待构建完成（约2-5分钟）
- 访问分配的域名或自定义域名
- 检查功能是否正常

## 部署优势

### EdgeOne特点
- **全球加速**: 自动CDN加速，访问速度快
- **自动扩容**: 根据访问量自动调整资源
- **高可用**: 多节点部署，服务稳定
- **免运维**: 无需管理服务器
- **HTTPS**: 自动配置SSL证书

### 成本优势
- 按量付费，使用多少付多少
- 免费额度：每月100万次请求
- 适合比赛项目展示

## 注意事项

1. **数据持久化**: EdgeOne是无状态服务，数据库文件会在重启后丢失
   - 建议使用云数据库或外部存储
   - 或接受数据丢失（演示项目）

2. **API密钥安全**: 
   - 建议在前端设置API密钥
   - 避免在代码中硬编码

3. **性能优化**:
   - 图片大小限制为5MB
   - 建议压缩静态资源

4. **访问限制**:
   - 检查CORS配置
   - 确保API域名在白名单中

## 故障排查

### 常见问题
1. **部署失败**: 检查Dockerfile和依赖包
2. **访问超时**: 检查端口配置和网络策略
3. **功能异常**: 查看边缘函数日志

### 监控指标
- 请求成功率
- 响应时间
- 错误日志
- 资源使用情况

## 快速部署命令

如果使用CLI工具：
```bash
# 安装EdgeOne CLI
npm install -g @tencent-cloud/edgeone-cli

# 登录
eo login

# 部署
eo deploy --app teaching-agent-ai --source .
```

部署完成后，你将获得一个类似 `https://your-app.edgeone.tencent.com` 的访问链接。
