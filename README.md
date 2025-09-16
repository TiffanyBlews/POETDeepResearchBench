# POET Bench


## 项目概述

POET Bench 是一个专为评估深度研究智能体（Deep Research Agents, DRAs）设计的综合基准测试系统。本系统基于POET评估框架（Performance, Operability, Efficiency, Trustworthiness），通过三大核心维度评估AI智能体的真实商业价值和投资回报率（ROI）。

### POET框架核心理念

POET基准设计理念是"始于终局"——首先回答一个根本问题：一个值得企业信赖并为其付费的AI智能体，需要满足决策者哪些最核心的关切？

#### 四大核心关切
1. **效果为王** (Effectiveness over Novelty)：一切围绕真实业务场景，准确性、深度和可用性是唯一的价值尺度
2. **信任与验证** (Trust through Transparency)：提供来源、列出依据，可验证性是商业化的基石
3. **价值提升** (Value Creation over Efficiency)：直接作用于企业的利润表和风险控制
4. **可靠性与稳定性** (Reliability as a Utility)：像电力系统一样稳定、可靠

## Query筛选系统

### 7维度查询价值评估模型

POET使用严格的7维度评估模型筛选高价值评测查询，确保每个测试任务都与企业真实痛点直接挂钩：

| 维度 | 权重 | 评分范围 |
|------|------|----------|
| 决策颠覆性 | 5% | 1分(参考级) - 5分(决定性) |
| 分析复杂性 | 20% | 1分(简单检索) - 5分(多维建模) |
| 行动导向性 | 20% | 1分(描述性) - 5分(可执行) |
| 风险/收益规模 | 15% | 1分(微不足道) - 5分(战略级) |
| 时效敏感性 | 10% | 1分(静态知识) - 5分(实时情报) |
| 专业壁垒 | 5% | 1分(通用知识) - 5分(尖端领域) |
| 可验证性 | 25% | 1分(难以验证) - 5分(极易验证) |

**总分公式**: Query价值分 = Σ(维度得分 × 维度权重)

只有Query价值分≥4.5分的任务才被纳入评估集。




## 评估框架：POET三大价值维度

### 1. 效率价值 (Efficiency Value) - 30%
量化智能体最直接的经济贡献，回答"快不快，省不省"的问题：
- **时间效率**：对比智能体与领域专家的耗时，量化"解放"出的专家时间
- **成本效率**：精确计算智能体带来的净成本节约
- **自动化率**：衡量无需人工干预的自动化节点比例
- **资源消耗**：完成任务使用的token数量和计算资源

### 2. 质量价值 (Quality Value) - 50%
构建人机协作的信任基石，包含两大评估维度：

#### RACE评估 (Reference-based Adaptive Criteria-driven Evaluation)
成果的宏观品质评估，包含四个维度：
- **全面性** (Comprehensiveness)：信息覆盖的广度、深度和相关性
- **洞察力** (Insight)：分析的深度、独到性、逻辑性和结论价值
- **指令遵循能力** (Instruction Following)：报告是否准确、完整地回应了任务的所有要求
- **可读性** (Readability)：结构清晰度、语言流畅度、数据呈现效果

#### FACT评估 (Framework for Factual Abundance and Citation Trustworthiness)
事实的微观溯源校验，重点关注：
- **有效引用数** (Effective Citations)：平均每篇报告包含多少条有事实依据支撑的引用
- **引用准确率** (Citation Accuracy)：所有引用中，有多少比例是准确无误的

### 3. 战略价值 (Strategic Value) - 20%
驱动组织进化的知识飞轮，评估智能体超越单次任务的长期赋能：
- **复杂任务处理能力**：能否独立处理人类专家需半小时以上才能完成的深度研究
- **知识沉淀与复用**：能否将任务产出沉淀到知识库，并在后续任务中智能复用

## 基准数据集构建

### 任务选择标准
系统采用7个维度的Query价值评估模型筛选高价值测试任务：

| 维度 | 权重 | 评分范围 |
|------|------|----------|
| 决策颠覆性 | 5% | 1分(参考级) - 5分(决定性) |
| 分析复杂性 | 20% | 1分(简单检索) - 5分(多维建模) |
| 行动导向性 | 20% | 1分(描述性) - 5分(可执行) |
| 风险/收益规模 | 15% | 1分(微不足道) - 5分(战略级) |
| 时效敏感性 | 10% | 1分(静态知识) - 5分(实时情报) |
| 专业壁垒 | 5% | 1分(通用知识) - 5分(尖端领域) |
| 可验证性 | 25% | 1分(难以验证) - 5分(极易验证) |

只有Query价值分≥4.5分的任务才被纳入评估集，确保每个测试任务都与企业真实痛点和需求直接挂钩。

### 数据集规模
基准测试包含**100个PhD级别研究任务**，由各领域专家精心设计，覆盖**22个不同领域**：

* 🔬 **科学与技术**: 物理、化学、生物、环境科学和工程学
* 💼 **金融与商业**: 投资、个人理财、市场营销和人力资源
* 💻 **软件技术**: 软件使用和互联网相关主题
* 🌍 **其他领域**: 艺术设计、娱乐、历史、工业、交通、旅游等


## 数据格式规范

### 输入数据格式

基础的输入数据格式在原有的基础上增加客观指标字段：

```json
{
    "id": "任务ID",
    "prompt": "用户输入的研究查询",
    "article": "AI智能体生成的研究报告",
    "execution_metrics": {
        "total_duration_seconds": 1200,
        "token_usage": {
            "input_tokens": 2500,
            "output_tokens": 12000,
            "total_cost_usd": 0.087
        },
        "automation_level": 0.95,
        "tool_calls_count": 8,
        "sources_used": 15,
        "citation_count": 22,
        "word_count": 8500
    }
}
```

#### 客观指标字段说明

**execution_metrics** 包含以下不需要人工标注和LLM评估的客观指标：

- `total_duration_seconds`: 任务实际执行总时间（秒）
- `token_usage`: Token使用情况
  - `input_tokens`: 输入token总数
  - `output_tokens`: 输出token总数
  - `total_cost_usd`: 实际产生的费用（美元）
- `automation_level`: 自动化程度（0-1，1表示完全自动化）
- `tool_calls_count`: 工具调用总次数
- `sources_used`: 使用的信息源数量
- `citation_count`: 引用数量
- `word_count`: 输出文档字数

### 人工标注数据要求

系统需要以下人工标注数据文件，位于 `data/annotation/` 目录：

#### 1. 领域专家数据 (`domain_expert_data.json`)
```json
{
    "finance": {
        "avg_hourly_rate_usd": 200,
        "avg_task_time_hours": 2.5
    },
    "technology": {
        "avg_hourly_rate_usd": 180,
        "avg_task_time_hours": 3.0
    },
    "healthcare": {
        "avg_hourly_rate_usd": 250,
        "avg_task_time_hours": 2.8
    }
}
```

#### 2. 任务复杂度数据 (`complexity_level_data.json`)
```json
{
    "1": {
        "description": "简单信息检索",
        "expert_time_multiplier": 0.5,
        "difficulty_score": 1
    },
    "2": {
        "description": "基础分析任务",
        "expert_time_multiplier": 0.7,
        "difficulty_score": 2
    },
    "3": {
        "description": "中等复杂度研究",
        "expert_time_multiplier": 1.0,
        "difficulty_score": 3
    },
    "4": {
        "description": "深度分析研究",
        "expert_time_multiplier": 1.5,
        "difficulty_score": 4
    },
    "5": {
        "description": "专家级复杂研究",
        "expert_time_multiplier": 2.0,
        "difficulty_score": 5
    }
}
```

#### 3. Token定价数据 (`token_pricing_data.json`)
```json
{
    "claude-3-sonnet": {
        "input_price_per_1k": 0.003,
        "output_price_per_1k": 0.015
    },
    "gpt-4": {
        "input_price_per_1k": 0.01,
        "output_price_per_1k": 0.03
    },
    "gemini-pro": {
        "input_price_per_1k": 0.00125,
        "output_price_per_1k": 0.00375
    }
}
```


## 快速开始

### 环境配置

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置API密钥
export OPENAI_API_KEY="your_openai_api_key"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_MODEL="google/gemini-2.5-pro"
export JINA_API_KEY="your_jina_api_key"
```

### 数据准备

将您的测试数据放置在以下目录结构中：

```
data/
├── test_data/raw_data/
│   └── your_model.jsonl          # 模型输出数据（包含execution_metrics）
├── prompt_data/
│   └── query.jsonl                # 100个研究任务查询
├── annotation/                    # 人工标注数据（必需）
│   ├── domain_expert_data.json
│   ├── complexity_level_data.json
│   └── token_pricing_data.json
└── reference/
    └── reference.jsonl            # 参考答案（用于RACE评估）
```

### 查询筛选和数据准备

#### 第一步：筛选高价值查询（首次运行）

```bash
# 基于POET 7维度模型筛选高价值查询
python query_selector.py \
    --input_file query_analysis/raw_query.md \
    --output_dir query_analysis/ \
    --threshold 4.0 \
    --export_selected \
    --max_workers 8

# 查看筛选结果
ls query_analysis/
# 输出文件:
# - query_scores.json        # 完整评分结果
# - query_scores.csv         # CSV格式结果
# - selected_queries.jsonl   # 筛选的高价值查询
```

### 运行完整评估

#### 方法一：完整POET评估（最新推荐）

```bash
# 使用配置驱动的完整POET评估系统
python poet_benchmark.py --config config/poet_algorithm_config.json

# 或指定具体模型
python poet_benchmark.py "model_name" \
    --config config/poet_algorithm_config.json \
    --input_file data/test_data/raw_data/model_name.jsonl \
    --output_dir results/poet/model_name
```

#### 方法二：一键式POET评估（推荐）

```bash
# 修改 run_benchmark.sh 中的模型名称
TARGET_MODELS=("your-model-name")

# 一键式运行：自动查询筛选 + 动态标准生成 + RACE+FACT评估
ENABLE_QUERY_SELECTION=true bash run_benchmark.sh

# 传统评估（不使用POET筛选）
bash run_benchmark.sh
```

**智能缓存机制：**
- ✅ **Query评分缓存**: 只在原始查询文件变化时重新评分，避免重复的昂贵LLM调用
- ✅ **Criteria生成缓存**: 只在筛选结果变化时重新生成动态标准
- ✅ **快速阈值调整**: 基于缓存评分文件快速尝试不同筛选阈值
- ✅ **工具整合**: `query_selector.py` 集成了筛选和格式转换功能

**工作流程优化：**
```bash
# 第一次运行：完整流程
raw_query.md → 7维度评分 → 筛选 → criteria生成 → 评估

# 后续运行：智能复用
cached_scores → 新阈值筛选 → cached_criteria → 评估
```

#### 方法三：手动分步运行

**步骤1：Query筛选和评分（智能缓存）**
```bash
# 完整评分（第一次或原始查询变化时）
python query_selector.py \
    --input_file query_analysis/raw_query.md \
    --output_dir query_analysis/ \
    --threshold 4.0 \
    --convert_to_jsonl data/prompt_data/query.jsonl

# 快速筛选（使用缓存评分，调整阈值）
python query_selector.py \
    --from_scores query_analysis/query_scores.json \
    --threshold 4.5 \
    --convert_to_jsonl data/prompt_data/query.jsonl
```

**步骤2：动态评估标准生成（智能缓存）**
```bash
# 自动检测是否需要重新生成criteria
python query_rubrics_generator.py
```

**步骤3：模型输出评估**
```bash
# RACE评估（使用筛选后的查询和动态标准）
python deepresearch_bench_race.py "model_name" \
    --raw_data_dir data/test_data/raw_data \
    --query_file data/prompt_data/query.jsonl \
    --output_dir results/race/model_name \
    --max_workers 10

**步骤4：FACT评估流水线**
```bash
python -m utils.extract \
    --raw_data_path data/test_data/raw_data/model_name.jsonl \
    --output_path results/fact/model_name/extracted.jsonl \
    --query_data_path data/prompt_data/query.jsonl \
    --n_total_process 10

python -m utils.deduplicate \
    --raw_data_path results/fact/model_name/extracted.jsonl \
    --output_path results/fact/model_name/deduplicated.jsonl \
    --query_data_path data/prompt_data/query.jsonl \
    --n_total_process 10

python -m utils.scrape \
    --raw_data_path results/fact/model_name/deduplicated.jsonl \
    --output_path results/fact/model_name/scraped.jsonl \
    --n_total_process 10

python -m utils.validate \
    --raw_data_path results/fact/model_name/scraped.jsonl \
    --output_path results/fact/model_name/validated.jsonl \
    --query_data_path data/prompt_data/query.jsonl \
    --n_total_process 10

python -m utils.stat \
    --input_path results/fact/model_name/validated.jsonl \
    --output_path results/fact/model_name/fact_result.txt

# 5. 三维价值评估
python -m utils.efficiency_evaluator_clean \
    --input_file data/test_data/raw_data/model_name.jsonl \
    --output_dir results/efficiency/model_name

python -m utils.strategic_evaluator \
    --input_file data/test_data/raw_data/model_name.jsonl \
    --output_dir results/strategic/model_name

python -m utils.web_interaction_evaluator \
    --input_file data/test_data/raw_data/model_name.jsonl \
    --output_dir results/web_interaction/model_name

# 6. POET综合评估
python poet_benchmark.py "model_name" \
    --config config/poet_algorithm_config.json \
    --input_file data/test_data/raw_data/model_name.jsonl \
    --output_dir results/poet/model_name
```

### 查看评估结果

评估完成后，结果将保存在以下位置：

```
results/
├── race/model_name/
│   └── race_result.txt              # RACE 4维度质量评估结果
├── fact/model_name/
│   ├── extracted.jsonl              # 提取的事实陈述和引用
│   ├── deduplicated.jsonl           # 去重后的引用
│   ├── scraped.jsonl                # 网页内容抓取结果
│   ├── validated.jsonl              # 引用验证结果
│   └── fact_result.txt              # FACT最终统计结果
├── efficiency/model_name/
│   └── efficiency_report.json       # 效率价值评估结果
├── strategic/model_name/
│   └── strategic_report.json        # 战略价值评估结果
├── web_interaction/model_name/
│   └── web_interaction_report.json  # Web交互能力评估结果
└── poet/model_name/
    ├── model_name_poet_detailed.json    # POET详细结果
    ├── model_name_poet_summary.json     # POET关键指标汇总
    └── model_name_poet_report.txt       # 综合分析报告
```

## 核心评估指标解读

### 效率价值指标
- **时间节约率** = (专家预期时间 - 实际执行时间) / 专家预期时间
- **成本节约额** = 专家成本 - AI成本
- **自动化程度** = execution_metrics.automation_level
- **资源效率** = 输出质量 / Token消耗

### 质量价值指标
- **RACE综合分** = 全面性×权重 + 洞察力×权重 + 指令遵循×权重 + 可读性×权重
- **引用准确率** = 准确引用数 / 总引用数
- **引用丰富度** = 有效引用数 / 报告长度

### 战略价值指标
- **任务复杂度适应性** = 基于任务复杂度和完成质量的综合评估
- **知识创造价值** = 新知识单元数量和质量评估

### POET综合分计算
```
POET综合分 = 效率价值 × 30% + 质量价值 × 50% + 战略价值 × 20%
```

## 系统架构

### 核心模块

#### 查询管理系统
- `query_selector.py`: POET 7维度查询价值评估和筛选
- `convert_md_to_jsonl.py`: Markdown查询转JSONL格式转换器
- `query_rubrics_generator.py`: 查询特定的Rubric生成器

#### 评估引擎
- `poet_benchmark.py`: POET完整评估系统（推荐使用）
- `deepresearch_bench_race.py`: RACE 4维度质量评估主程序
- `utils/efficiency_evaluator_clean.py`: 效率价值评估器
- `utils/strategic_evaluator.py`: 战略价值评估器
- `utils/web_interaction_evaluator.py`: Web交互能力评估器

#### FACT事实验证流水线
- `utils/extract.py`: 从报告中提取事实陈述和引用
- `utils/deduplicate.py`: 去除重复的事实-URL对
- `utils/scrape.py`: 基于Jina API的网页内容抓取
- `utils/validate.py`: LLM驱动的引用验证
- `utils/stat.py`: FACT评估统计分析

#### 自动化流程
- `run_benchmark.sh`: 传统RACE+FACT评估流水线
- `config/poet_algorithm_config.json`: 配置驱动的参数管理

### POET数据流程
1. **查询价值评估**: 7维度商业价值评估和高价值查询筛选
2. **动态标准生成**: 基于查询特性自动生成评估Rubric和权重
3. **质量价值评估**: RACE 4维度质量评估 + FACT引用可信度验证
4. **效率价值评估**: 时间成本分析和资源消耗统计
5. **战略价值评估**: 复杂任务处理能力和知识沉淀评估
6. **综合价值计算**: 三大价值维度加权计算POET综合分
7. **报告生成**: 生成详细的商业价值分析报告

## 配置选项

### 评估参数调整
在 `run_benchmark.sh` 中可调整：
- `N_TOTAL_PROCESS=10`: 并行处理进程数
- `LIMIT="--limit 2"`: 限制评估任务数量（测试用）
- `SKIP_CLEANING="--skip_cleaning"`: 跳过文章预处理
- `ONLY_ZH="--only_zh"`: 仅评估中文任务
- `ONLY_EN="--only_en"`: 仅评估英文任务

### POET配置管理
在 `config/poet_algorithm_config.json` 中可自定义参数：
```json
{
    "poet_weights": {
        "efficiency_value": 0.30,
        "quality_value": 0.50,
        "strategic_value": 0.20
    },
    "race_weights": {
        "comprehensiveness": 0.25,
        "insight": 0.35,
        "instruction_following": 0.25,
        "readability": 0.15
    },
    "query_selection": {
        "threshold": 4.0,
        "enable_dynamic_weighting": true
    },
    "evaluation_settings": {
        "max_workers": 10,
        "enable_parallel_processing": true,
        "language_support": ["zh", "en"]
    }
}
```

## 最佳实践

### 数据收集建议
1. **准确记录执行时间**: 从任务开始到完成的准确时间戳
2. **精确统计Token用量**: 使用API返回的实际Token数量
3. **客观评估自动化程度**: 基于实际人工干预次数计算
4. **完整记录工具调用**: 包括失败的调用次数
5. **准确计算实际成本**: 基于实际API费用而非估算

### 标注数据维护
1. **定期更新专家费率**: 基于市场调研保持数据时效性
2. **校准复杂度分级**: 基于实际任务表现调整复杂度定义
3. **同步Token定价**: 及时更新各模型的最新定价信息

### 评估质量保证
1. **数据格式验证**: 运行前检查所有必需字段完整性
2. **结果交叉验证**: 对异常高分或低分结果进行人工复查
3. **基准对比**: 与人类专家表现进行定期基准对比
4. **持续改进**: 基于评估结果反馈优化评估标准

## 故障排除

### 常见问题

1. **缺少execution_metrics字段**
   ```bash
   # 检查数据格式
   python -c "
   import json
   with open('data/test_data/raw_data/model.jsonl') as f:
       for line in f:
           data = json.loads(line)
           print('execution_metrics' in data)
           break
   "
   ```

2. **API密钥未设置**
   ```bash
   echo $OPENAI_API_KEY
   echo $OPENAI_BASE_URL
   echo $OPENAI_MODEL
   echo $JINA_API_KEY
   ```

3. **标注数据缺失**
   ```bash
   ls data/annotation/
   # 应该看到: domain_expert_data.json, complexity_level_data.json, token_pricing_data.json
   ```
