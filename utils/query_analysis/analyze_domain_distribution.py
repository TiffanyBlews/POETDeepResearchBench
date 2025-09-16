import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取CSV文件
df = pd.read_csv('query_scores.csv')

# 统计领域分布
domain_counts = df['领域分类'].value_counts()
total_queries = len(df)

print("Query领域分布统计:")
print("=" * 50)
for domain, count in domain_counts.items():
    percentage = (count / total_queries) * 100
    print(f"{domain}: {count}个 ({percentage:.1f}%)")

print(f"\n总计: {total_queries}个查询")

# 创建图表
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# 饼图
colors = plt.cm.Set3(np.linspace(0, 1, len(domain_counts)))
wedges, texts, autotexts = ax1.pie(domain_counts.values, 
                                   labels=domain_counts.index,
                                   autopct='%1.1f%%',
                                   colors=colors,
                                   startangle=90)

# 美化饼图
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(10)

ax1.set_title('Query领域分布占比图', fontsize=16, fontweight='bold', pad=20)

# 柱状图
bars = ax2.bar(range(len(domain_counts)), domain_counts.values, color=colors)
ax2.set_xlabel('领域分类', fontsize=12)
ax2.set_ylabel('查询数量', fontsize=12)
ax2.set_title('Query领域分布柱状图', fontsize=16, fontweight='bold', pad=20)

# 设置x轴标签
ax2.set_xticks(range(len(domain_counts)))
ax2.set_xticklabels(domain_counts.index, rotation=45, ha='right')

# 在柱状图上添加数值标签
for i, bar in enumerate(bars):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
             f'{int(height)}', ha='center', va='bottom', fontweight='bold')

# 调整布局
plt.tight_layout()

# 保存图片
plt.savefig('query_domain_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# 输出详细统计信息
print("\n详细统计信息:")
print("=" * 50)
domain_stats = []
for domain, count in domain_counts.items():
    percentage = (count / total_queries) * 100
    domain_stats.append({
        '领域': domain,
        '数量': count,
        '占比(%)': f"{percentage:.1f}%"
    })

stats_df = pd.DataFrame(domain_stats)
print(stats_df.to_string(index=False))
