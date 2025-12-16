# AI Market Radar

## 简介 (Introduction)
AI Market Radar 是一个 AI 驱动的市场情报分析平台，旨在帮助开发者和投资人从海量信息中筛选出高价值的科技产品、创业公司和技术趋势。

## 核心功能 (Core Features)
1.  **多源数据采集 (Ingestion)**: 自动抓取 Product Hunt, Hacker News, TechCrunch, Github Trending 等源头数据。
2.  **AI 智能清洗与分析 (AI Analysis)**:
    *   **降噪**: 过滤无关信息。
    *   **深度分析**: 利用 LLM (GPT-4/Gemini/Claude) 分析商业模式、技术壁垒和投资潜力。
    *   **分类与打分**: 自动打标签并计算关注指数。
3.  **情报仪表盘 (Dashboard)**: 高密度的信息展示界面，支持筛选、搜索和详情查看。

## 技术栈 (Tech Stack)

### Backend (Data Pipeline & API)
- **Language**: Python 3.x
- **Framework**: FastAPI
- **AI/Agent**: LangChain / LlamaIndex
- **Crawling**: Playwright / BeautifulSoup
- **Database**: PostgreSQL (with pgvector for semantic search)

### Frontend (User Interface)
- **Framework**: Next.js (React)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui

## 目录结构 (Structure)
- `/backend`: Python 后端代码、ETL 脚本、AI Agent 逻辑。
- `/frontend`: Next.js 前端应用。
