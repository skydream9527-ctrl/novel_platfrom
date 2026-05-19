# Novel Platform 设计文档 V4

> 版本：4.0
> 日期：2025-01-20
> 状态：待审阅

---

## 目录

- [第一阶段：核心增强](#第一阶段核心增强)
  - [1.1 双向链接系统](#11-双向链接系统)
  - [1.2 标签系统](#12-标签系统)
  - [1.3 多视图切换](#13-多视图切换)
  - [1.4 写作目标与字数统计](#14-写作目标与字数统计)
  - [1.5 章节自定义属性](#15-章节自定义属性)
- [第二阶段：可视化](#第二阶段可视化)
  - [2.1 知识图谱增强](#21-知识图谱增强)
  - [2.2 大纲编辑器](#22-大纲编辑器)
  - [2.3 时间线编辑器](#23-时间线编辑器)
- [第三阶段：协作与深度](#第三阶段协作与深度)
  - [3.1 评论批注系统](#31-评论批注系统)
  - [3.2 世界观设定管理](#32-世界观设定管理)
  - [3.3 冲突伏笔追踪](#33-冲突伏笔追踪)
  - [3.4 审阅模式](#34-审阅模式)

---

## 第一阶段：核心增强

### 1.1 双向链接系统

#### 概述
借鉴 Obsidian 的 `[[wiki link]]` 语法，实现章节、角色、笔记之间的双向链接。当引用被修改时，所有引用处自动更新。

#### 数据模型

```sql
-- 链接关系表（新建）
CREATE TABLE links (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    source_type VARCHAR(20) NOT NULL,  -- 'chapter' | 'note' | 'character' | 'source'
    source_id INTEGER NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id INTEGER NOT NULL,
    anchor_text VARCHAR(500),          -- 链接显示文本
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, source_type, source_id, target_type, target_id)
);

-- 索引
CREATE INDEX idx_links_source ON links(source_type, source_id);
CREATE INDEX idx_links_target ON links(target_type, target_id);
```

#### 语法规范

```
[[章节名]]              → 链接到章节
[[章节名#段落锚点]]     → 链接到章节具体位置
[[角色:角色名]]         → 链接到角色
[[笔记:笔记名]]         → 链接到笔记
[[素材:素材名]]         → 链接到素材
```

#### API 接口

```
GET    /api/v1/links/by-task/{task_id}           # 获取任务下所有链接
GET    /api/v1/links/backlinks/{type}/{id}        # 获取反向链接（谁引用了我）
POST   /api/v1/links/parse                        # 解析内容中的链接语法
DELETE /api/v1/links/{link_id}                    # 删除链接
```

#### 前端交互

1. **编辑器内**
   - 输入 `[[` 时弹出候选列表（章节/角色/笔记/素材）
   - 已识别的链接显示为可点击的高亮文本
   - 悬停显示目标内容预览

2. **反向链接面板**
   - 在章节/角色/笔记详情页显示"被引用于"列表
   - 点击可跳转到引用位置

3. **链接自动维护**
   - 重命名章节/角色时，自动更新所有引用
   - 删除目标时，标记链接为断开状态

---

### 1.2 标签系统

#### 概述
为章节、笔记、素材添加标签，支持快速筛选和分类。

#### 数据模型

```sql
-- 标签表（新建）
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7),           -- HEX颜色值
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, name)
);

-- 内容标签关联表（新建）
CREATE TABLE content_tags (
    id INTEGER PRIMARY KEY,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL,  -- 'chapter' | 'note' | 'source'
    content_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tag_id, content_type, content_id)
);

-- 索引
CREATE INDEX idx_content_tags_content ON content_tags(content_type, content_id);
CREATE INDEX idx_content_tags_tag ON content_tags(tag_id);
```

#### API 接口

```
GET    /api/v1/tags/by-task/{task_id}              # 获取任务下所有标签
POST   /api/v1/tags/                               # 创建标签
PATCH  /api/v1/tags/{tag_id}                       # 更新标签（名称/颜色）
DELETE /api/v1/tags/{tag_id}                       # 删除标签
POST   /api/v1/tags/assign                         # 为内容添加标签
DELETE /api/v1/tags/unassign                       # 移除内容标签
GET    /api/v1/tags/{tag_id}/content               # 获取标签下的所有内容
```

#### 前端交互

1. **标签管理器**
   - 在侧边栏新增"标签"Tab
   - 支持创建、编辑、删除、批量管理
   - 标签云展示（按使用频率缩放）

2. **内容标签编辑**
   - 章节/笔记/素材详情页显示标签区域
   - 输入框支持自动补全已有标签
   - 点击标签可快速筛选相关内容

3. **标签筛选**
   - 在章节列表、笔记列表顶部添加标签筛选器
   - 支持多标签组合筛选（AND/OR）
   - 保存常用筛选条件

---

### 1.3 多视图切换

#### 概述
章节列表支持多种视图模式，适应不同创作阶段的管理需求。

#### 视图类型

| 视图 | 说明 | 适用场景 |
|------|------|----------|
| **列表视图** | 传统列表，显示标题、字数、状态 | 日常编辑 |
| **看板视图** | 按状态分列（待写/草稿/初稿/定稿） | 进度管理 |
| **日历视图** | 按创建/更新日期展示 | 时间规划 |
| **时间线视图** | 按章节顺序横向展示 | 故事结构 |

#### 数据模型扩展

在章节表添加状态字段：

```sql
-- 章节表修改
ALTER TABLE chapters ADD COLUMN status VARCHAR(20) DEFAULT 'draft';
-- 状态值：'idea'(构思) | 'outline'(大纲) | 'draft'(草稿) | 'revision'(修订) | 'final'(定稿)

ALTER TABLE chapters ADD COLUMN scheduled_date DATE;  -- 计划完成日期
ALTER TABLE chapters ADD COLUMN completed_date DATE;  -- 实际完成日期
```

#### API 接口

```
GET /api/v1/chapters/by-task/{task_id}?view=list|kanban|calendar|timeline
GET /api/v1/chapters/by-task/{task_id}/stats          # 获取各状态章节数量
PATCH /api/v1/chapters/{chapter_id}/status            # 批量更新章节状态
PATCH /api/v1/chapters/reorder                        # 批量更新章节顺序
```

#### 前端交互

1. **视图切换器**
   - 在章节列表顶部添加视图切换按钮
   - 记住用户最后使用的视图偏好

2. **看板视图**
   - 拖拽章节卡片改变状态
   - 每列显示章节计数
   - 卡片显示：标题、字数、标签、进度

3. **日历视图**
   - 月视图展示章节的创建/更新/计划日期
   - 拖拽调整计划日期
   - 点击日期查看当天相关章节

4. **时间线视图**
   - 横向滚动的时间轴
   - 章节按顺序排列，显示字数柱状图
   - 支持缩放（按章节/按卷/全部）

---

### 1.4 写作目标与字数统计

#### 概述
设定写作目标，追踪创作进度，分析写作习惯。

#### 数据模型

```sql
-- 写作目标表（新建）
CREATE TABLE writing_goals (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    goal_type VARCHAR(20) NOT NULL,     -- 'daily' | 'weekly' | 'total'
    target_words INTEGER NOT NULL,       -- 目标字数
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 写作记录表（新建）
CREATE TABLE writing_logs (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    chapter_id INTEGER REFERENCES chapters(id),
    words_written INTEGER NOT NULL,      -- 本次写字数
    duration_seconds INTEGER,            -- 写作时长（秒）
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_writing_logs_task ON writing_logs(task_id, recorded_at);
CREATE INDEX idx_writing_logs_chapter ON writing_logs(chapter_id);
```

#### API 接口

```
GET    /api/v1/writing-goals/by-task/{task_id}       # 获取写作目标
POST   /api/v1/writing-goals/                        # 创建目标
PATCH  /api/v1/writing-goals/{goal_id}               # 更新目标
DELETE /api/v1/writing-goals/{goal_id}               # 删除目标

GET    /api/v1/writing-stats/by-task/{task_id}       # 获取统计数据
GET    /api/v1/writing-stats/by-task/{task_id}/daily  # 每日字数统计
GET    /api/v1/writing-stats/by-task/{task_id}/weekly # 每周统计
GET    /api/v1/writing-stats/streak                   # 连续写作天数
```

#### 统计指标

| 指标 | 说明 |
|------|------|
| 今日字数 | 今天写的总字数 |
| 本周字数 | 本周写的总字数 |
| 连续天数 | 连续写作的天数 |
| 平均速度 | 每小时平均写字数 |
| 总字数 | 项目总字数 |
| 完成率 | 目标完成百分比 |

#### 前端交互

1. **目标设置**
   - 在项目设置中添加"写作目标"区域
   - 支持设置每日/每周/总字数目标
   - 可视化进度条

2. **仪表盘统计卡片**
   - 在 Dashboard 添加写作统计卡片
   - 热力图展示每日写作量（类似 GitHub 贡献图）
   - 折线图展示字数趋势

3. **实时统计**
   - 编辑器底部状态栏显示：当前章节字数、今日字数、目标进度
   - 编辑时实时更新字数

4. **成就系统（可选）**
   - 连续写作徽章
   - 字数里程碑徽章
   - 首次完成目标徽章

---

### 1.5 章节自定义属性

#### 概述
为章节添加自定义字段，支持结构化元数据管理。

#### 数据模型

```sql
-- 属性定义表（新建）
CREATE TABLE attribute_definitions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    name VARCHAR(50) NOT NULL,
    field_type VARCHAR(20) NOT NULL,    -- 'text' | 'number' | 'select' | 'multi_select' | 'date' | 'checkbox' | 'url'
    options TEXT,                        -- JSON数组，select/multi_select的选项
    default_value TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, name)
);

-- 属性值表（新建）
CREATE TABLE attribute_values (
    id INTEGER PRIMARY KEY,
    definition_id INTEGER NOT NULL REFERENCES attribute_definitions(id) ON DELETE CASCADE,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(definition_id, chapter_id)
);

-- 索引
CREATE INDEX idx_attribute_values_chapter ON attribute_values(chapter_id);
```

#### 预设属性模板

| 属性名 | 类型 | 选项 | 说明 |
|--------|------|------|------|
| POV角色 | select | (从角色列表动态生成) | 本章视角角色 |
| 情绪基调 | select | 轻松/紧张/悲伤/欢快/压抑/激昂 | 章节氛围 |
| 故事线 | select | 主线/支线A/支线B/... | 所属故事线 |
| 时间段 | text | - | 故事内时间（如"第三天下午"） |
| 地点 | text | - | 故事发生地点 |
| 出场角色 | multi_select | (从角色列表动态生成) | 本章出场角色 |
| 完成度 | number | - | 0-100% |
| 是否审阅 | checkbox | - | 是否已审阅 |

#### API 接口

```
GET    /api/v1/attributes/definitions/by-task/{task_id}   # 获取属性定义
POST   /api/v1/attributes/definitions                     # 创建属性定义
PATCH  /api/v1/attributes/definitions/{def_id}            # 更新属性定义
DELETE /api/v1/attributes/definitions/{def_id}            # 删除属性定义

GET    /api/v1/attributes/values/by-chapter/{chapter_id}  # 获取章节属性值
PUT    /api/v1/attributes/values/batch                    # 批量更新属性值
GET    /api/v1/attributes/values/filter                   # 按属性筛选章节
```

#### 前端交互

1. **属性管理器**
   - 在项目设置中添加"自定义属性"区域
   - 拖拽排序属性
   - 预设模板一键导入

2. **章节属性面板**
   - 在章节编辑区右侧或底部显示属性面板
   - 根据字段类型渲染不同输入控件
   - 自动保存

3. **属性筛选**
   - 章节列表支持按属性筛选
   - 组合筛选条件
   - 保存筛选视图

---

## 第二阶段：可视化

### 2.1 知识图谱增强

#### 概述
增强现有的角色关系图谱，支持可视化所有内容类型之间的关系。

#### 节点类型

| 节点 | 颜色 | 图标 | 说明 |
|------|------|------|------|
| 章节 | 蓝色 | 📄 | 章节节点 |
| 角色 | 绿色 | 👤 | 角色节点 |
| 笔记 | 黄色 | 📝 | 笔记节点 |
| 素材 | 紫色 | 📎 | 素材节点 |
| 标签 | 灰色 | 🏷️ | 标签节点 |

#### 边类型

| 关系 | 样式 | 说明 |
|------|------|------|
| 引用 | 实线 | 双向链接建立的引用 |
| 出场 | 虚线 | 角色在章节中出场 |
| 标签 | 点线 | 内容拥有相同标签 |
| 属于 | 实线 | 笔记属于某分类 |
| 关联 | 实线 | 角色之间的关系 |

#### 筛选与交互

```
筛选维度：
- 按内容类型（章节/角色/笔记/素材）
- 按标签
- 按关联深度（1跳/2跳/3跳）
- 按时间范围

交互操作：
- 点击节点：高亮相邻节点，显示详情面板
- 双击节点：跳转到该内容
- 拖拽节点：调整布局
- 滚轮缩放：放大缩小
- 搜索：按名称定位节点
```

#### 前端实现

使用 **Cytoscape.js** 或 **React Flow** 实现：

```typescript
interface GraphNode {
  id: string;
  type: 'chapter' | 'character' | 'note' | 'source' | 'tag';
  label: string;
  data: any;
  position: { x: number; y: number };
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'reference' | 'appearance' | 'tag' | 'belongs_to' | 'relation';
  label?: string;
}
```

#### API 接口

```
GET /api/v1/graph/by-task/{task_id}                  # 获取完整图数据
GET /api/v1/graph/by-task/{task_id}?type=chapter     # 按类型筛选
GET /api/v1/graph/neighbors/{type}/{id}?depth=2      # 获取邻居节点
GET /api/v1/graph/path/{from_type}/{from_id}/{to_type}/{to_id}  # 查找路径
```

---

### 2.2 大纲编辑器

#### 概述
树形大纲结构，支持无限层级嵌套，用于故事结构规划。

#### 数据模型

```sql
-- 大纲节点表（新建）
CREATE TABLE outline_nodes (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    parent_id INTEGER REFERENCES outline_nodes(id) ON DELETE CASCADE,
    chapter_id INTEGER REFERENCES chapters(id),       -- 关联到实际章节（可空）
    title VARCHAR(200) NOT NULL,
    summary TEXT,                                      -- 节点摘要/备注
    node_type VARCHAR(20) DEFAULT 'node',             -- 'root' | 'act' | 'chapter' | 'scene' | 'node'
    sort_order INTEGER DEFAULT 0,
    is_collapsed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_outline_nodes_task ON outline_nodes(task_id);
CREATE INDEX idx_outline_nodes_parent ON outline_nodes(parent_id);
```

#### 节点类型

| 类型 | 说明 | 图标 |
|------|------|------|
| root | 根节点（整个故事） | 📚 |
| act | 幕/卷 | 📖 |
| chapter | 章节 | 📄 |
| scene | 场景 | 🎬 |
| node | 普通节点（备注/想法） | 💡 |

#### API 接口

```
GET    /api/v1/outline/by-task/{task_id}              # 获取完整大纲树
POST   /api/v1/outline/nodes                          # 创建节点
PATCH  /api/v1/outline/nodes/{node_id}                # 更新节点
DELETE /api/v1/outline/nodes/{node_id}                # 删除节点
PATCH  /api/v1/outline/nodes/{node_id}/move           # 移动节点（改变父节点/顺序）
POST   /api/v1/outline/nodes/{node_id}/link-chapter   # 关联章节
POST   /api/v1/outline/from-template                  # 从模板生成大纲
```

#### 前端交互

1. **大纲树视图**
   - 左侧树形结构，支持无限层级
   - 拖拽调整节点顺序和层级
   - 折叠/展开节点
   - 右键菜单：添加子节点、删除、关联章节

2. **大纲编辑面板**
   - 右侧显示选中节点详情
   - 编辑标题、摘要、类型
   - 关联/取消关联章节
   - 添加备注

3. **大纲与章节联动**
   - 从大纲节点快速创建章节
   - 章节内容变更时同步更新大纲摘要
   - 大纲结构调整时同步更新章节顺序

4. **大纲导出**
   - 导出为 Markdown 树形结构
   - 导出为思维导图格式
   - 导出为 PDF 大纲文档

---

### 2.3 时间线编辑器

#### 概述
可视化故事内时间轴，标记事件节点，用于逻辑校验和结构规划。

#### 数据模型

```sql
-- 时间线事件表（新建）
CREATE TABLE timeline_events (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    chapter_id INTEGER REFERENCES chapters(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(20) DEFAULT 'scene',  -- 'scene' | 'plot' | 'background' | 'flashback'
    story_date VARCHAR(100),                  -- 故事内日期（如"第三天"、"2024年春"）
    story_date_order INTEGER,                 -- 用于排序的数值
    duration VARCHAR(100),                    -- 持续时长
    location VARCHAR(200),                    -- 地点
    characters TEXT,                          -- JSON数组，参与角色ID
    is_milestone BOOLEAN DEFAULT FALSE,       -- 是否为重要节点
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_timeline_events_task ON timeline_events(task_id, story_date_order);
CREATE INDEX idx_timeline_events_chapter ON timeline_events(chapter_id);
```

#### 事件类型

| 类型 | 颜色 | 说明 |
|------|------|------|
| scene | 蓝色 | 主线场景 |
| plot | 绿色 | 情节节点 |
| background | 灰色 | 背景事件 |
| flashback | 橙色 | 回忆/闪回 |

#### API 接口

```
GET    /api/v1/timeline/by-task/{task_id}              # 获取时间线
POST   /api/v1/timeline/events                         # 创建事件
PATCH  /api/v1/timeline/events/{event_id}              # 更新事件
DELETE /api/v1/timeline/events/{event_id}              # 删除事件
PATCH  /api/v1/timeline/events/{event_id}/move         # 移动事件位置
POST   /api/v1/timeline/from-chapters                  # 从章节自动生成时间线
```

#### 前端交互

1. **时间线视图**
   - 横向滚动的时间轴
   - 事件节点按时间顺序排列
   - 不同类型事件用不同颜色标记
   - 里程碑节点放大显示

2. **事件卡片**
   - 点击事件显示详情卡片
   - 显示：标题、描述、地点、参与角色、关联章节
   - 快速跳转到关联章节

3. **时间线编辑**
   - 拖拽调整事件顺序
   - 双击创建新事件
   - 缩放视图（按事件/按时间段/全部）

4. **逻辑检查**
   - 标记时间冲突（角色同时出现在两地）
   - 标记未回收的伏笔
   - 标记断裂的时间线

---

## 第三阶段：协作与深度

### 3.1 评论批注系统

#### 概述
对章节或段落添加评论，支持自我审阅和 AI 辅助评论。

#### 数据模型

```sql
-- 评论表（新建）
CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,  -- 回复
    author_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    comment_type VARCHAR(20) DEFAULT 'general',  -- 'general' | 'suggestion' | 'issue' | 'praise' | 'ai'
    status VARCHAR(20) DEFAULT 'open',            -- 'open' | 'resolved' | 'wontfix'
    selection_start INTEGER,                      -- 选中文本起始位置
    selection_end INTEGER,                        -- 选中文本结束位置
    selected_text TEXT,                           -- 选中的原文
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_comments_chapter ON comments(chapter_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
```

#### 评论类型

| 类型 | 图标 | 颜色 | 说明 |
|------|------|------|------|
| general | 💬 | 蓝色 | 通用评论 |
| suggestion | 💡 | 绿色 | 修改建议 |
| issue | ⚠️ | 红色 | 问题标记 |
| praise | 👍 | 黄色 | 好的表达 |
| ai | 🤖 | 紫色 | AI 评论 |

#### API 接口

```
GET    /api/v1/comments/by-chapter/{chapter_id}        # 获取章节评论
POST   /api/v1/comments/                               # 创建评论
PATCH  /api/v1/comments/{comment_id}                   # 更新评论
DELETE /api/v1/comments/{comment_id}                   # 删除评论
POST   /api/v1/comments/{comment_id}/resolve           # 标记为已解决
POST   /api/v1/comments/ai-review                      # AI 自动评论
```

#### AI 自动评论功能

```python
# AI 审阅提示词模板
AI_REVIEW_PROMPT = """
你是一位专业的文字编辑。请审阅以下章节内容，从以下角度提供评论：

1. 逻辑一致性：是否有前后矛盾的地方
2. 角色一致性：角色言行是否符合设定
3. 节奏把控：是否有拖沓或跳跃
4. 描写质量：是否有更好的表达方式
5. 错别字/语法：是否有明显错误

对于每个发现，请标注具体位置并给出修改建议。

章节内容：
{content}

角色设定：
{characters}
"""
```

#### 前端交互

1. **评论侧边栏**
   - 在编辑器右侧显示评论列表
   - 按位置排序（从上到下）
   - 支持筛选：按类型、按状态

2. **行内批注**
   - 选中文本后弹出"添加评论"按钮
   - 评论锚点在原文中高亮显示
   - 悬停显示评论预览

3. **AI 审阅**
   - 点击"AI 审阅"按钮，自动分析章节
   - AI 评论以特殊样式显示
   - 可一键接受 AI 建议

4. **评论统计**
   - 显示：总评论数、未解决数、按类型分布
   - 审阅进度追踪

---

### 3.2 世界观设定管理

#### 概述
结构化管理世界观设定，包括地图、势力、魔法体系、科技设定等。

#### 数据模型

```sql
-- 世界观分类表（新建）
CREATE TABLE worldbuilding_categories (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    name VARCHAR(50) NOT NULL,
    icon VARCHAR(10),
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 世界观条目表（新建）
CREATE TABLE worldbuilding_entries (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    category_id INTEGER NOT NULL REFERENCES worldbuilding_categories(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    attributes TEXT,                   -- JSON格式的自定义属性
    related_entries TEXT,              -- JSON数组，关联的其他条目ID
    related_characters TEXT,          -- JSON数组，关联的角色ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_worldbuilding_entries_task ON worldbuilding_entries(task_id);
CREATE INDEX idx_worldbuilding_entries_category ON worldbuilding_entries(category_id);
```

#### 预设分类模板

| 分类 | 图标 | 条目示例 |
|------|------|----------|
| 地理 | 🌍 | 大陆、城市、山脉、河流 |
| 势力 | 🏛️ | 国家、组织、家族 |
| 魔法体系 | ✨ | 法术分类、魔法规则、魔法物品 |
| 科技设定 | 🔬 | 科技水平、发明创造、交通工具 |
| 历史 | 📜 | 历史事件、朝代更替、重要战争 |
| 种族 | 👥 | 种族特征、文化习俗、语言 |
| 物品 | ⚔️ | 重要道具、神器、武器 |
| 规则 | 📏 | 世界运行规则、限制条件 |

#### API 接口

```
GET    /api/v1/worldbuilding/categories/by-task/{task_id}   # 获取分类
POST   /api/v1/worldbuilding/categories                     # 创建分类
PATCH  /api/v1/worldbuilding/categories/{cat_id}            # 更新分类
DELETE /api/v1/worldbuilding/categories/{cat_id}            # 删除分类

GET    /api/v1/worldbuilding/entries/by-task/{task_id}      # 获取所有条目
GET    /api/v1/worldbuilding/entries/by-category/{cat_id}   # 按分类获取
POST   /api/v1/worldbuilding/entries                        # 创建条目
PATCH  /api/v1/worldbuilding/entries/{entry_id}             # 更新条目
DELETE /api/v1/worldbuilding/entries/{entry_id}             # 删除条目
GET    /api/v1/worldbuilding/search                         # 搜索条目
```

#### 前端交互

1. **世界观浏览器**
   - 在侧边栏新增"世界观"Tab
   - 左侧分类树，右侧条目列表
   - 支持搜索和筛选

2. **条目编辑器**
   - 富文本编辑器，支持图片插入
   - 自定义属性面板
   - 关联条目选择器
   - 关联角色选择器

3. **世界观图谱**
   - 可视化条目之间的关联关系
   - 按分类着色
   - 支持筛选和搜索

4. **AI 辅助**
   - 根据已有设定生成新条目建议
   - 检查设定一致性
   - 生成设定文档摘要

---

### 3.3 冲突伏笔追踪

#### 概述
追踪故事中的冲突引入/解决和伏笔埋设/回收，确保剧情完整性。

#### 数据模型

```sql
-- 冲突表（新建）
CREATE TABLE conflicts (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    conflict_type VARCHAR(20) DEFAULT 'external',  -- 'external' | 'internal' | 'interpersonal'
    status VARCHAR(20) DEFAULT 'introduced',        -- 'introduced' | 'developing' | 'climax' | 'resolved'
    priority VARCHAR(10) DEFAULT 'medium',          -- 'high' | 'medium' | 'low'
    introduced_chapter_id INTEGER REFERENCES chapters(id),
    resolved_chapter_id INTEGER REFERENCES chapters(id),
    related_characters TEXT,                        -- JSON数组，相关角色ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 伏笔表（新建）
CREATE TABLE foreshadowing (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    foreshadowing_type VARCHAR(20) DEFAULT 'plot',  -- 'plot' | 'character' | 'world' | 'item'
    status VARCHAR(20) DEFAULT 'planted',            -- 'planted' | 'hinted' | 'revealed' | 'resolved'
    planted_chapter_id INTEGER REFERENCES chapters(id),
    revealed_chapter_id INTEGER REFERENCES chapters(id),
    hints TEXT,                                      -- JSON数组，包含{chapter_id, description}的提示列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_conflicts_task ON conflicts(task_id);
CREATE INDEX idx_conflicts_status ON conflicts(status);
CREATE INDEX idx_foreshadowing_task ON foreshadowing(task_id);
CREATE INDEX idx_foreshadowing_status ON foreshadowing(status);
```

#### 冲突类型与状态

**冲突类型：**
| 类型 | 说明 | 示例 |
|------|------|------|
| external | 外部冲突 | 主角vs反派、人vs自然 |
| internal | 内部冲突 | 内心挣扎、道德困境 |
| interpersonal | 人际关系冲突 | 朋友误会、家庭矛盾 |

**冲突状态流转：**
```
introduced → developing → climax → resolved
```

**伏笔状态流转：**
```
planted → hinted → revealed → resolved
```

#### API 接口

```
GET    /api/v1/conflicts/by-task/{task_id}              # 获取所有冲突
POST   /api/v1/conflicts/                               # 创建冲突
PATCH  /api/v1/conflicts/{conflict_id}                  # 更新冲突
DELETE /api/v1/conflicts/{conflict_id}                  # 删除冲突
GET    /api/v1/conflicts/unresolved                     # 获取未解决冲突

GET    /api/v1/foreshadowing/by-task/{task_id}          # 获取所有伏笔
POST   /api/v1/foreshadowing/                           # 创建伏笔
PATCH  /api/v1/foreshadowing/{fs_id}                    # 更新伏笔
DELETE /api/v1/foreshadowing/{fs_id}                    # 删除伏笔
GET    /api/v1/foreshadowing/unresolved                 # 获取未回收伏笔
```

#### 前端交互

1. **冲突追踪器**
   - 看板视图：按状态分列展示冲突卡片
   - 卡片显示：标题、类型、相关角色、关联章节
   - 拖拽改变状态

2. **伏笔追踪器**
   - 列表视图：显示所有伏笔
   - 状态筛选：未回收、已回收、全部
   - 高亮长期未回收的伏笔

3. **章节关联**
   - 在章节编辑区显示本章涉及的冲突和伏笔
   - 快速标记冲突进展/伏笔回收

4. **完整性检查**
   - 检测未解决的冲突
   - 检测长期未回收的伏笔
   - 检测逻辑漏洞

---

### 3.4 审阅模式

#### 概述
沉浸式阅读视图，支持标注和修改建议，用于后期修订。

#### 功能设计

1. **沉浸式阅读**
   - 隐藏编辑器，全屏显示章节内容
   - 优化排版：字体、行距、段距
   - 护眼模式/暗色模式
   - 自动滚动（可调速）

2. **阅读统计**
   - 预计阅读时间
   - 当前阅读进度
   - 阅读速度

3. **标注工具**
   - 高亮（多颜色）
   - 下划线
   - 删除线
   - 波浪线（标记错误）
   - 边注（在侧边添加备注）

4. **修改建议**
   - 选中文本后显示"建议修改"按钮
   - 输入修改建议
   - 显示原文 vs 建议对比
   - 一键接受/拒绝建议

5. **审阅报告**
   - 生成审阅摘要
   - 统计：高亮数、批注数、修改建议数
   - 导出审阅报告

#### 数据模型

```sql
-- 审阅标注表（新建）
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    annotation_type VARCHAR(20) NOT NULL,  -- 'highlight' | 'underline' | 'strikethrough' | 'wavy' | 'margin_note'
    color VARCHAR(7),
    selection_start INTEGER NOT NULL,
    selection_end INTEGER NOT NULL,
    selected_text TEXT,
    note TEXT,                               -- 边注内容
    suggestion TEXT,                         -- 修改建议
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_annotations_chapter ON annotations(chapter_id);
CREATE INDEX idx_annotations_user ON annotations(user_id);
```

#### API 接口

```
GET    /api/v1/annotations/by-chapter/{chapter_id}      # 获取章节标注
POST   /api/v1/annotations/                             # 创建标注
PATCH  /api/v1/annotations/{annotation_id}              # 更新标注
DELETE /api/v1/annotations/{annotation_id}              # 删除标注
POST   /api/v1/annotations/{annotation_id}/accept       # 接受修改建议
POST   /api/v1/annotations/{annotation_id}/reject       # 拒绝修改建议
GET    /api/v1/reviews/by-chapter/{chapter_id}          # 获取审阅报告
```

#### 前端交互

1. **进入审阅模式**
   - 在章节编辑器工具栏添加"审阅模式"按钮
   - 全屏切换，优化阅读体验

2. **标注交互**
   - 选中文本弹出工具栏
   - 选择标注类型和颜色
   - 输入边注或修改建议

3. **标注列表**
   - 侧边栏显示所有标注
   - 点击标注跳转到位置
   - 按类型筛选

4. **对比视图**
   - 显示原文和修改建议的并排对比
   - 差异高亮
   - 逐条接受/拒绝

---

## 附录

### A. 数据库迁移策略

每个阶段的功能涉及新增表和字段，建议使用 Alembic 进行数据库迁移管理：

```bash
# 安装 Alembic
pip install alembic

# 初始化迁移环境
alembic init migrations

# 生成迁移脚本
alembic revision --autogenerate -m "add双向链接和标签系统"

# 执行迁移
alembic upgrade head
```

### B. 前端组件库建议

| 功能 | 推荐库 |
|------|--------|
| 知识图谱 | Cytoscape.js / React Flow |
| 时间线 | vis-timeline / react-calendar-timeline |
| 日历视图 | react-big-calendar |
| 看板视图 | react-beautiful-dnd / @dnd-kit |
| 大纲树 | react-arborist / react-sortable-tree |
| 图表统计 | recharts / visx |

### C. 开发优先级建议

```
第一阶段（4-6周）
├── 1.1 双向链接系统 (1.5周)
├── 1.2 标签系统 (1周)
├── 1.3 多视图切换 (1.5周)
├── 1.4 写作目标与字数统计 (1周)
└── 1.5 章节自定义属性 (1周)

第二阶段（4-5周）
├── 2.1 知识图谱增强 (2周)
├── 2.2 大纲编辑器 (1.5周)
└── 2.3 时间线编辑器 (1.5周)

第三阶段（5-6周）
├── 3.1 评论批注系统 (1.5周)
├── 3.2 世界观设定管理 (1.5周)
├── 3.3 冲突伏笔追踪 (1周)
└── 3.4 审阅模式 (1.5周)
```

---

## 审阅清单

请审阅以下内容：

- [ ] 功能设计是否符合需求
- [ ] 数据模型设计是否合理
- [ ] API 接口设计是否完整
- [ ] 前端交互设计是否清晰
- [ ] 开发优先级是否合理
- [ ] 是否有遗漏的功能点

审阅意见：
_________________________________
_________________________________
_________________________________
