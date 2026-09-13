# MarketLens — Client Business Case

## The Company: UrbanCart Retail Group

UrbanCart Retail Group is a fictional multi-location retail/e-commerce
company used as the consistent case study throughout MarketLens. All data,
analysis, models, and recommendations in this project refer to UrbanCart.

**Profile**

| Attribute | Detail |
|---|---|
| Industry | Retail & E-commerce (general merchandise: apparel, home goods, electronics accessories, personal care) |
| Business model | Hybrid — physical stores + online storefront, same product catalog |
| Footprint | 5 regions, 18 stores + 1 online channel |
| Customer base | ~45,000 customers accumulated over 3 years |
| Channels | In-store purchases, online orders (delivery), marketing-driven acquisition |
| Reporting currency | INR (₹) |
| History modeled | 3 fiscal years of transactional history |

**Regions**

1. North
2. South
3. East
4. West
5. Central

Each region contains 3–4 physical stores. Online orders are attributed to
the region of the customer's registered address.

**Product categories**

1. Apparel
2. Home Goods
3. Electronics Accessories
4. Personal Care
5. Footwear

**Customer segments**

- New — first purchase within the last 90 days
- Regular — repeat purchaser, active within the last 180 days
- Loyal — 5+ orders, active within the last 180 days
- At-Risk — previously active, no purchase in 180+ days
- Churned — no purchase in 365+ days

## The Business Problem

UrbanCart's leadership has brought in MarketLens (the analytics engagement)
because of four converging symptoms observed over the last several
quarters:

1. **Revenue growth is slowing.** Year-over-year revenue growth has
   decelerated for several consecutive quarters.
2. **Margins are declining.** Gross margin has been compressing, even in
   quarters where revenue held steady.
3. **Repeat purchases are falling.** The share of revenue coming from
   repeat customers (vs. first-time buyers) is trending down, and days
   between purchases are lengthening.
4. **Certain regions are underperforming.** Not all regions are affected
   equally — some regions are flat or growing, while others are declining
   noticeably faster than the company average.

Management does not yet know:

- Whether this is a market-wide slowdown or an UrbanCart-specific problem
- Which regions, products, or customer segments are driving the decline
- Whether discounting and marketing spend are helping or masking the
  problem
- Which customers are at the highest risk of churning, and how much
  revenue that represents
- What concrete actions would have the highest return if taken now

**MarketLens's mandate**: use the company's own transactional data,
statistical analysis, predictive modeling, and external market context to
diagnose the causes of the slowdown, quantify the financial stakes, and
recommend prioritized, costed actions.

## Why This Case Was Chosen

This business problem was deliberately designed so that every phase of the
frozen build order has a genuine purpose:

- Revenue/margin/customer/region symptoms → needs SQL + Python KPI analysis
- "Is this us or the market?" → needs external market/competitor research
- "Which customers will churn?" → needs predictive modeling (ML)
- "What should we do, and what's it worth?" → needs financial modeling,
  scenario analysis, and prioritized recommendations
- "Explain this to a non-technical exec" → needs the AI Business Analyst,
  dashboard, executive report, and client presentation

No part of the data model or analysis was designed backward from a desired
answer — the data will be generated to be internally consistent and
realistic, and the diagnosis will be derived from what the data actually
shows once it exists (Phase 03 onward).
