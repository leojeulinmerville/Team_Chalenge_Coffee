## Overview

**Challenge Question:** "Find insights to improve our café's business"


## Available Datasets

### 1. Cafe DateInfo.csv
- **CALENDAR_DATE**: Daily dates from 2012-2015
- **YEAR**: Year of transaction
- **HOLIDAY**: Holiday names (New Year, Lunar New Year, etc.)
- **IS_WEEKEND**: Binary indicator (0/1)
- **IS_SCHOOLBREAK**: Binary indicator (0/1)
- **AVERAGE_TEMPERATURE**: Daily temperature
- **IS_OUTDOOR**: Weather suitability for outdoor seating (0/1)

### 2. Cafe Transaction store.csv
- **CALENDAR_DATE**: Transaction date
- **PRICE**: Item price
- **QUANTITY**: Units sold
- **SELL_ID**: Product/combo identifier
- **SELL_CATEGORY**: Category code (0=single item, 2=combo)

### 3. Cafe Sell MetaData.csv
- **SELL_ID**: Product/combo identifier
- **SELL_CATEGORY**: Category type
- **ITEM_ID**: Individual item identifier
- **ITEM_NAME**: Product name (BURGER, COFFEE, COKE, LEMONADE)


## Judging Criteria

### Data Wrangling
- Proper data cleaning and handling of missing values
- Effective merging of datasets
- Feature engineering creativity
- Data transformation quality

### Analysis Depth
- Variety of insights discovered
- Statistical rigor
- Proper use of analytical techniques
- Answering the core question

### Visualization Quality
- Clarity and readability
- Appropriate chart types
- Visual appeal
- Storytelling effectiveness

### Business Recommendations
- Actionability of insights
- Clarity of recommendations
- Evidence-based conclusions
- Creativity and innovation


## Common Pitfalls to Avoid

1. **Overlooking Combos**: Remember SELL_CATEGORY 2 contains multiple items
2. **Ignoring Context**: Temperature is in Fahrenheit (not Celsius)

Good luck with your hackathon! 🚀
