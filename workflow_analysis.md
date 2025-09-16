# POET Bench 完整工作流程分析

## 当前实现状态

### ✅ 已实现的核心组件

#### 1. 查询筛选与评分系统
- **query_selector.py**: POET 7维度查询评分和筛选
- **convert_md_to_jsonl.py**: 将markdown查询转换为JSONL格式
- **状态**: ✅ 完全实现并集成

#### 2. Rubric生成系统
- **query_rubrics_generator.py**: 查询特定的rubric生成器
- **数据文件**: data/criteria_data/criteria.jsonl
- **状态**: ✅ 完全实现，支持动态权重生成

#### 3. 模型输出评估系统
- **deepresearch_bench_race.py**: RACE评估主程序（4维度评估）
- **poet_benchmark.py**: 完整POET评估系统
- **FACT评估组件**: extract, deduplicate, scrape, validate, stat
- **状态**: ✅ 完全实现

#### 4. 主工作流程
- **run_benchmark.sh**: 自动化评估流水线
- **状态**: ✅ 已集成查询筛选和动态配置

#### 5. 新增评估器系统
- **utils/efficiency_evaluator_clean.py**: 效率价值评估
- **utils/strategic_evaluator.py**: 战略价值评估
- **utils/web_interaction_evaluator.py**: Web交互能力评估
- **状态**: ✅ 全新实现，对齐POET价值框架

## 🔄 完整工作流程

```
原始数据 → 查询筛选 → Rubric生成 → 模型输出评估 → 多维价值评估 → 综合分析
    ↓           ↓            ↓             ↓             ↓           ↓
query.md → query.jsonl → criteria.jsonl → RACE+FACT → Efficiency → Strategic
                                                    ↓             ↓
                                                    Quality     Value
```

### 详细流程步骤

1. **原始查询准备**
   ```bash
   # 输入: query_analysis/raw_query.md (markdown格式的原始查询)
   # 支持中英文混合查询，自动识别语言
   ```

2. **POET查询筛选和评分**
   ```bash
   # 7维度查询价值评估（决策颠覆性、分析复杂性、行动导向性等）
   python query_selector.py \
     --input_file query_analysis/raw_query.md \
     --output_dir query_analysis/ \
     --threshold 4.0 \
     --export_selected

   # 输出: query_analysis/query_scores.json
   ```

3. **标准格式转换**
   ```bash
   # 转换为benchmark标准格式
   python convert_md_to_jsonl.py \
     --input_file query_analysis/raw_query.md \
     --output_file data/prompt_data/query.jsonl

   # 输出: data/prompt_data/query.jsonl
   ```

4. **动态Rubric生成**
   ```bash
   # 基于query特性生成自适应评估标准和权重
   python query_rubrics_generator.py

   # 输出: data/criteria_data/criteria.jsonl (包含动态权重)
   ```

5. **核心评估系统**
   ```bash
   # 方式1: 完整POET评估（推荐）
   python poet_benchmark.py --config config/poet_algorithm_config.json

   # 方式2: 传统RACE+FACT评估
   bash run_benchmark.sh

   # 方式3: 带查询筛选的RACE评估
   python deepresearch_bench_race.py "model_name" \
     --enable_query_selection \
     --query_selection_threshold 4.0

   # 输入:
   # - data/test_data/raw_data/model_name.jsonl (模型输出)
   # - data/prompt_data/query.jsonl (查询)
   # - data/criteria_data/criteria.jsonl (动态评估标准)
   ```

6. **FACT评估（引用验证）**
   ```bash
   # 事实丰富度和引用可信度评估
   python -m utils.extract --raw_data_path data/test_data/raw_data/model.jsonl ...
   python -m utils.deduplicate ...
   python -m utils.scrape ...
   python -m utils.validate ...
   python -m utils.stat ...

   # 输出: results/fact/model_name/ (有效引用数、引用准确率)
   ```

7. **三维价值评估**
   ```bash
   # 效率价值评估 (Time-to-Completion, Token用量, 成本节约)
   python -m utils.efficiency_evaluator_clean

   # 战略价值评估 (复杂任务处理、知识沉淀能力)
   python -m utils.strategic_evaluator

   # Web交互能力评估
   python -m utils.web_interaction_evaluator
   ```

## 🎯 关键集成点

### 1. POET查询筛选集成
- **位置**: deepresearch_bench_race.py, poet_benchmark.py
- **触发**: --enable_query_selection 参数
- **功能**: 7维度查询价值评估和高价值查询自动筛选

### 2. 动态Rubric系统
- **位置**: query_rubrics_generator.py
- **功能**: 基于查询特性自动生成评估标准和权重
- **特性**: 每个查询都有专门的4维度动态权重

### 3. 多模式评估引擎
- **RACE评估**: deepresearch_bench_race.py (4维度质量评估)
- **FACT评估**: utils/extract.py → validate.py (引用可信度)
- **效率评估**: utils/efficiency_evaluator_clean.py
- **战略评估**: utils/strategic_evaluator.py

### 4. 配置驱动架构
- **位置**: config/poet_algorithm_config.json
- **功能**: 统一配置各评估器参数和权重
- **支持**: 多语言、多模型、多任务类型

## 🆕 新增核心功能

### 1. POET价值框架对齐
- **三维价值评估**: 效率价值 + 质量价值 + 战略价值
- **商业ROI计算**: 时间节约、成本节约、风险降低
- **专业对齐评估**: Tech-Market-Fit量化

### 2. 智能化查询管理
- **价值评分系统**: 7维度商业价值量化
- **动态筛选**: 可配置阈值的高价值查询筛选
- **多语言支持**: 中英文混合查询处理

### 3. 自适应评估体系
- **动态权重**: 基于查询特性的自适应权重分配
- **多层次评估**: 宏观质量 + 微观事实 + 效率战略
- **可扩展架构**: 支持新评估器插件式集成

## 🚀 一键式完整流程

### 当前推荐命令

**一键式完整评估（推荐）:**
```bash
# 启用POET查询筛选 + 动态标准生成 + RACE+FACT评估
ENABLE_QUERY_SELECTION=true bash run_benchmark.sh
```

**手动分步执行:**
```bash
# 步骤1: 查询筛选（带缓存）
python query_selector.py \
  --input_file query_analysis/raw_query.md \
  --threshold 4.0 \
  --convert_to_jsonl data/prompt_data/query.jsonl

# 步骤2: 动态标准生成（带缓存）
python query_rubrics_generator.py

# 步骤3: 模型评估
python deepresearch_bench_race.py "model_name" \
  --query_file data/prompt_data/query.jsonl \
  --output_dir results/race/model_name
```

**仅使用缓存快速筛选:**
```bash
# 从已有评分文件快速筛选不同阈值
python query_selector.py \
  --from_scores query_analysis/query_scores.json \
  --threshold 4.5 \
  --convert_to_jsonl data/prompt_data/query.jsonl
```

### 优化的缓存机制
```bash
# 完整流程（第一次运行）
raw_query.md → query_selector.py → query_scores.json + query.jsonl
                     ↓
              query_rubrics_generator.py → criteria.jsonl
                     ↓
              deepresearch_bench_race.py → results/

# 后续运行（使用缓存）
query_scores.json → query_selector.py --from_scores → query.jsonl（新阈值）
                           ↓
                    直接使用缓存的criteria.jsonl → results/
```

## 📋 使用前检查清单

### 环境配置
1. ✅ **API密钥配置**
   - OPENAI_API_KEY (LLM评估)
   - OPENAI_BASE_URL (OpenAI兼容API)
   - OPENAI_MODEL (推荐: google/gemini-2.5-pro)
   - JINA_API_KEY (Web爬取)

2. ✅ **Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

### 数据准备
3. ✅ **输入数据检查**
   - query_analysis/raw_query.md (原始查询markdown)
   - data/test_data/raw_data/model_name.jsonl (模型输出)
   - config/poet_algorithm_config.json (POET配置)

4. ✅ **输出目录权限**
   - results/ (评估结果)
   - query_analysis/ (查询分析)
   - data/criteria_data/ (动态标准)

### 数据一致性
5. ✅ **自动化流程**
   - ✅ 查询筛选自动化
   - ✅ Rubric生成自动化
   - ✅ 评估流程自动化
   - ✅ 多语言自动识别

## 📊 当前实现完整度

### ✅ 完全实现 (100%)
- **查询价值评估**: 7维度POET评分系统
- **动态评估标准**: 自适应Rubric生成
- **质量评估**: RACE 4维度评估
- **事实验证**: FACT引用可信度评估
- **效率评估**: 时间成本分析
- **战略评估**: 复杂任务处理能力
- **多语言支持**: 中英文混合处理
- **配置驱动**: 统一配置管理

### 🔄 持续优化
- **端到端测试**: 增强集成测试覆盖
- **性能优化**: 并行处理和缓存机制
- **可视化报告**: 结果展示和分析界面
- **扩展性**: 新评估维度插件化

## 📈 核心优势

1. **价值导向**: 从技术指标转向商业价值评估
2. **自适应性**: 动态权重和标准，避免过拟合
3. **全面性**: 效率+质量+战略三维价值框架
4. **可信度**: 事实验证和引用可信度评估
5. **实用性**: 对齐真实企业应用场景

## 🎯 结论

**POET Bench已经实现了从原始查询到多维价值评估的完整闭环**，具备以下核心能力：

1. **智能化查询管理** - 7维度价值评估和自动筛选
2. **自适应评估体系** - 动态权重和标准生成
3. **多层次价值评估** - 效率、质量、战略三维并举
4. **商业ROI量化** - Tech-Market-Fit的直接衡量

相比传统基准测试，POET Bench真正实现了"始于终局"的设计理念，为AI智能体的商业化应用提供了可信的价值评估标准。