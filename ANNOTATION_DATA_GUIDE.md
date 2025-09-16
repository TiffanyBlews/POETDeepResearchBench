# 标注数据外部化指南

本指南说明如何使用外部标注数据文件来配置POET基准测试系统，替代代码中的硬编码数据。

## 文件结构

```
data/annotation/
├── domain_expert_data.json      # 领域专家时间和时薪数据
├── task_type_data.json          # 任务类型专家时间数据
├── expert_type_data.json        # 专家类型和时薪数据
├── token_pricing_data.json      # AI模型token定价数据
└── complexity_level_data.json   # 任务复杂度级别数据

config/
└── poet_algorithm_config.json   # 算法参数配置（非标注数据）
```

## 标注数据文件说明

### 1. 领域专家数据 (domain_expert_data.json)

包含不同领域的专家完成任务所需时间和时薪：

```json
{
  "domains": {
    "finance": {
      "expert_time_hours": 3.0,
      "expert_hourly_rate_usd": 150.0,
      "description": "金融分析、投资研究、财务建模等任务"
    }
  }
}
```

**可配置字段：**
- `expert_time_hours`: 专家完成该领域任务的平均时间（小时）
- `expert_hourly_rate_usd`: 该领域专家的平均时薪（美元）
- `description`: 领域描述
- `complexity_factors`: 影响该领域复杂度的因素列表

**支持的领域：**
- `finance` - 金融
- `legal` - 法律
- `medical` - 医学
- `technology` - 技术
- `marketing` - 市场营销
- `consulting` - 咨询
- `research` - 研究
- `engineering` - 工程
- `general` - 通用（默认）

### 2. 任务类型数据 (task_type_data.json)

包含不同任务类型的专家完成时间：

```json
{
  "task_types": {
    "analysis_task": {
      "expert_time_hours": 2.0,
      "description": "数据分析任务，需要整理、分析、解释数据",
      "complexity_level": 2
    }
  }
}
```

**可配置字段：**
- `expert_time_hours`: 专家完成该类型任务的平均时间（小时）
- `description`: 任务类型描述
- `typical_examples`: 典型任务示例列表
- `complexity_level`: 对应的复杂度级别（1-5）

**支持的任务类型：**
- `simple_query` - 简单查询
- `analysis_task` - 分析任务
- `research_task` - 研究任务
- `complex_research` - 复杂研究
- `market_analysis` - 市场分析
- `competitor_research` - 竞品研究
- `financial_analysis` - 财务分析
- `legal_research` - 法律研究
- `technical_analysis` - 技术分析

### 3. 专家类型数据 (expert_type_data.json)

包含不同级别专家的时薪数据：

```json
{
  "expert_types": {
    "senior_analyst": {
      "hourly_rate_usd": 100.0,
      "description": "高级分析师，3-7年经验",
      "experience_years": "3-7"
    }
  }
}
```

**可配置字段：**
- `hourly_rate_usd`: 专家时薪（美元）
- `description`: 专家类型描述
- `capabilities`: 专家能力列表
- `experience_years`: 经验年限

**支持的专家类型：**
- `junior_analyst` - 初级分析师
- `senior_analyst` - 高级分析师
- `domain_expert` - 领域专家
- `consultant` - 咨询顾问
- `specialist` - 专业顾问

### 4. Token定价数据 (token_pricing_data.json)

包含不同AI模型的token定价：

```json
{
  "pricing_models": {
    "gpt-3.5-turbo": {
      "input_cost_per_1k": 0.0015,
      "output_cost_per_1k": 0.006,
      "description": "GPT-3.5 Turbo模型定价",
      "provider": "OpenAI"
    }
  }
}
```

**可配置字段：**
- `input_cost_per_1k`: 每1000个输入token的成本（美元）
- `output_cost_per_1k`: 每1000个输出token的成本（美元）
- `description`: 模型描述
- `provider`: 模型提供商

**支持的模型：**
- `gpt-4`, `gpt-4o`, `gpt-3.5-turbo`
- `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- `gemini-pro`
- `default` - 默认定价

### 5. 复杂度级别数据 (complexity_level_data.json)

包含任务复杂度级别定义：

```json
{
  "complexity_levels": {
    "3": {
      "name": "complex",
      "description": "复杂任务，需要深度分析和综合",
      "typical_time_range": "3-6小时"
    }
  },
  "complexity_mapping": {
    "simple": 1,
    "moderate": 2,
    "complex": 3,
    "advanced": 4,
    "expert": 5
  }
}
```

**复杂度级别：**
- Level 1 (`simple`) - 简单任务
- Level 2 (`moderate`) - 中等任务
- Level 3 (`complex`) - 复杂任务
- Level 4 (`advanced`) - 高级任务
- Level 5 (`expert`) - 专家级任务
