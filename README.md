# ECS Health Check Monitoring Project

A production-grade Flask application deployed to AWS ECS that demonstrates operational resilience, health checks, and automated failure recovery.

---

## ⚠️ Security Note

**Never commit or share:**
- AWS Account IDs
- Subnet IDs
- Security Group IDs
- Task ARNs with your account ID
- AWS credentials or access keys
- Any other AWS resource IDs

All placeholder values in this README (like `YOUR_ACCOUNT_ID`, `subnet-ID`, `sg-ID`) should be replaced with your actual values locally, but **never committed to GitHub**.

## 🎯 Project Goal

Build a real system that:
- ✅ Runs on AWS ECS (Fargate)
- ✅ Implements health checks (ALB + ECS)
- ✅ Monitors with CloudWatch
- ✅ Auto-restarts on failure
- ✅ Tests failure scenarios

**Why this matters:** Most engineers learn "systems fail" the hard way. This project teaches operational thinking: design for failure recovery, monitor what matters, keep humans in the loop.

---

## 🏗️ Architecture

```
Your Local Machine (Mac)
    ↓
    | Code (Flask app)
    ↓
GitHub (Version control)
    ↓
AWS ECR (Docker image registry)
    ↓
AWS ECS Fargate (Runs containers)
    ├─ Task Definition (How to run the app)
    ├─ Health Checks (Is the app alive?)
    ├─ Service (Keep desired count running)
    └─ CloudWatch (Monitoring & Alarms)
    
CloudWatch
    ├─ Logs (/ecs/my-health-check)
    ├─ Metrics (CPU, Memory, Task Count)
    └─ Alarms (Alert if tasks < 1)
```

**Flow:**
1. User visits the app
2. Request hits the app on port 5000
3. App returns a response
4. CloudWatch logs the request
5. ECS health check validates the app is healthy
6. If health check fails, ECS restarts the task
7. CloudWatch alarms notify if something is wrong

---

## 🛠️ Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Application** | Python Flask | Simple web app that responds to requests |
| **Containerization** | Docker | Package app for cloud deployment |
| **Container Registry** | AWS ECR | Store Docker images |
| **Container Orchestration** | AWS ECS Fargate | Run and manage containers |
| **Monitoring** | CloudWatch | Logs, metrics, alarms |
| **Networking** | AWS VPC | Private network, subnets, security groups |
| **Infrastructure** | AWS CLI | Define and manage all resources |

---

## 📦 What's in This Repository

```
ecs-monitoring-project/
├── app/
│   ├── app.py              # Flask application
│   └── requirements.txt     # Python dependencies
├── Dockerfile              # Docker image definition
├── task-definition.json    # ECS task configuration (template)
├── trust-policy.json       # IAM trust policy (template)
├── FAILURE_TEST_RESULTS.md # Test results (auto-recovery proof)
├── README.md              # This file
├── .gitignore            # Git ignore rules
└── .env.example          # Environment variables template (DO NOT commit .env)
```

### .gitignore

Always include a `.gitignore` to prevent accidental commits of sensitive data:

```
# AWS credentials and resource IDs (NEVER commit these)
.aws/
*.pem
*.key
.env
.env.local

# Files with real AWS resource IDs (use -template.json versions instead)
task-definition-prod.json
task-definition-real.json

# OS files
.DS_Store
*.swp
*~

# Python
__pycache__/
*.py[cod]
*$py.class
.venv
venv/

# IDE
.vscode/
.idea/
*.sublime-*
```

---

## 🚀 Deployment Guide

### Prerequisites

- AWS Account (free tier eligible)
- macOS/Linux/Windows with terminal
- Docker installed (`brew install docker` on Mac)
- AWS CLI installed (`brew install awscli` on Mac)
- Git installed

### Step 1: Build Docker Image

```bash
# Build for Linux (AWS uses AMD64)
docker build --platform linux/amd64 -t my-health-check-app:1.0 .

# Verify
docker images
```

### Step 2: Push to AWS ECR

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name my-health-check-app \
  --region us-east-1

# Login to ECR (replace YOUR_ACCOUNT_ID with your actual AWS account ID)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag image for ECR
docker tag my-health-check-app:1.0 \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/my-health-check-app:1.0

# Push to ECR
docker push \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/my-health-check-app:1.0
```

**Note:** Replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID (visible in AWS Console → Account)

### Step 3: Create ECS Infrastructure

```bash
# Create cluster
aws ecs create-cluster \
  --cluster-name my-monitoring-cluster \
  --region us-east-1

# Create CloudWatch log group
aws logs create-log-group \
  --log-group-name /ecs/my-health-check \
  --region us-east-1

# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region us-east-1

# Create VPC, subnet, security group
# (See Phase 2 of deployment guide for details)

# Create ECS service (replace subnet-ID and sg-ID with your actual values)
aws ecs create-service \
  --cluster my-monitoring-cluster \
  --service-name my-health-check-service \
  --task-definition my-health-check-task:1 \
  --launch-type FARGATE \
  --desired-count 1 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-ID],securityGroups=[sg-ID],assignPublicIp=ENABLED}" \
  --region us-east-1
```

**Note:** 
- Replace `subnet-ID` with your subnet ID (e.g., `subnet-0f21c9a95634bbc73`)
- Replace `sg-ID` with your security group ID (e.g., `sg-12345678`)

---

## 🏥 Health Checks Explained

### What is a Health Check?

A health check is a question ECS asks your app every 5 seconds: **"Are you healthy?"**

**Your app responds:**
- ✅ **200 (Success):** "Yes, I'm healthy"
- ❌ **500 (Error):** "No, I'm broken"

### Configuration

```json
{
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
    "interval": 5,        // Check every 5 seconds
    "timeout": 2,         // Wait max 2 seconds for response
    "retries": 3,         // 3 failures = unhealthy
    "startPeriod": 10     // Grace period at startup
  }
}
```

### What Happens When Health Check Fails

```
Attempt 1: Fails
Attempt 2: Fails
Attempt 3: Fails ← Task marked UNHEALTHY
    ↓
ECS detects unhealthy task
    ↓
ECS stops the task
    ↓
ECS starts a new task
    ↓
New task runs health checks
    ↓
New task marked HEALTHY
    ↓
Service back to normal
```

**Time:** ~30-60 seconds from failure to recovery

---

## 📊 Monitoring with CloudWatch

### Metrics Available

| Metric | Meaning |
|--------|---------|
| **RunningCount** | Number of tasks currently running |
| **DesiredCount** | Number of tasks you want running |
| **PendingCount** | Number of tasks starting up |
| **CPUUtilization** | Percentage of CPU being used |
| **MemoryUtilization** | Percentage of memory being used |

### View Logs

```bash
# Stream logs in real-time
aws logs tail /ecs/my-health-check --follow

# View logs for past hour
aws logs tail /ecs/my-health-check --since 1h
```

### Example Log Output

```
2026-05-03T14:00:05.123456Z Task started
2026-05-03T14:00:06.234567Z Starting Flask application on port 5000
2026-05-03T14:00:10.345678Z Health check requested
2026-05-03T14:00:10.456789Z Health check: status=healthy
2026-05-03T14:00:15.567890Z Health check requested
2026-05-03T14:00:15.678901Z Health check: status=healthy
```

---

## 🧪 Testing Failure Scenarios

### Scenario 1: Stop a Running Task

```bash
# Get task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster my-monitoring-cluster \
  --service-name my-health-check-service \
  --region us-east-1 \
  --query 'taskArns[0]' \
  --output text | cut -d'/' -f3)

# Stop the task
aws ecs stop-task \
  --cluster my-monitoring-cluster \
  --task $TASK_ID \
  --region us-east-1

# Watch recovery
aws ecs describe-services \
  --cluster my-monitoring-cluster \
  --services my-health-check-service \
  --region us-east-1 \
  --query 'services[0].[runningCount, desiredCount, pendingCount]'
```

**Expected behavior:**
- Immediately: `runningCount: 0` (task stopped)
- After 30 sec: `runningCount: 1, pendingCount: 1` (new task starting)
- After 60 sec: `runningCount: 1, pendingCount: 0` (new task healthy)

### Scenario 2: Check Health Checks

```bash
# Tail logs to see health checks in action
aws logs tail /ecs/my-health-check --follow

# You'll see entries like:
# Health check: GET /health -> 200 OK
# Health check: GET /health -> 200 OK
```

---

## 📈 Key Learnings

### 1. Health Checks Are Critical

Without health checks:
- ❌ App crashes, requests fail, users upset, you don't know why

With health checks:
- ✅ App crashes, ECS notices in 5 seconds, new task starts, users don't notice

### 2. Monitoring Shows Everything

CloudWatch shows:
- Is the app healthy? (Task count)
- Is it under load? (CPU/Memory)
- What's happening inside? (Logs)

Without monitoring:
- ❌ You don't know the app is broken until users complain

With monitoring:
- ✅ You know there's a problem before users do

### 3. Automation Beats Manual Fixes

Without automation:
- ❌ App crashes → Pager goes off → You wake up at 3am → You restart it

With automation:
- ✅ App crashes → ECS restarts it → You get a Slack notification in the morning

### 4. Design for Failure

Most engineers ask: "Will this work?"
Good engineers ask: "What breaks and how do we recover?"

This project teaches the second way of thinking.

---

## 🔍 What Each File Does

### `app/app.py`
Flask web application with three endpoints:
- `/health` → Health check (used by ECS)
- `/api/message` → Application endpoint (what users call)
- `/simulate-failure` → For testing (makes health check fail)

### `app/requirements.txt`
Lists Python dependencies:
- Flask (web framework)
- Werkzeug (WSGI utilities)

### `Dockerfile`
Instructions for Docker to build the image:
1. Start with Python 3.11 base image
2. Install dependencies
3. Copy application code
4. Run the app when container starts

### `task-definition.json`
Tells ECS how to run the app:
- Which Docker image to use
- How much CPU/memory to give it
- Where to send logs
- How to check if it's healthy
- What port to listen on

---

## 🎓 What This Project Teaches

| Concept | What You Learn |
|---------|----------------|
| **Containers** | How to package code for cloud |
| **Orchestration** | How ECS manages running containers |
| **Health Checks** | How systems detect failures automatically |
| **Monitoring** | How to observe what's happening |
| **Auto-Recovery** | How systems heal themselves |
| **Infrastructure as Code** | How to define infrastructure with commands |
| **DevOps Thinking** | How to design for reliability, not just features |

---

## 🚀 Next Steps

### Extend This Project

1. **Add Load Balancer (ALB)**
   - Route traffic to the app
   - Distribute load across multiple tasks

2. **Add Database**
   - RDS PostgreSQL
   - Show how to connect containerized app to managed database

3. **Add Secrets Management**
   - Store credentials securely
   - Don't hardcode sensitive data

4. **Add Multi-Region**
   - Deploy same infrastructure in multiple AWS regions
   - Learn about distributed systems

5. **Add CI/CD Pipeline**
   - Automatically build and push new images
   - Deploy automatically when code changes

### For Interview Preparation

This project demonstrates:
- ✅ Can deploy to cloud ✅ Understand containerization
- ✅ Know operational thinking
- ✅ Can test failure scenarios
- ✅ Understand monitoring
- ✅ Can work with AWS

**Interview talking point:**
> "I deployed a Flask app to ECS with health checks and CloudWatch monitoring. I tested failure scenarios—stopped a running task and watched ECS auto-restart it in 30 seconds. This taught me that operational resilience requires design and testing, not luck."

---

## 📚 Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Docker Documentation](https://docs.docker.com/)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

## 💡 Key Takeaway

This isn't just a project. It's learning how production systems actually work.

**Most engineers learn this in their first on-call shift at 3am.**

You're learning it proactively, with your own system, where failure doesn't matter.

That's the difference between junior and thoughtful junior.

---

## 📞 Troubleshooting

### Task won't start?
- Check CloudWatch logs: `aws logs tail /ecs/my-health-check --follow`
- Verify Docker image was pushed: `aws ecr list-images --repository-name my-health-check-app`
- Check security group allows port 5000

### Health checks failing?
- Check app is running: `curl http://localhost:5000/health` (locally)
- Check CloudWatch logs for errors
- Verify health check command in task definition

### Can't access the app?
- Is the task running? `aws ecs describe-services --cluster my-monitoring-cluster --services my-health-check-service --region us-east-1`
- Is the security group allowing traffic on port 5000?
- What's the task's IP address? Look in ECS console → Tasks

---

## 📄 License

This is a learning project. Use it for educational purposes.

---

## 👨‍💻 Author

Built as a learning project to understand ECS, health checks, and operational resilience.

---

## 🎉 Credits

This project was built step-by-step to understand:
- How containers work
- How cloud platforms manage applications
- How monitoring enables reliability
- How to design systems that fail gracefully

Every line of code, every AWS command, every test was intentional. That's the point.