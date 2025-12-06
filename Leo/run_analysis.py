# Café Business Analysis - Volatility-Profitability Matrix
# Executable Python Script Version

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set visualization style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

print("=" * 80)
print("CAFÉ VOLATILITY-PROFITABILITY MATRIX ANALYSIS")
print("=" * 80)

# Load datasets
print("\n[1/8] Loading datasets...")
transactions = pd.read_csv('Dataset/Cafe Transaction store.csv')
date_info = pd.read_csv('Dataset/Cafe DateInfo.csv')
metadata = pd.read_csv('Dataset/Cafe Sell MetaData.csv')

print(f"✓ Transactions: {len(transactions):,} rows")
print(f"✓ Date Info: {len(date_info):,} rows")
print(f"✓ Metadata: {len(metadata):,} rows")

# Merge and prepare data
print("\n[2/8] Preparing and merging data...")
df = transactions.merge(date_info, on='CALENDAR_DATE', how='left')
df['DATE'] = pd.to_datetime(df['CALENDAR_DATE'], format='%m/%d/%y', errors='coerce')
df['MONTH'] = df['DATE'].dt.month
df['QUARTER'] = df['DATE'].dt.quarter
df['REVENUE'] = df['PRICE'] * df['QUANTITY']
df['TEMP_BIN'] = pd.cut(df['AVERAGE_TEMPERATURE'], 
                         bins=[0, 32, 50, 70, 90], 
                         labels=['Cold (<32°F)', 'Cool (32-50°F)', 'Moderate (50-70°F)', 'Hot (70°F+)'])

# Expand combo items
combo_items = []
for idx, row in df[df['SELL_CATEGORY'] == 2].iterrows():
    combo_products = metadata[metadata['SELL_ID'] == row['SELL_ID']]
    for _, product in combo_products.iterrows():
        combo_items.append({
            'DATE': row['DATE'],
            'ITEM_NAME': product['ITEM_NAME'],
            'QUANTITY': row['QUANTITY'],
            'REVENUE': row['REVENUE'] / len(combo_products),
            'PRICE': row['PRICE'] / len(combo_products),
            'SELL_CATEGORY': 'COMBO',
            'IS_WEEKEND': row['IS_WEEKEND'],
            'IS_SCHOOLBREAK': row['IS_SCHOOLBREAK'],
            'AVERAGE_TEMPERATURE': row['AVERAGE_TEMPERATURE'],
            'IS_OUTDOOR': row['IS_OUTDOOR'],
            'HOLIDAY': row['HOLIDAY'],
            'TEMP_BIN': row['TEMP_BIN'],
            'MONTH': row['MONTH'],
            'QUARTER': row['QUARTER']
        })

# Single items
single_items = []
for idx, row in df[df['SELL_CATEGORY'] == 0].iterrows():
    product = metadata[metadata['SELL_ID'] == row['SELL_ID']].iloc[0]
    single_items.append({
        'DATE': row['DATE'],
        'ITEM_NAME': product['ITEM_NAME'],
        'QUANTITY': row['QUANTITY'],
        'REVENUE': row['REVENUE'],
        'PRICE': row['PRICE'],
        'SELL_CATEGORY': 'SINGLE',
        'IS_WEEKEND': row['IS_WEEKEND'],
        'IS_SCHOOLBREAK': row['IS_SCHOOLBREAK'],
        'AVERAGE_TEMPERATURE': row['AVERAGE_TEMPERATURE'],
        'IS_OUTDOOR': row['IS_OUTDOOR'],
        'HOLIDAY': row['HOLIDAY'],
        'TEMP_BIN': row['TEMP_BIN'],
        'MONTH': row['MONTH'],
        'QUARTER': row['QUARTER']
    })

item_df = pd.DataFrame(combo_items + single_items)
print(f"✓ Item-level records: {len(item_df):,}")

# Profitability analysis
print("\n[3/8] Calculating profitability metrics...")
profitability = item_df.groupby('ITEM_NAME').agg({
    'REVENUE': 'sum',
    'QUANTITY': 'sum',
    'PRICE': 'mean'
}).reset_index()

profitability['AVG_REVENUE_PER_UNIT'] = profitability['REVENUE'] / profitability['QUANTITY']
n_days = (item_df['DATE'].max() - item_df['DATE'].min()).days
profitability['REVENUE_PER_DAY'] = profitability['REVENUE'] / n_days

print("\nProfitability by Item:")
print(profitability.sort_values('REVENUE', ascending=False).to_string(index=False))

# Volatility analysis
print("\n[4/8] Calculating volatility metrics...")
daily_sales = item_df.groupby(['DATE', 'ITEM_NAME']).agg({
    'QUANTITY': 'sum',
    'REVENUE': 'sum'
}).reset_index()

volatility = daily_sales.groupby('ITEM_NAME').agg({
    'QUANTITY': ['mean', 'std']
}).reset_index()
volatility.columns = ['ITEM_NAME', 'AVG_DAILY_QTY', 'STD_DAILY_QTY']
volatility['VOLATILITY'] = (volatility['STD_DAILY_QTY'] / volatility['AVG_DAILY_QTY']) * 100

print("\nVolatility (Coefficient of Variation %):")
print(volatility.sort_values('VOLATILITY', ascending=False).to_string(index=False))

# Matrix construction
print("\n[5/8] Building Volatility-Profitability Matrix...")
matrix_df = profitability.merge(volatility[['ITEM_NAME', 'VOLATILITY']], on='ITEM_NAME')
matrix_df['PROFITABILITY_SCORE'] = (matrix_df['REVENUE'] - matrix_df['REVENUE'].min()) / (matrix_df['REVENUE'].max() - matrix_df['REVENUE'].min()) * 100
matrix_df['VOLATILITY_SCORE'] = matrix_df['VOLATILITY']

prof_median = matrix_df['PROFITABILITY_SCORE'].median()
vol_median = matrix_df['VOLATILITY_SCORE'].median()

def classify_quadrant(row):
    if row['PROFITABILITY_SCORE'] >= prof_median and row['VOLATILITY_SCORE'] < vol_median:
        return 'Stars (High Profit, Low Volatility)'
    elif row['PROFITABILITY_SCORE'] >= prof_median and row['VOLATILITY_SCORE'] >= vol_median:
        return 'Wildcards (High Profit, High Volatility)'
    elif row['PROFITABILITY_SCORE'] < prof_median and row['VOLATILITY_SCORE'] < vol_median:
        return 'Steady (Low Profit, Low Volatility)'
    else:
        return 'Problem (Low Profit, High Volatility)'

matrix_df['QUADRANT'] = matrix_df.apply(classify_quadrant, axis=1)

print("\nVOLATILITY-PROFITABILITY MATRIX:")
print(matrix_df[['ITEM_NAME', 'REVENUE', 'VOLATILITY', 'QUADRANT']].to_string(index=False))

# Contextual analysis
print("\n[6/8] Analyzing contextual factors...")
item_df['IS_HOLIDAY'] = item_df['HOLIDAY'].apply(lambda x: 0 if x == 'NULL' or pd.isna(x) else 1)

# Temperature correlation
temp_corr = daily_sales.merge(item_df[['DATE', 'ITEM_NAME', 'AVERAGE_TEMPERATURE']].drop_duplicates(), 
                               on=['DATE', 'ITEM_NAME'])
temp_correlation = temp_corr.groupby('ITEM_NAME').apply(
    lambda x: x['AVERAGE_TEMPERATURE'].corr(x['QUANTITY'])
).reset_index()
temp_correlation.columns = ['ITEM_NAME', 'TEMP_CORRELATION']

print("\nTemperature Correlation:")
print(temp_correlation.sort_values('TEMP_CORRELATION', ascending=False).to_string(index=False))

# Weekend impact
weekend_impact = item_df.groupby(['ITEM_NAME', 'IS_WEEKEND'])['QUANTITY'].sum().unstack(fill_value=0)
weekend_impact.columns = ['Weekday', 'Weekend']
weekend_impact['Weekend_Lift_%'] = ((weekend_impact['Weekend'] - weekend_impact['Weekday']) / weekend_impact['Weekday']) * 100

print("\nWeekend Impact:")
print(weekend_impact.to_string())

# Holiday impact
holiday_impact = item_df.groupby(['ITEM_NAME', 'IS_HOLIDAY'])['QUANTITY'].sum().unstack(fill_value=0)
holiday_impact.columns = ['Non-Holiday', 'Holiday']
holiday_impact['Holiday_Lift_%'] = ((holiday_impact['Holiday'] - holiday_impact['Non-Holiday']) / holiday_impact['Non-Holiday']) * 100

print("\nHoliday Impact:")
print(holiday_impact.to_string())

# Visualizations
print("\n[7/8] Creating visualizations...")

# 1. Volatility-Profitability Matrix
colors_dict = {
    'Stars (High Profit, Low Volatility)': 'green',
    'Wildcards (High Profit, High Volatility)': 'gold',
    'Steady (Low Profit, Low Volatility)': 'lightblue',
    'Problem (Low Profit, High Volatility)': 'red'
}

plt.figure(figsize=(14, 10))
for quadrant in matrix_df['QUADRANT'].unique():
    subset = matrix_df[matrix_df['QUADRANT'] == quadrant]
    plt.scatter(subset['PROFITABILITY_SCORE'], subset['VOLATILITY_SCORE'], 
                c=colors_dict[quadrant], label=quadrant, s=500, alpha=0.7, edgecolors='black', linewidths=2)
    
    for idx, row in subset.iterrows():
        plt.annotate(row['ITEM_NAME'], 
                    (row['PROFITABILITY_SCORE'], row['VOLATILITY_SCORE']),
                    fontsize=12, fontweight='bold', ha='center', va='center')

plt.axhline(y=vol_median, color='gray', linestyle='--', linewidth=2, alpha=0.5)
plt.axvline(x=prof_median, color='gray', linestyle='--', linewidth=2, alpha=0.5)
plt.xlabel('Profitability Score →', fontsize=14, fontweight='bold')
plt.ylabel('Volatility (CV%) →', fontsize=14, fontweight='bold')
plt.title('Volatility-Profitability Matrix: Menu Portfolio Analysis', fontsize=16, fontweight='bold')
plt.legend(loc='upper left', fontsize=11, frameon=True, shadow=True)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('volatility_profitability_matrix.png', dpi=300, bbox_inches='tight')
print("✓ Saved: volatility_profitability_matrix.png")

# 2. Profitability overview
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

axes[0, 0].bar(profitability['ITEM_NAME'], profitability['REVENUE'], color='steelblue')
axes[0, 0].set_title('Total Revenue by Item', fontsize=14, fontweight='bold')
axes[0, 0].set_ylabel('Revenue ($)', fontsize=12)
axes[0, 0].tick_params(axis='x', rotation=45)

axes[0, 1].bar(profitability['ITEM_NAME'], profitability['QUANTITY'], color='coral')
axes[0, 1].set_title('Total Units Sold', fontsize=14, fontweight='bold')
axes[0, 1].set_ylabel('Quantity', fontsize=12)
axes[0, 1].tick_params(axis='x', rotation=45)

axes[1, 0].bar(profitability['ITEM_NAME'], profitability['AVG_REVENUE_PER_UNIT'], color='seagreen')
axes[1, 0].set_title('Average Revenue per Unit', fontsize=14, fontweight='bold')
axes[1, 0].set_ylabel('Revenue per Unit ($)', fontsize=12)
axes[1, 0].tick_params(axis='x', rotation=45)

axes[1, 1].bar(profitability['ITEM_NAME'], profitability['REVENUE_PER_DAY'], color='purple')
axes[1, 1].set_title('Average Daily Revenue', fontsize=14, fontweight='bold')
axes[1, 1].set_ylabel('Revenue per Day ($)', fontsize=12)
axes[1, 1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('profitability_overview.png', dpi=300, bbox_inches='tight')
print("✓ Saved: profitability_overview.png")

# Strategic recommendations
print("\n[8/8] Generating strategic recommendations...")
print("\n" + "=" * 80)
print("STRATEGIC RECOMMENDATIONS BY QUADRANT")
print("=" * 80)

for quadrant in sorted(matrix_df['QUADRANT'].unique()):
    items = matrix_df[matrix_df['QUADRANT'] == quadrant]['ITEM_NAME'].tolist()
    print(f"\n{quadrant}:")
    print(f"  Products: {', '.join(items)}")
    
    if 'Stars' in quadrant:
        print("  → STRATEGY: MAXIMIZE")
        print("     • Ensure consistent availability")
        print("     • Premium positioning and pricing")
        print("     • Promote heavily in marketing")
    
    elif 'Wildcards' in quadrant:
        print("  → STRATEGY: STABILIZE")
        print("     • Weather-based inventory management")
        print("     • Dynamic pricing strategies")
        print("     • Targeted promotions during slow periods")
    
    elif 'Steady' in quadrant:
        print("  → STRATEGY: OPTIMIZE")
        print("     • Bundle with high-margin items")
        print("     • Use as traffic drivers")
        print("     • Cost reduction through bulk purchasing")
    
    else:
        print("  → STRATEGY: REFORM OR REMOVE")
        print("     • Evaluate viability")
        print("     • Test repositioning")
        print("     • Consider menu simplification")

# Profit per hour analysis
hours_per_day = 12
matrix_df['REVENUE_PER_HOUR'] = matrix_df['REVENUE_PER_DAY'] / hours_per_day
total_revenue = matrix_df['REVENUE'].sum()
total_hours = n_days * hours_per_day
current_rph = total_revenue / total_hours

print("\n" + "=" * 80)
print("PROFIT PER HOUR ANALYSIS")
print("=" * 80)
print(f"\nCurrent Revenue Per Hour: ${current_rph:.2f}")
print("\nRevenue Per Hour by Product:")
for idx, row in matrix_df.sort_values('REVENUE_PER_HOUR', ascending=False).iterrows():
    print(f"  {row['ITEM_NAME']}: ${row['REVENUE_PER_HOUR']:.2f}/hour")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)
print("\nGenerated files:")
print("  • volatility_profitability_matrix.png")
print("  • profitability_overview.png")
print("  • business_recommendations.md (strategic guide)")
print("\nNext steps:")
print("  1. Review the matrix visualization")
print("  2. Read business_recommendations.md for detailed strategies")
print("  3. Implement quick wins within 30 days")
print("  4. Track KPIs weekly")
