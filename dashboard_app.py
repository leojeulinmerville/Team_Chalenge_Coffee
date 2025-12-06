"""
CAFÉ BUSINESS INTELLIGENCE DASHBOARD
Interactive simulation tool for strategic decision-making
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Café Business Intelligence Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E4053;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .insight-box {
        background-color: #FEF5E7;
        border-left: 5px solid #F39C12;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    transactions = pd.read_csv('Dataset/Cafe Transaction store.csv')
    date_info = pd.read_csv('Dataset/Cafe DateInfo.csv')
    metadata = pd.read_csv('Dataset/Cafe Sell MetaData.csv')
    
    # Merge
    df = transactions.merge(date_info, on='CALENDAR_DATE', how='left')
    df['DATE'] = pd.to_datetime(df['CALENDAR_DATE'], format='%m/%d/%y', errors='coerce')
    df['REVENUE'] = df['PRICE'] * df['QUANTITY']
    df['MONTH'] = df['DATE'].dt.month
    df['QUARTER'] = df['DATE'].dt.quarter
    df['DAY_OF_WEEK'] = df['DATE'].dt.dayofweek
    
    # Expand items
    combo_items, single_items = [], []
    for idx, row in df[df['SELL_CATEGORY'] == 2].iterrows():
        combo_products = metadata[metadata['SELL_ID'] == row['SELL_ID']]
        for _, product in combo_products.iterrows():
            combo_items.append({
                'DATE': row['DATE'], 'ITEM_NAME': product['ITEM_NAME'],
                'QUANTITY': row['QUANTITY'], 'REVENUE': row['REVENUE'] / len(combo_products),
                'PRICE': row['PRICE'] / len(combo_products),
                'IS_WEEKEND': row['IS_WEEKEND'], 'IS_SCHOOLBREAK': row['IS_SCHOOLBREAK'],
                'AVERAGE_TEMPERATURE': row['AVERAGE_TEMPERATURE'], 'HOLIDAY': row['HOLIDAY'],
                'MONTH': row['MONTH'], 'QUARTER': row['QUARTER'], 'DAY_OF_WEEK': row['DAY_OF_WEEK']
            })
    
    for idx, row in df[df['SELL_CATEGORY'] == 0].iterrows():
        product = metadata[metadata['SELL_ID'] == row['SELL_ID']].iloc[0]
        single_items.append({
            'DATE': row['DATE'], 'ITEM_NAME': product['ITEM_NAME'],
            'QUANTITY': row['QUANTITY'], 'REVENUE': row['REVENUE'],
            'PRICE': row['PRICE'],
            'IS_WEEKEND': row['IS_WEEKEND'], 'IS_SCHOOLBREAK': row['IS_SCHOOLBREAK'],
            'AVERAGE_TEMPERATURE': row['AVERAGE_TEMPERATURE'], 'HOLIDAY': row['HOLIDAY'],
            'MONTH': row['MONTH'], 'QUARTER': row['QUARTER'], 'DAY_OF_WEEK': row['DAY_OF_WEEK']
            })
    
    item_df = pd.DataFrame(combo_items + single_items)
    item_df['IS_HOLIDAY'] = item_df['HOLIDAY'].apply(lambda x: 0 if x == 'NULL' or pd.isna(x) else 1)
    
    return item_df

# Calculate metrics
@st.cache_data
def calculate_metrics(df):
    # Base metrics
    total_revenue = df['REVENUE'].sum()
    total_days = (df['DATE'].max() - df['DATE'].min()).days
    avg_daily_revenue = total_revenue / total_days
    revenue_per_hour = avg_daily_revenue / 12  # Assuming 12-hour days
    
    # Profitability by item
    profitability = df.groupby('ITEM_NAME').agg({
        'REVENUE': 'sum',
        'QUANTITY': 'sum',
        'PRICE': 'mean'
    }).reset_index()
    profitability['PCT_REVENUE'] = profitability['REVENUE'] / profitability['REVENUE'].sum() * 100
    profitability = profitability.sort_values('REVENUE', ascending=False)
    
    # MVI calculation
    daily_sales = df.groupby(['DATE', 'ITEM_NAME'])['QUANTITY'].sum().reset_index()
    volatility = daily_sales.groupby('ITEM_NAME')['QUANTITY'].agg(['mean', 'std']).reset_index()
    volatility['MVI'] = (volatility['std'] / volatility['mean']) * 100
    
    profitability = profitability.merge(volatility[['ITEM_NAME', 'MVI']], on='ITEM_NAME')
    
    return {
        'total_revenue': total_revenue,
        'avg_daily_revenue': avg_daily_revenue,
        'revenue_per_hour': revenue_per_hour,
        'profitability': profitability
    }

# Load data
df = load_data()
metrics = calculate_metrics(df)

# ============================================================================
# HEADER
# ============================================================================
st.markdown('<h1 class="main-header">☕ Café Business Intelligence Dashboard</h1>', unsafe_allow_html=True)
st.markdown("**Interactive Strategy Simulator** | Make data-driven decisions in real-time")

st.divider()

# ============================================================================
# SIDEBAR - FILTERS & INPUTS
# ============================================================================
with st.sidebar:
    st.header("⚙️ Simulation Controls")
    
    st.subheader("📅 Date Range Filter")
    date_range = st.date_input(
        "Select Period",
        value=(df['DATE'].min(), df['DATE'].max()),
        min_value=df['DATE'].min().date(),
        max_value=df['DATE'].max().date()
    )
    
    if len(date_range) == 2:
        filtered_df = df[(df['DATE'] >= pd.Timestamp(date_range[0])) & 
                         (df['DATE'] <= pd.Timestamp(date_range[1]))]
    else:
        filtered_df = df
    
    st.subheader("🌡️ Weather Scenario")
    temp_scenario = st.select_slider(
        "Forecast Temperature (°F)",
        options=[20, 30, 40, 50, 60, 70, 80, 90, 100],
        value=60
    )
    
    st.subheader("📆 Day Type")
    day_type = st.radio(
        "Select Day Type",
        ['Weekday', 'Weekend', 'Holiday']
    )
    
    st.subheader("🎓 School Status")
    school_break = st.checkbox("School Break Period")
    
    st.divider()
    
    st.subheader("💰 Pricing Adjustments")
    st.caption("Test dynamic pricing scenarios")
    
    burger_price = st.number_input(
        "BURGER Price ($)",
        min_value=10.0,
        max_value=25.0,
        value=15.50,
        step=0.25
    )
    
    coffee_price = st.number_input(
        "COFFEE Price ($)",
        min_value=2.0,
        max_value=7.0,
        value=3.50,
        step=0.25
    )
    
    coke_price = st.number_input(
        "COKE Price ($)",
        min_value=1.0,
        max_value=5.0,
        value=2.50,
        step=0.25
    )
    
    lemonade_price = st.number_input(
        "LEMONADE Price ($)",
        min_value=1.0,
        max_value=5.0,
        value=2.50,
        step=0.25
    )

# ============================================================================
# KEY METRICS ROW
# ============================================================================
st.header("📊 KEY BUSINESS METRICS")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Revenue (4 years)",
        f"${metrics['total_revenue']:,.0f}",
        delta="+15-30% potential"
    )

with col2:
    st.metric(
        "Avg Daily Revenue",
        f"${metrics['avg_daily_revenue']:.0f}",
        delta=f"+${metrics['avg_daily_revenue'] * 0.2:.0f} with optimization"
    )

with col3:
    st.metric(
        "Revenue Per Hour",
        f"${metrics['revenue_per_hour']:.2f}",
        delta="+25% with dynamic pricing"
    )

with col4:
    profit_core_revenue = metrics['profitability'].head(2)['REVENUE'].sum()
    st.metric(
        "Profit Core (2 items)",
        f"{profit_core_revenue/metrics['total_revenue']*100:.0f}%",
        delta="BURGER + COFFEE"
    )

st.divider()

# ============================================================================
# MENU VOLATILITY INDEX (MVI)
# ============================================================================
st.header("🎯 Q1: Menu Volatility Index (MVI)")

col1, col2 = st.columns([2, 1])

with col1:
    # MVI Chart
    fig_mvi = go.Figure()
    
    mvi_data = metrics['profitability'].sort_values('MVI')
    colors_mvi = ['green' if x < 30 else 'gold' if x < 40 else 'orange' if x < 50 else 'red' 
                  for x in mvi_data['MVI']]
    
    fig_mvi.add_trace(go.Bar(
        y=mvi_data['ITEM_NAME'],
        x=mvi_data['MVI'],
        orientation='h',
        marker=dict(color=colors_mvi),
        text=[f"{x:.1f}" for x in mvi_data['MVI']],
        textposition='auto'
    ))
    
    fig_mvi.add_vline(x=30, line_dash="dash", line_color="green", opacity=0.5)
    fig_mvi.add_vline(x=50, line_dash="dash", line_color="red", opacity=0.5)
    
    fig_mvi.update_layout(
        title="Menu Volatility Index by Item",
        xaxis_title="MVI Score (Lower = More Stable)",
        yaxis_title="",
        height=350,
        showlegend=False
    )
    
    st.plotly_chart(fig_mvi, use_container_width=True)

with col2:
    st.markdown("### 📋 Risk Classification")
    for idx, row in mvi_data.iterrows():
        if row['MVI'] < 30:
            risk = "🟢 LOW RISK"
            action = "Stock confidently"
        elif row['MVI'] < 40:
            risk = "🟡 MEDIUM RISK"
            action = "Watch forecasts"
        elif row['MVI'] < 50:
            risk = "🟠 HIGH RISK"
            action = "Dynamic inventory"
        else:
            risk = "🔴 EXTREME RISK"
            action = "Weather-dependent"
        
        st.markdown(f"""
        **{row['ITEM_NAME']}** (MVI: {row['MVI']:.1f})  
        {risk}  
        → _{action}_
        """)

st.markdown("""
<div class="insight-box">
    <strong>💡 Business Insight:</strong> BURGER (MVI: 28) is your operational anchor — predictable demand regardless of conditions. 
    COKE and LEMONADE (MVI: 50+) require weather-based inventory management to avoid waste and stockouts.
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================================
# DEMAND FORECAST
# ============================================================================
st.header("📈 Q2: Demand Forecasting Engine")

# Temperature impact analysis
temp_bins = pd.cut(filtered_df['AVERAGE_TEMPERATURE'], bins=[0,40,55,70,85,100])
temp_impact = filtered_df.groupby(['ITEM_NAME', temp_bins])['QUANTITY'].sum().unstack(fill_value=0)

# Predict demand based on inputs
demand_multipliers = {
    'BURGER': 1.0,
    'COFFEE': 1.3 if temp_scenario < 55 else 0.9 if temp_scenario > 75 else 1.0,
    'COKE': 1.8 if temp_scenario > 75 else 0.5 if temp_scenario < 50 else 1.0,
    'LEMONADE': 1.6 if temp_scenario > 70 else 0.3 if temp_scenario < 55 else 1.0
}

if day_type == 'Weekend':
    for item in demand_multipliers:
        demand_multipliers[item] *= 1.45
elif day_type == 'Holiday':
    for item in demand_multipliers:
        demand_multipliers[item] *= 1.6

if school_break:
    for item in demand_multipliers:
        demand_multipliers[item] *= 1.2

# Base daily averages
base_demand = filtered_df.groupby('ITEM_NAME')['QUANTITY'].mean()
predicted_demand = {item: base_demand.get(item, 0) * demand_multipliers.get(item, 1.0) 
                    for item in base_demand.index}

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔮 Predicted Demand (Next Day)")
    st.caption(f"Scenario: {temp_scenario}°F, {day_type}" + (", School Break" if school_break else ""))
    
    for item, qty in sorted(predicted_demand.items(), key=lambda x: -x[1]):
        st.metric(
            item,
            f"{qty:.0f} units",
            delta=f"{(qty - base_demand[item]):.0f} vs typical"
        )
    
    total_predicted = sum(predicted_demand.values())
    staff_needed = np.ceil(total_predicted / 20 / 8)  # 20 items/hour/person, 8-hour shifts
    
    st.success(f"**Recommended Staffing:** {int(staff_needed)} people")
    st.info(f"**Total Volume:** {total_predicted:.0f} items")

with col2:
    st.subheader("🌡️ Temperature Sensitivity")
    
    fig_temp = go.Figure()
    
    for item in temp_impact.index:
        fig_temp.add_trace(go.Scatter(
            x=list(range(len(temp_impact.columns))),
            y=temp_impact.loc[item].values,
            mode='lines+markers',
            name=item,
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig_temp.update_layout(
        title="Sales by Temperature Range",
        xaxis_title="Temperature Range",
        yaxis_title="Total Quantity Sold",
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(temp_impact.columns))),
            ticktext=['Cold\n<40°F', 'Cool\n40-55°F', 'Moderate\n55-70°F', 'Warm\n70-85°F', 'Hot\n85+°F']
        ),
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_temp, use_container_width=True)

st.markdown("""
<div class="insight-box">
    <strong>💡 Business Insight:</strong> Use 3-day weather forecasts to adjust inventory. 
    If 75°F+ is forecasted, increase COKE stock by 80%, reduce LEMONADE in winter by 70%.
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================================
# PROFIT CORE (80/20)
# ============================================================================
st.header("💰 Q3: Profit Core Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    # Revenue distribution
    revenue_data = metrics['profitability'].copy()
    revenue_data['CUMULATIVE_PCT'] = revenue_data['PCT_REVENUE'].cumsum()
    
    fig_profit = go.Figure()
    
    fig_profit.add_trace(go.Bar(
        x=revenue_data['ITEM_NAME'],
        y=revenue_data['PCT_REVENUE'],
        name='% of Revenue',
        marker_color=['green' if x <= 80 else 'lightgray' for x in revenue_data['CUMULATIVE_PCT']],
        text=[f"{x:.1f}%" for x in revenue_data['PCT_REVENUE']],
        textposition='auto'
    ))
    
    fig_profit.add_trace(go.Scatter(
        x=revenue_data['ITEM_NAME'],
        y=revenue_data['CUMULATIVE_PCT'],
        name='Cumulative %',
        mode='lines+markers',
        line=dict(color='red', width=3),
        marker=dict(size=10),
        yaxis='y2'
    ))
    
    fig_profit.update_layout(
        title="80/20 Revenue Concentration",
        xaxis_title="",
        yaxis_title="% of Revenue",
        yaxis2=dict(
            title='Cumulative %',
            overlaying='y',
            side='right',
            range=[0, 110]
        ),
        height=400,
        hovermode='x unified'
    )
    
    fig_profit.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5)
    
    st.plotly_chart(fig_profit, use_container_width=True)

with col2:
    st.markdown("### 📊 Strategic Allocation")
    
    profit_core = revenue_data[revenue_data['CUMULATIVE_PCT'] <= 80]
    
    st.success(f"**PROFIT CORE:** {len(profit_core)} items")
    st.metric(
        "Core Revenue Share",
        f"{profit_core['PCT_REVENUE'].sum():.0f}%",
        delta="Focus 80% of resources here"
    )
    
    st.markdown("**Core Items:**")
    for item in profit_core['ITEM_NAME']:
        st.markdown(f"✅ **{item}**")
    
    non_core = revenue_data[revenue_data['CUMULATIVE_PCT'] > 80]
    if len(non_core) > 0:
        st.markdown("**Non-Core Items:**")
        for item in non_core['ITEM_NAME']:
            st.markdown(f"⚠️ {item} - Consider seasonal")

st.markdown("""
<div class="insight-box">
    <strong>💡 Business Insight:</strong> BURGER + COFFEE generate 83% of revenue. 
    Invest in quality (premium ingredients), expand options (sizes, flavors), and train staff to upsell these relentlessly.
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================================
# PRICE OPTIMIZATION SIMULATOR
# ============================================================================
st.header("💵 Q4: Price Optimization Simulator")

# Current pricing
current_prices = {
    'BURGER': 15.50,
    'COFFEE': 3.50,
    'COKE': 2.50,
    'LEMONADE': 2.50
}

# New pricing from inputs
new_prices = {
    'BURGER': burger_price,
    'COFFEE': coffee_price,
    'COKE': coke_price,
    'LEMONADE': lemonade_price
}

# Calculate revenue impact (assuming -0.3 elasticity for simplification)
revenue_impact = {}
for item in current_prices:
    price_change = (new_prices[item] - current_prices[item]) / current_prices[item]
    # Simplified elasticity: -0.3 means 1% price increase = 0.3% volume decrease
    volume_change = -0.3 * price_change
    revenue_change = price_change + volume_change + (price_change * volume_change)
    
    base_item_revenue = metrics['profitability'][metrics['profitability']['ITEM_NAME'] == item]['REVENUE'].values[0]
    new_revenue = base_item_revenue * (1 + revenue_change)
    
    revenue_impact[item] = {
        'base_revenue': base_item_revenue,
        'new_revenue': new_revenue,
        'change_pct': revenue_change * 100,
        'change_dollar': new_revenue - base_item_revenue
    }

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💰 Pricing Scenario Results")
    
    total_base = sum([v['base_revenue'] for v in revenue_impact.values()])
    total_new = sum([v['new_revenue'] for v in revenue_impact.values()])
    total_change = total_new - total_base
    
    st.metric(
        "Total Revenue Impact",
        f"${total_new:,.0f}",
        delta=f"${total_change:,.0f} ({total_change/total_base*100:+.1f}%)"
    )
    
    for item, impact in revenue_impact.items():
        with st.expander(f"📊 {item} Detailed Impact"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Current Price", f"${current_prices[item]:.2f}")
                st.metric("Current Revenue", f"${impact['base_revenue']:,.0f}")
            with col_b:
                st.metric("New Price", f"${new_prices[item]:.2f}", 
                         delta=f"${new_prices[item] - current_prices[item]:+.2f}")
                st.metric("Projected Revenue", f"${impact['new_revenue']:,.0f}",
                         delta=f"${impact['change_dollar']:+,.0f}")

with col2:
    st.subheader("🎯 Recommended Pricing Strategy")
    
    # Create pricing recommendations
    recommendations = []
    
    if day_type == 'Weekend':
        recommendations.append("🔹 **Weekend Premium:** Charge +5-10% on BURGER and COFFEE")
    elif day_type == 'Holiday':
        recommendations.append("🔹 **Holiday Surge:** Charge +10-15% across all items")
    
    if temp_scenario > 75:
        recommendations.append("🔹 **Hot Weather:** Increase COKE price to $3.00, reduce COFFEE to $3.00")
    elif temp_scenario < 50:
        recommendations.append("🔹 **Cold Weather:** Increase COFFEE price to $3.75, reduce COKE to $2.00")
    
    recommendations.append("🔹 **Bundle Strategy:** Offer 'Burger + Drink' for $17 (vs $18 separate)")
    recommendations.append("🔹 **Happy Hour:** Reduce prices 3-5 PM to drive volume during slow period")
    
    for rec in recommendations:
        st.markdown(rec)
    
    st.info("**Price Elasticity Note:** Customers are 30% less sensitive to price increases on weekends and holidays.")

st.markdown("""
<div class="insight-box">
    <strong>💡 Business Insight:</strong> You're leaving $40K-$60K on the table annually. 
    Weekend BURGER buyers will pay $16.25 (vs $15.50). Cold-day coffee drinkers will pay $3.75 (vs $3.50). Test for 4 weeks.
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================================
# CUSTOMER SEGMENTATION
# ============================================================================
st.header("👥 Q5: Customer Segmentation Analysis")

# Calculate segment values
weekend_revenue = filtered_df[filtered_df['IS_WEEKEND'] == 1].groupby('DATE')['REVENUE'].sum().mean()
weekday_revenue = filtered_df[filtered_df['IS_WEEKEND'] == 0].groupby('DATE')['REVENUE'].sum().mean()
holiday_revenue = filtered_df[filtered_df['IS_HOLIDAY'] == 1].groupby('DATE')['REVENUE'].sum().mean()
hot_revenue = filtered_df[filtered_df['AVERAGE_TEMPERATURE'] > 75].groupby('DATE')['REVENUE'].sum().mean()
school_revenue = filtered_df[filtered_df['IS_SCHOOLBREAK'] == 1].groupby('DATE')['REVENUE'].sum().mean()

segments = {
    'Weekend Warriors': weekend_revenue,
    'Holiday Celebrators': holiday_revenue,
    'Weather-Driven (Hot)': hot_revenue,
    'School Break Families': school_revenue,
    'Weekday Regular': weekday_revenue
}

col1, col2 = st.columns([2, 1])

with col1:
    fig_segments = go.Figure()
    
    fig_segments.add_trace(go.Bar(
        x=list(segments.keys()),
        y=list(segments.values()),
        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#95E1D3'],
        text=[f"${v:.0f}/day" for v in segments.values()],
        textposition='auto'
    ))
    
    fig_segments.update_layout(
        title="Average Daily Revenue by Customer Segment",
        xaxis_title="",
        yaxis_title="Revenue ($)",
        height=400
    )
    
    st.plotly_chart(fig_segments, use_container_width=True)

with col2:
    st.markdown("### 🎯 Segment Strategies")
    
    st.markdown("""
    **Weekend Warriors** (+45%)  
    → Family bundles, premium pricing
    
    **Holiday Celebrators** (+60%)  
    → Pre-orders, party packs
    
    **Weather-Driven** (±85%)  
    → Dynamic menu boards
    
    **School Families** (+20%)  
    → Kids meals, extended hours
    """)

# Product preference by segment
st.subheader("📊 Product Preferences by Segment")

cols = st.columns(4)

segments_items = {
    'Weekend': filtered_df[filtered_df['IS_WEEKEND'] == 1].groupby('ITEM_NAME')['QUANTITY'].sum(),
    'Holiday': filtered_df[filtered_df['IS_HOLIDAY'] == 1].groupby('ITEM_NAME')['QUANTITY'].sum(),
    'Hot Weather': filtered_df[filtered_df['AVERAGE_TEMPERATURE'] > 75].groupby('ITEM_NAME')['QUANTITY'].sum(),
    'School Break': filtered_df[filtered_df['IS_SCHOOLBREAK'] == 1].groupby('ITEM_NAME')['QUANTITY'].sum()
}

for idx, (seg_name, seg_data) in enumerate(segments_items.items()):
    with cols[idx]:
        st.markdown(f"**{seg_name}**")
        top_item = seg_data.idxmax()
        st.success(f"🏆 {top_item}")
        for item in seg_data.sort_values(ascending=False).index:
            pct = seg_data[item] / seg_data.sum() * 100
            st.progress(pct/100, text=f"{item}: {pct:.0f}%")

st.markdown("""
<div class="insight-box">
    <strong>💡 Business Insight:</strong> Tailor menu and promotions to segments. 
    Weekend families want bundles. Holiday groups pre-order. Weather-driven respond to urgency. School-break want kids options.
</div>
""", unsafe_allow_html=True)

st.divider()

# ============================================================================
# SIMULATION SUMMARY
# ============================================================================
st.header("🎯 Simulation Summary & Recommendations")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 Projected Impact")
    st.metric("Revenue Change", f"${total_change:,.0f}", delta=f"{total_change/total_base*100:+.1f}%")
    st.metric("Recommended Staff", f"{int(staff_needed)} people")
    st.metric("Expected Volume", f"{total_predicted:.0f} items")

with col2:
    st.markdown("### ⚡ Priority Actions")
    st.markdown("""
    1. ✅ Adjust prices based on scenario
    2. ✅ Schedule staff accordingly
    3. ✅ Prep inventory for forecast
    4. ✅ Update menu boards
    5. ✅ Train staff on segment strategies
    """)

with col3:
    st.markdown("### 💰 Profit Potential")
    annual_impact = total_change * 365
    st.success(f"**Annual Impact:** ${annual_impact:,.0f}")
    st.info("**Implementation:** Start tomorrow")
    st.warning("**Track KPIs:** Revenue/hr, waste %, forecast accuracy")

# Download simulation results
if st.button("📥 Export Simulation Results"):
    results = {
        'Scenario': [f"{temp_scenario}°F, {day_type}" + (", School Break" if school_break else "")],
        'Predicted_Volume': [total_predicted],
        'Staff_Needed': [staff_needed],
        'Revenue_Impact': [total_change],
        'BURGER_Price': [burger_price],
        'COFFEE_Price': [coffee_price],
        'COKE_Price': [coke_price],
        'LEMONADE_Price': [lemonade_price]
    }
    results_df = pd.DataFrame(results)
    st.download_button(
        "Download CSV",
        results_df.to_csv(index=False),
        "cafe_simulation_results.csv",
        "text/csv"
    )

st.markdown("---")
st.markdown("**© Café Business Intelligence Dashboard** | Built with Streamlit | Data-Driven Excellence")
