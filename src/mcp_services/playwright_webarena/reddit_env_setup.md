# WebArena Reddit环境搭建指南

本指南介绍如何搭建WebArena Reddit环境，用于Playwright MCP自动化测试。

## 系统要求

- Ubuntu 22.04+ 或其他Linux发行版
- Docker环境
- 至少50GB可用磁盘空间
- 至少4GB内存

## 快速设置步骤

### 1. 下载Reddit Docker镜像

WebArena提供3个镜像源，选择网络最快的：

```bash
# 选项1: Google Drive (通常最快)
pip install gdown
gdown 17Qpp1iu_mPqzgO_73Z9BnFjHrzmX9DGf

# 选项2: Archive.org
wget https://archive.org/download/webarena-env-forum-image/postmill-populated-exposed-withimg.tar

# 选项3: CMU服务器
wget http://metis.lti.cs.cmu.edu/webarena-images/postmill-populated-exposed-withimg.tar
```

### 2. 安装Docker (如果尚未安装)

```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

### 3. 启动Reddit环境

```bash
# 加载Docker镜像 (约50GB，需要等待几分钟)
docker load --input postmill-populated-exposed-withimg.tar

# 启动容器
docker run --name forum -p 9999:80 -d postmill-populated-exposed-withimg

# 等待服务启动 (约1-2分钟)
sleep 120

# 验证服务状态
docker logs forum | tail -10
curl -I http://localhost:9999
```

### 4. 验证环境

访问 `http://localhost:9999` 应该看到Postmill论坛主页，包含：
- 导航栏 (Forums, Wiki)
- 搜索框
- 登录/注册链接
- 论坛列表 (AskReddit, technology, gaming等)

## 端口开放策略

根据使用场景选择合适的端口开放策略：

### 策略1: GCP防火墙规则 (推荐 - 生产环境)

**适用场景**: 长期使用、团队协作、稳定的公共访问

```bash
# 安装gcloud CLI (如果尚未安装)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 认证
gcloud auth login

# 创建防火墙规则
gcloud compute firewall-rules create allow-reddit-9999 \
  --allow tcp:9999 \
  --source-ranges 0.0.0.0/0 \
  --description "Allow access to WebArena Reddit on port 9999"

# 获取外部IP
gcloud compute instances list
```

**优点**: 永久有效、稳定、无额外依赖  
**缺点**: 需要GCP权限、公网完全开放

### 策略2: ngrok隧道 (快速分享)

**适用场景**: 临时演示、快速测试、无需GCP权限

```bash
# 安装ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin

# 创建隧道
ngrok http 9999
```

**优点**: 即时生效、HTTPS支持、无需服务器配置  
**缺点**: 临时URL、需要保持运行、免费版有限制

### 策略3: Cloudflared隧道 (免费持久)

**适用场景**: 长期免费使用、无需GCP、需要稳定访问

```bash
# 安装cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# 创建临时隧道
cloudflared tunnel --url http://localhost:9999

# 或创建永久隧道 (需要Cloudflare账号)
cloudflared tunnel login
cloudflared tunnel create webarena-reddit
cloudflared tunnel route dns webarena-reddit reddit.yourdomain.com
```

**优点**: 免费、持久、自定义域名  
**缺点**: 需要Cloudflare账号、设置稍复杂

### 策略4: SSH端口转发 (开发调试)

**适用场景**: 本地开发、安全要求高、团队内部访问

```bash
# 在本地机器上执行
ssh -L 8080:localhost:9999 user@your-server-ip

# 然后访问 http://localhost:8080
```

**优点**: 最安全、无需开放公网端口  
**缺点**: 需要SSH访问、仅限本地使用

## Playwright MCP测试

环境搭建完成后，可以使用Playwright MCP进行自动化测试：

```javascript
// 基础连接测试
await page.goto('http://your-reddit-url:9999');

// 导航测试
await page.click('text=Forums');
await page.click('text=AskReddit');

// 表单交互测试
await page.click('text=Log in');
await page.fill('[placeholder="Username"]', 'testuser');
await page.fill('[placeholder="Password"]', 'testpass');
```

## 故障排除

### 容器启动失败
```bash
# 检查容器状态
docker ps -a

# 查看详细日志
docker logs forum

# 重启容器
docker restart forum
```

### 服务未就绪
```bash
# 检查PostgreSQL是否完全启动
docker logs forum | grep "database system is ready"

# 等待更长时间 (数据库恢复需要时间)
sleep 300
```

### 端口被占用
```bash
# 检查端口使用情况
netstat -tlnp | grep 9999

# 使用不同端口
docker run --name forum -p 8888:80 -d postmill-populated-exposed-withimg
```

## 环境重置

完成测试后重置环境：

```bash
# 停止并删除容器
docker stop forum
docker rm forum

# 重新启动
docker run --name forum -p 9999:80 -d postmill-populated-exposed-withimg
```

## 高级配置

### 环境变量设置 (WebArena标准)
```bash
export REDDIT="your-server-hostname:9999"
export REDDIT_URL="http://your-server-hostname:9999"
```

### 批量任务测试
```bash
# 准备WebArena测试配置
mkdir -p ~/.webarena
echo "REDDIT=your-server-hostname:9999" >> ~/.webarena/config
```

---

**注意**: 这个Reddit环境包含成千上万的预填充数据，完全模拟真实的Reddit使用场景，非常适合进行复杂的Web自动化任务测试。