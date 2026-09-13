# MarketLens Business Analytics Report

_Phase 07 output. Data window: 2023-01-01 to 2025-12-27. All figures computed live from `data/processed/*.csv` by `python/analytics/run_analytics.py`._

## 1. Revenue KPIs

- **Total gross revenue:** ₹857,168,939.70
- **Total net revenue (after returns):** ₹803,075,998.49
- **Total discount given:** ₹106,043,181.82
- **Total returned amount:** ₹54,092,941.21
- **Total orders:** 82,800

**Revenue growth YoY:**

|     year |   gross_revenue |    orders |   yoy_growth_pct |
|---------:|----------------:|----------:|-----------------:|
| 2,023.00 |  164,302,526.29 | 15,280.00 |           nan    |
| 2,024.00 |  324,941,413.63 | 31,061.00 |            97.77 |
| 2,025.00 |  367,924,999.78 | 36,459.00 |            13.23 |

**Revenue by region:**

| region   |   gross_revenue |   orders |   customers |   pct_of_total |
|:---------|----------------:|---------:|------------:|---------------:|
| North    |  289,678,811.39 |    27996 |        8736 |          33.79 |
| East     |  180,647,263.68 |    17667 |        6432 |          21.07 |
| Central  |  153,314,892.37 |    14808 |        4978 |          17.89 |
| South    |  117,583,767.87 |    11195 |        4800 |          13.72 |
| West     |  115,944,204.39 |    11134 |        4394 |          13.53 |

**Revenue by region, year over year (this is where the South-region decline shows up numerically):**

| region   |          2023 |           2024 |           2025 |   2023_yoy_growth_pct |   2024_yoy_growth_pct |   2025_yoy_growth_pct |
|:---------|--------------:|---------------:|---------------:|----------------------:|----------------------:|----------------------:|
| Central  | 27,356,408.61 |  56,842,261.06 |  69,116,222.70 |                   nan |                107.78 |                 21.59 |
| East     | 34,166,270.56 |  67,869,645.93 |  78,611,347.19 |                   nan |                 98.65 |                 15.83 |
| North    | 46,883,246.86 | 104,991,957.79 | 137,803,606.74 |                   nan |                123.94 |                 31.25 |
| South    | 30,501,175.66 |  49,675,838.08 |  37,406,754.13 |                   nan |                 62.87 |                -24.70 |
| West     | 25,395,424.60 |  45,561,710.77 |  44,987,069.02 |                   nan |                 79.41 |                 -1.26 |

**Revenue by product category:**

| category                |        revenue |   units |   order_items |   pct_of_total |
|:------------------------|---------------:|--------:|--------------:|---------------:|
| Home Goods              | 255,172,275.11 |   95803 |         48007 |          29.77 |
| Apparel                 | 191,526,621.41 |  110516 |         55211 |          22.34 |
| Electronics Accessories | 184,398,021.59 |   82584 |         41210 |          21.51 |
| Footwear                | 158,053,123.34 |   55614 |         27654 |          18.44 |
| Personal Care           |  68,018,898.25 |   68578 |         34415 |           7.94 |

**Revenue by customer segment:**

| customer_segment   |   gross_revenue |   orders |   customers |   pct_of_total |
|:-------------------|----------------:|---------:|------------:|---------------:|
| Churned            |  438,776,306.62 |    41847 |       17030 |          51.19 |
| At-Risk            |  170,304,920.67 |    16668 |        5210 |          19.87 |
| Loyal              |  132,766,378.38 |    12865 |        1833 |          15.49 |
| Regular            |   97,212,864.00 |     9570 |        3417 |          11.34 |
| New                |   18,108,470.03 |     1850 |        1850 |           2.11 |

## 2. Profitability KPIs

- **Gross revenue:** ₹857,168,939.70
- **Net revenue:** ₹803,075,998.49
- **Cogs:** ₹588,059,205.99
- **Gross profit:** ₹269,109,733.71
- **Gross margin pct:** 31.4%
- **Total variable cost:** ₹81,594,697.49
- **Contribution margin:** ₹133,422,095.01
- **Contribution margin pct:** 16.61%
- **Cost per order:** ₹985.44
- **Total discount given:** ₹106,043,181.82
- **Discount impact pct:** 11.01%
- **Total returned amount:** ₹54,092,941.21
- **Return impact pct:** 6.31%

**Gross margin trend by year (margin compression visible here):**

|     year |   gross_revenue |           cogs |   gross_profit |   gross_margin_pct |   discount_rate_pct |   return_rate_pct |
|---------:|----------------:|---------------:|---------------:|-------------------:|--------------------:|------------------:|
| 2,023.00 |  164,302,526.29 | 107,965,300.76 |  56,337,225.53 |              34.29 |                7.04 |              5.22 |
| 2,024.00 |  324,941,413.63 | 220,592,649.00 | 104,348,764.63 |              32.11 |               10.09 |              5.88 |
| 2,025.00 |  367,924,999.78 | 259,501,256.23 | 108,423,743.55 |              29.47 |               13.44 |              7.18 |

**Profitability by region (weakest margin first):**

| region   |   gross_revenue |           cogs |   total_variable_cost |   gross_profit |   gross_margin_pct |
|:---------|----------------:|---------------:|----------------------:|---------------:|-------------------:|
| North    |  289,678,811.39 | 199,401,350.71 |         27,299,985.28 |  90,277,460.68 |              31.16 |
| Central  |  153,314,892.37 | 105,231,600.27 |         14,433,516.53 |  48,083,292.10 |              31.36 |
| East     |  180,647,263.68 | 123,900,350.51 |         17,243,501.14 |  56,746,913.17 |              31.41 |
| West     |  115,944,204.39 |  79,378,850.46 |         11,283,307.86 |  36,565,353.93 |              31.54 |
| South    |  117,583,767.87 |  80,147,054.04 |         11,334,386.68 |  37,436,713.83 |              31.84 |

## 3. Customer KPIs

- **Total customers:** 45,000
- **Customers with purchase:** 29,340
- **Conversion rate pct:** 65.2%
- **Never purchased:** 15,660
- **Repeat customers:** 19,380
- **Repeat purchase rate pct:** 66.05%
- **Churned customers:** 17,030
- **Churn rate pct:** 58.04%
- **At risk customers:** 5,210
- **At risk rate pct:** 17.76%
- **Avg customer lifetime value:** ₹27,371.37
- **Avg orders per active customer:** 2.82

**Customer segment summary:**

| customer_segment   |   customers |   total_revenue |   avg_clv |   avg_orders |   avg_return_rate |   pct_of_customers |
|:-------------------|------------:|----------------:|----------:|-------------:|------------------:|-------------------:|
| Churned            |       17030 |  438,776,306.62 | 24,226.44 |         2.46 |              0.14 |              37.84 |
| At-Risk            |        5210 |  170,304,920.67 | 30,523.82 |         3.20 |              0.16 |              11.58 |
| Loyal              |        1833 |  132,766,378.38 | 67,803.99 |         7.02 |              0.15 |               4.07 |
| Regular            |        3417 |   97,212,864.00 | 26,435.06 |         2.80 |              0.17 |               7.59 |
| New                |        1850 |   18,108,470.03 |  9,112.10 |         1.00 |              0.16 |               4.11 |
| Never Purchased    |       15660 |            0.00 |      0.00 |         0.00 |              0.00 |              34.80 |

- **Revenue sitting with At-Risk + Churned customers:** ₹571,605,313.52 (71.18% of total active-customer CLV, across 22,240 customers)

**Month-over-month retention curve (first 6 and last 6 months):**

| month   |   active_customers |   retained_next_month |   retention_rate_pct |
|:--------|-------------------:|----------------------:|---------------------:|
| 2023-01 |                223 |                    41 |                18.39 |
| 2023-02 |                424 |                    74 |                17.45 |
| 2023-03 |                569 |                    83 |                14.59 |
| 2023-04 |                745 |                   106 |                14.23 |
| 2023-05 |                949 |                   165 |                17.39 |
| 2023-06 |               1111 |                   173 |                15.57 |
| 2025-06 |               2669 |                   336 |                12.59 |
| 2025-07 |               2767 |                   363 |                13.12 |
| 2025-08 |               2594 |                   310 |                11.95 |
| 2025-09 |               2625 |                   302 |                11.50 |
| 2025-10 |               2677 |                   314 |                11.73 |
| 2025-11 |               2597 |                   311 |                11.98 |

## 4. Product KPIs

**Top 10 products by revenue:**

|   product_id | product_name         | category   |       revenue |   units_sold |   orders |         cogs |       profit |   margin_pct |
|-------------:|:---------------------|:-----------|--------------:|-------------:|---------:|-------------:|-------------:|-------------:|
|           60 | Classic Rug          | Home Goods | 14,636,645.93 |         2760 |     1351 | 8,576,203.20 | 6,060,442.73 |        41.41 |
|           68 | Essential Cushion    | Home Goods | 14,007,126.23 |         2695 |     1354 | 9,439,992.10 | 4,567,134.13 |        32.61 |
|           61 | Premium Cookware Set | Home Goods | 12,933,828.04 |         2707 |     1372 | 7,588,695.52 | 5,345,132.52 |        41.33 |
|           72 | Classic Rug          | Home Goods | 12,196,870.61 |         2806 |     1374 | 7,631,534.32 | 4,565,336.29 |        37.43 |
|           47 | Everyday Organizer   | Home Goods | 11,986,310.33 |         2831 |     1417 | 9,213,008.23 | 2,773,302.10 |        23.14 |
|          136 | Lite Running Shoe    | Footwear   | 11,971,354.41 |         2732 |     1347 | 8,667,297.32 | 3,304,057.09 |        27.60 |
|           51 | Comfort Cushion      | Home Goods | 11,694,373.89 |         2625 |     1310 | 6,848,546.25 | 4,845,827.64 |        41.44 |
|          144 | Premium Loafer       | Footwear   | 11,480,764.17 |         2826 |     1382 | 6,635,956.68 | 4,844,807.49 |        42.20 |
|          140 | Classic Running Shoe | Footwear   | 11,306,136.96 |         2859 |     1387 | 8,402,972.67 | 2,903,164.29 |        25.68 |
|           54 | Pro Curtain          | Home Goods | 11,126,966.01 |         2669 |     1339 | 8,476,824.07 | 2,650,141.94 |        23.82 |

**10 lowest-margin products (min ₹10,000 revenue):**

|   product_id | product_name       | category                |       revenue |   units_sold |   orders |         cogs |       profit |   margin_pct |
|-------------:|:-------------------|:------------------------|--------------:|-------------:|---------:|-------------:|-------------:|-------------:|
|           80 | Pro Earbuds        | Electronics Accessories |  8,752,192.01 |         2741 |     1349 | 7,826,651.40 |   925,540.61 |        10.57 |
|           76 | Comfort Cable      | Electronics Accessories | 10,183,124.97 |         2736 |     1361 | 9,093,287.52 | 1,089,837.45 |        10.70 |
|           96 | Classic Power Bank | Electronics Accessories |  5,027,338.50 |         2806 |     1365 | 4,476,720.46 |   550,618.04 |        10.95 |
|           94 | Essential Charger  | Electronics Accessories |  9,542,244.74 |         2771 |     1386 | 8,479,869.62 | 1,062,375.12 |        11.13 |
|           97 | Classic Stand      | Electronics Accessories |  6,230,595.49 |         2830 |     1405 | 5,463,060.30 |   767,535.19 |        12.32 |
|           77 | Lite Earbuds       | Electronics Accessories |  7,573,587.52 |         2892 |     1407 | 6,631,789.80 |   941,797.72 |        12.44 |
|           90 | Comfort Earbuds    | Electronics Accessories |  2,227,900.52 |         2771 |     1345 | 1,943,662.53 |   284,237.99 |        12.76 |
|          101 | Signature Cable    | Electronics Accessories |  8,666,550.15 |         2738 |     1370 | 7,537,056.88 | 1,129,493.27 |        13.03 |
|           89 | Premium Charger    | Electronics Accessories | 10,170,114.46 |         2748 |     1364 | 8,775,573.12 | 1,394,541.34 |        13.71 |
|           91 | Signature Earbuds  | Electronics Accessories |  1,183,660.01 |         2742 |     1385 | 1,018,351.38 |   165,308.63 |        13.97 |

**Top 10 highest-growth products (latest YoY):**

|   product_id | product_name        | category                |   latest_yoy_growth_pct |      revenue |
|-------------:|:--------------------|:------------------------|------------------------:|-------------:|
|           67 | Active Rug          | Home Goods              |                   34.29 | 3,560,626.85 |
|           86 | Active Earbuds      | Electronics Accessories |                   31.41 | 8,056,323.47 |
|          115 | Essential Serum     | Personal Care           |                   28.62 | 3,446,491.89 |
|           93 | Lite Stand          | Electronics Accessories |                   27.14 | 3,863,657.14 |
|           30 | Active Trousers     | Apparel                 |                   26.95 | 4,513,877.56 |
|           12 | Lite Hoodie         | Apparel                 |                   26.21 | 3,843,412.63 |
|           46 | Essential Organizer | Home Goods              |                   25.58 | 1,018,863.29 |
|          124 | Pro Shampoo         | Personal Care           |                   24.86 | 3,847,834.91 |
|           37 | Premium Jacket      | Apparel                 |                   24.76 | 1,713,580.12 |
|           87 | Urban Earbuds       | Electronics Accessories |                   24.38 | 1,342,028.93 |

**10 most-declining products (latest YoY):**

|   product_id | product_name       | category                |   latest_yoy_growth_pct |      revenue |
|-------------:|:-------------------|:------------------------|------------------------:|-------------:|
|           83 | Premium Power Bank | Electronics Accessories |                   -5.37 | 7,031,500.80 |
|           56 | Essential Rug      | Home Goods              |                   -2.18 | 5,990,814.34 |
|           95 | Pro Cable          | Electronics Accessories |                   -2.07 | 3,108,794.64 |
|          139 | Essential Sneaker  | Footwear                |                   -1.84 | 2,449,330.05 |
|           64 | Active Lamp        | Home Goods              |                    1.39 | 4,306,057.40 |
|          118 | Classic Kit        | Personal Care           |                    1.87 | 1,011,503.51 |
|           15 | Lite Shirt         | Apparel                 |                    2.07 | 6,344,671.48 |
|            6 | Signature Tee      | Apparel                 |                    2.11 | 2,615,591.26 |
|          116 | Classic Shampoo    | Personal Care           |                    2.34 | 3,579,763.49 |
|           94 | Essential Charger  | Electronics Accessories |                    2.37 | 9,542,244.74 |

**Category performance:**

| category                |        revenue |   units_sold |        profit |   margin_pct |
|:------------------------|---------------:|-------------:|--------------:|-------------:|
| Home Goods              | 255,172,275.11 |        95803 | 82,956,651.23 |        32.51 |
| Apparel                 | 191,526,621.41 |       110516 | 73,038,321.95 |        38.13 |
| Electronics Accessories | 184,398,021.59 |        82584 | 36,836,214.83 |        19.98 |
| Footwear                | 158,053,123.34 |        55614 | 46,658,365.99 |        29.52 |
| Personal Care           |  68,018,898.25 |        68578 | 29,620,179.71 |        43.55 |

## 5. Marketing KPIs

- **Total campaigns:** 75
- **Total marketing spend:** ₹18,743,994.19
- **Total customers targeted:** 638,158
- **Total customers converted:** 22,534
- **Overall conversion rate pct:** 3.53%
- **Total customers acquired via campaigns:** 20,634
- **Blended cac:** ₹908.40
- **Revenue from campaign acquired customers:** ₹386,787,722.31
- **Overall roi pct:** 1963.53%

**Campaign type performance (ROI ranked):**

| campaign_type   |   campaigns |   total_spend |   total_customers_acquired |   total_revenue_from_acquired |   avg_conversion_rate_pct |   blended_cac |   roi_pct |
|:----------------|------------:|--------------:|---------------------------:|------------------------------:|--------------------------:|--------------:|----------:|
| Influencer      |          16 |  3,808,986.82 |                       5068 |                102,421,716.94 |                      4.12 |        751.58 |  2,588.95 |
| Email           |          15 |  3,689,566.45 |                       4708 |                 85,818,395.59 |                      3.06 |        783.68 |  2,225.98 |
| Social Media    |          13 |  2,929,627.80 |                       3145 |                 57,876,137.50 |                      3.26 |        931.52 |  1,875.55 |
| In-Store Promo  |          20 |  5,219,020.08 |                       4999 |                 91,654,358.81 |                      3.38 |      1,044.01 |  1,656.16 |
| Search Ads      |          11 |  3,096,793.04 |                       2714 |                 49,017,113.47 |                      3.57 |      1,141.04 |  1,482.83 |

**Top 10 individual campaigns by ROI:**

|   campaign_id | campaign_type   | campaign_date       |      spend |   customers_acquired |    cac |   revenue_from_acquired |   roi_pct |
|--------------:|:----------------|:--------------------|-----------:|---------------------:|-------:|------------------------:|----------:|
|             6 | Influencer      | 2023-05-08 00:00:00 |  96,933.11 |                  340 | 285.10 |           10,036,134.37 | 10,253.67 |
|             4 | In-Store Promo  | 2023-03-16 00:00:00 | 155,469.92 |                  547 | 284.22 |           14,948,693.38 |  9,515.17 |
|            43 | Email           | 2024-10-21 00:00:00 |  64,331.44 |                  304 | 211.62 |            4,715,707.56 |  7,230.33 |
|            30 | Social Media    | 2024-04-10 00:00:00 |  70,337.97 |                  264 | 266.43 |            5,019,510.28 |  7,036.27 |
|            26 | Influencer      | 2024-03-25 00:00:00 | 113,324.33 |                  318 | 356.37 |            7,601,402.65 |  6,607.65 |
|            12 | Influencer      | 2023-07-12 00:00:00 | 242,200.53 |                  565 | 428.67 |           14,865,092.25 |  6,037.51 |
|             1 | Email           | 2023-01-20 00:00:00 | 359,451.00 |                  647 | 555.57 |           19,445,887.28 |  5,309.89 |
|            27 | Email           | 2024-03-08 00:00:00 | 131,498.30 |                  307 | 428.33 |            6,119,802.58 |  4,553.90 |
|             5 | Influencer      | 2023-04-05 00:00:00 | 379,208.04 |                  665 | 570.24 |           17,450,100.57 |  4,501.72 |
|            17 | Search Ads      | 2023-11-21 00:00:00 | 159,862.68 |                  283 | 564.89 |            7,266,271.34 |  4,445.32 |

**Bottom 10 individual campaigns by ROI:**

|   campaign_id | campaign_type   | campaign_date       |      spend |   customers_acquired |      cac |   revenue_from_acquired |   roi_pct |
|--------------:|:----------------|:--------------------|-----------:|---------------------:|---------:|------------------------:|----------:|
|            72 | Email           | 2025-11-09 00:00:00 | 122,457.19 |                  184 |   665.53 |              641,233.89 |    423.64 |
|            69 | Email           | 2025-09-03 00:00:00 | 385,921.08 |                  350 | 1,102.63 |            1,920,319.55 |    397.59 |
|            48 | Social Media    | 2024-12-22 00:00:00 | 308,801.01 |                  115 | 2,685.23 |            1,434,011.13 |    364.38 |
|            64 | In-Store Promo  | 2025-06-08 00:00:00 | 356,010.03 |                  195 | 1,825.69 |            1,479,121.60 |    315.47 |
|            66 | In-Store Promo  | 2025-08-22 00:00:00 | 365,893.89 |                  180 | 2,032.74 |            1,288,154.74 |    252.06 |
|            73 | In-Store Promo  | 2025-11-01 00:00:00 | 195,813.37 |                  187 | 1,047.13 |              620,839.40 |    217.06 |
|            71 | Influencer      | 2025-11-02 00:00:00 | 184,576.53 |                  173 | 1,066.92 |              579,984.99 |    214.22 |
|            68 | Search Ads      | 2025-08-14 00:00:00 | 384,372.30 |                  173 | 2,221.81 |            1,052,248.49 |    173.76 |
|            74 | Email           | 2025-12-14 00:00:00 | 227,858.57 |                  238 |   957.39 |              366,427.43 |     60.81 |
|            75 | Influencer      | 2025-12-22 00:00:00 | 200,964.46 |                   62 | 3,241.36 |              117,872.35 |    -41.35 |

## Outputs written

All under `data/processed/`: `customer_features.csv`, `kpi_customer_segment_summary.csv`, `kpi_revenue_by_month.csv`, `kpi_revenue_by_region.csv`, `kpi_revenue_by_region_trend.csv`, `kpi_revenue_by_category.csv`, `kpi_revenue_by_segment.csv`, `kpi_margin_trend_yoy.csv`, `kpi_profitability_by_region.csv`, `kpi_monthly_retention.csv`, `kpi_category_performance.csv`, `kpi_campaign_performance.csv`, `kpi_campaign_type_summary.csv`.
