"""
MarketLens - Phase 03: Internal Dataset Generation
====================================================
Generates a realistic, internally-consistent synthetic dataset for the
fictional company UrbanCart Retail Group (see research/business_case.md).

This script plays the role of "the raw export from UrbanCart's operational
systems" (POS + e-commerce + CRM + marketing). Downstream phases treat its
output (data/raw/*.csv) as the raw source, exactly as they would treat a
real company data export.

Design goals (so later analysis has something real to find):
  - Overall revenue growth decelerates over the 3-year window (not a
    uniform straight-line company).
  - Two regions (South, West) underperform the company average, with South
    turning into outright decline - this is the "hidden" regional problem.
  - Discounting intensity increases over time -> contributes to margin
    compression.
  - Return rates increase over time, particularly in Electronics
    Accessories -> further margin pressure.
  - Customer retention (repeat purchase behavior) weakens for later
    cohorts, and weakens fastest in the underperforming regions -> produces
    a real, discoverable "repeat purchases falling" signal.

No metric is hardcoded anywhere else in the project - every KPI in later
phases is computed from this data, not asserted.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)  # fixed seed -> reproducible dataset

OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_MONTHS = 36
START_DATE = pd.Timestamp("2023-01-01")
MONTHS = pd.date_range(START_DATE, periods=N_MONTHS, freq="MS")

N_CUSTOMERS = 45_000

# ---------------------------------------------------------------------------
# 1. REGIONS
# ---------------------------------------------------------------------------
REGION_NAMES = ["North", "South", "East", "West", "Central"]
regions = pd.DataFrame({
    "region_id": range(1, len(REGION_NAMES) + 1),
    "region_name": REGION_NAMES,
})

# Monthly performance index per region (index 1.0 = month-0 baseline).
# This is the ground truth the whole diagnosis (Phase 13) will later
# "discover" from the generated transactions - not asserted anywhere else.
REGION_TRAJECTORY = {
    "North":   lambda m: 1.00 + 0.014 * m,                       # steady grower
    "Central": lambda m: 1.00 + 0.009 * m,                       # moderate grower
    "East":    lambda m: 1.00 + 0.004 * m,                       # roughly stable
    "West":    lambda m: 1.00 + 0.006 * min(m, 14) - 0.010 * max(0, m - 14),   # flattens then declines
    "South":   lambda m: 1.00 + 0.010 * min(m, 10) - 0.022 * max(0, m - 10),   # grows early, then falls hard
}

# ---------------------------------------------------------------------------
# 2. STORES
# ---------------------------------------------------------------------------
stores_per_region = {"North": 4, "South": 3, "East": 4, "West": 3, "Central": 4}
store_rows = []
store_id = 1
for region_name, n_stores in stores_per_region.items():
    region_id = regions.loc[regions.region_name == region_name, "region_id"].iloc[0]
    for i in range(1, n_stores + 1):
        store_rows.append({
            "store_id": store_id,
            "store_name": f"UrbanCart {region_name} #{i}",
            "region_id": region_id,
        })
        store_id += 1
stores = pd.DataFrame(store_rows)

# ---------------------------------------------------------------------------
# 3. PRODUCTS
# ---------------------------------------------------------------------------
CATEGORY_INFO = {
    # category: (n_products, price_range, margin_range)
    "Apparel":                 (40, (400, 3500), (0.35, 0.55)),
    "Home Goods":              (35, (300, 6000), (0.30, 0.50)),
    "Electronics Accessories": (30, (250, 4500), (0.20, 0.40)),
    "Personal Care":           (25, (150, 1800), (0.40, 0.60)),
    "Footwear":                (20, (800, 5500), (0.30, 0.50)),
}
ADJECTIVES = ["Classic", "Premium", "Everyday", "Urban", "Essential", "Comfort",
              "Pro", "Lite", "Signature", "Active"]
NOUNS = {
    "Apparel": ["Tee", "Hoodie", "Jacket", "Trousers", "Shirt", "Dress"],
    "Home Goods": ["Cushion", "Lamp", "Organizer", "Cookware Set", "Rug", "Curtain"],
    "Electronics Accessories": ["Earbuds", "Charger", "Power Bank", "Cable", "Speaker", "Stand"],
    "Personal Care": ["Lotion", "Shampoo", "Trimmer", "Kit", "Serum", "Kit Refill"],
    "Footwear": ["Sneaker", "Sandal", "Boot", "Loafer", "Running Shoe"],
}

product_rows = []
pid = 1
for category, (n_products, price_range, margin_range) in CATEGORY_INFO.items():
    for _ in range(n_products):
        selling_price = round(RNG.uniform(*price_range), 2)
        margin = RNG.uniform(*margin_range)
        cost = round(selling_price * (1 - margin), 2)
        name = f"{RNG.choice(ADJECTIVES)} {RNG.choice(NOUNS[category])}"
        product_rows.append({
            "product_id": pid,
            "product_name": name,
            "category": category,
            "cost": cost,
            "selling_price": selling_price,
        })
        pid += 1
products = pd.DataFrame(product_rows)

# Category-level return-rate drift (Electronics Accessories worsens most,
# consistent with the margin-pressure narrative).
CATEGORY_RETURN_BASE = {
    "Apparel": 0.05, "Home Goods": 0.04, "Electronics Accessories": 0.05,
    "Personal Care": 0.02, "Footwear": 0.06,
}
CATEGORY_RETURN_DRIFT = {  # additional return-rate added by month 35
    "Apparel": 0.02, "Home Goods": 0.015, "Electronics Accessories": 0.06,
    "Personal Care": 0.01, "Footwear": 0.02,
}

# ---------------------------------------------------------------------------
# 4. MARKETING CAMPAIGNS
# ---------------------------------------------------------------------------
CAMPAIGN_TYPES = ["Email", "Social Media", "Search Ads", "Influencer", "In-Store Promo"]
campaign_rows = []
cid = 1
for m_idx, month in enumerate(MONTHS):
    n_campaigns = RNG.integers(1, 4)
    chosen_types = RNG.choice(CAMPAIGN_TYPES, size=n_campaigns, replace=False)
    for ctype in chosen_types:
        spend = round(RNG.uniform(50_000, 400_000), 2)
        targeted = int(RNG.integers(2_000, 15_000))
        # conversion rate has mild time-decay (marketing getting less efficient
        # -> consistent with "is marketing spend helping or masking the problem")
        base_conv_rate = RNG.uniform(0.02, 0.07)
        time_decay = 1 - 0.35 * (m_idx / (N_MONTHS - 1))
        conv_rate = max(0.005, base_conv_rate * time_decay)
        converted = int(targeted * conv_rate)
        campaign_rows.append({
            "campaign_id": cid,
            "campaign_date": month + pd.Timedelta(days=int(RNG.integers(0, 27))),
            "campaign_type": ctype,
            "spend": spend,
            "customers_targeted": targeted,
            "customers_converted": converted,
        })
        cid += 1
campaigns = pd.DataFrame(campaign_rows).sort_values("campaign_date").reset_index(drop=True)

# ---------------------------------------------------------------------------
# 5. CUSTOMERS
# ---------------------------------------------------------------------------
# New-signup volume front-loaded (deceleration of acquisition over time),
# and split across regions with fixed weights.
signup_weight_by_month = np.array([
    1.0 + 0.5 * np.exp(-m / 10) - 0.15 * (m / (N_MONTHS - 1)) for m in range(N_MONTHS)
])
signup_weight_by_month = np.clip(signup_weight_by_month, 0.15, None)
signup_month_probs = signup_weight_by_month / signup_weight_by_month.sum()
signup_month_idx = RNG.choice(N_MONTHS, size=N_CUSTOMERS, p=signup_month_probs)

REGION_SIGNUP_WEIGHTS = {"North": 0.27, "South": 0.20, "East": 0.21, "West": 0.16, "Central": 0.16}
region_choices = RNG.choice(
    list(REGION_SIGNUP_WEIGHTS.keys()), size=N_CUSTOMERS,
    p=list(REGION_SIGNUP_WEIGHTS.values())
)

FIRST_NAMES = ["Aarav", "Vivaan", "Ishaan", "Ananya", "Diya", "Kabir", "Meera", "Rohan",
               "Sara", "Aditi", "Karan", "Priya", "Neha", "Arjun", "Riya", "Dev",
               "Tara", "Yash", "Anika", "Zoya", "Nikhil", "Pooja", "Rahul", "Simran"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Nair", "Reddy", "Gupta", "Khan", "Das",
              "Mehta", "Rao", "Chatterjee", "Pillai", "Joshi", "Kapoor", "Menon"]

customer_ids = np.arange(1, N_CUSTOMERS + 1)
signup_dates = MONTHS[signup_month_idx] + pd.to_timedelta(RNG.integers(0, 27, size=N_CUSTOMERS), unit="D")

# Per-customer latent purchase propensity (drives how often they buy at all)
purchase_propensity = RNG.gamma(shape=2.0, scale=0.06, size=N_CUSTOMERS)  # mean ~0.12/month baseline

# Per-customer churn hazard multiplier - later cohorts and South/West cohorts
# churn faster, which is exactly the "repeat purchases falling" signal.
region_churn_multiplier = {"North": 0.85, "Central": 0.95, "East": 1.0, "West": 1.15, "South": 1.35}
cohort_churn_multiplier = 1 + 0.5 * (signup_month_idx / (N_MONTHS - 1))  # later cohorts churn faster
churn_hazard = np.array([region_churn_multiplier[r] for r in region_choices]) * cohort_churn_multiplier

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "customer_name": [f"{RNG.choice(FIRST_NAMES)} {RNG.choice(LAST_NAMES)}" for _ in range(N_CUSTOMERS)],
    "signup_date": signup_dates,
    "region": region_choices,
    "_signup_month_idx": signup_month_idx,          # helper column, dropped before saving raw
    "_purchase_propensity": purchase_propensity,     # helper column, dropped before saving raw
    "_churn_hazard": churn_hazard,                   # helper column, dropped before saving raw
})

# Attribute a customer's acquisition to a campaign if they signed up within
# 21 days after a campaign in a plausible type-mix; else organic (NaN).
campaign_lookup = campaigns.sort_values("campaign_date").reset_index(drop=True)
acquisition_campaign_id = np.full(N_CUSTOMERS, np.nan)
for i in range(N_CUSTOMERS):
    sd = customers.at[i, "signup_date"]
    window = campaign_lookup[(campaign_lookup.campaign_date <= sd) &
                              (campaign_lookup.campaign_date >= sd - pd.Timedelta(days=21))]
    if len(window) > 0 and RNG.random() < 0.55:  # 55% of signups are campaign-attributable
        acquisition_campaign_id[i] = int(window.sample(1, random_state=int(RNG.integers(0, 1e6))).campaign_id.iloc[0])
customers["acquisition_campaign_id"] = acquisition_campaign_id

print(f"[1/6] Base entities generated: {len(regions)} regions, {len(stores)} stores, "
      f"{len(products)} products, {len(campaigns)} campaigns, {len(customers)} customers")

# ---------------------------------------------------------------------------
# 6. ORDERS (header rows) — month-by-month simulation
# ---------------------------------------------------------------------------
stores_by_region = {
    rname: stores.loc[stores.region_id == regions.loc[regions.region_name == rname, "region_id"].iloc[0],
                       "store_id"].values
    for rname in REGION_NAMES
}
ONLINE_SHARE_BY_REGION = {"North": 0.55, "South": 0.60, "East": 0.58, "West": 0.62, "Central": 0.56}

order_cust_ids, order_dates, order_channels, order_store_ids, order_month_idx = [], [], [], [], []

for m_idx, month in enumerate(MONTHS):
    active_mask = customers["_signup_month_idx"].values <= m_idx
    active_idx = np.where(active_mask)[0]
    if len(active_idx) == 0:
        continue

    tenure = m_idx - customers["_signup_month_idx"].values[active_idx]
    region_arr = customers["region"].values[active_idx]
    region_idx_val = np.array([REGION_TRAJECTORY[r](m_idx) for r in region_arr])
    churn_haz = customers["_churn_hazard"].values[active_idx]
    retention_decay = np.exp(-churn_haz * tenure / 24)
    propensity = customers["_purchase_propensity"].values[active_idx]

    prob = np.clip(propensity * region_idx_val * retention_decay, 0, 0.9)
    buys = RNG.random(len(active_idx)) < prob
    buyer_idx = active_idx[buys]
    if len(buyer_idx) == 0:
        continue

    n_orders_this_month = 1 + RNG.poisson(0.15, size=len(buyer_idx))
    cust_ids_repeated = np.repeat(customers["customer_id"].values[buyer_idx], n_orders_this_month)
    region_repeated = np.repeat(customers["region"].values[buyer_idx], n_orders_this_month)
    n_total = len(cust_ids_repeated)

    day_offsets = RNG.integers(0, 27, size=n_total)
    dates = month + pd.to_timedelta(day_offsets, unit="D")

    online_share = np.array([ONLINE_SHARE_BY_REGION[r] for r in region_repeated])
    is_online = RNG.random(n_total) < online_share
    channels = np.where(is_online, "online", "in-store")

    store_ids = np.full(n_total, np.nan)
    instore_positions = np.where(~is_online)[0]
    for pos in instore_positions:
        r = region_repeated[pos]
        store_ids[pos] = RNG.choice(stores_by_region[r])

    order_cust_ids.append(cust_ids_repeated)
    order_dates.append(dates.values)
    order_channels.append(channels)
    order_store_ids.append(store_ids)
    order_month_idx.append(np.full(n_total, m_idx))

orders = pd.DataFrame({
    "customer_id": np.concatenate(order_cust_ids),
    "order_date": np.concatenate(order_dates),
    "channel": np.concatenate(order_channels),
    "store_id": np.concatenate(order_store_ids),
    "_month_idx": np.concatenate(order_month_idx),
}).sort_values("order_date").reset_index(drop=True)
orders.insert(0, "order_id", range(1, len(orders) + 1))

print(f"[2/6] Orders generated: {len(orders):,} orders "
      f"({(orders.channel == 'online').mean():.0%} online)")

# ---------------------------------------------------------------------------
# 7. ORDER ITEMS
# ---------------------------------------------------------------------------
n_orders_total = len(orders)
n_items_per_order = RNG.integers(1, 5, size=n_orders_total)  # 1-4 items
total_items = int(n_items_per_order.sum())

order_id_rep = np.repeat(orders["order_id"].values, n_items_per_order)
month_idx_rep = np.repeat(orders["_month_idx"].values, n_items_per_order)

product_id_choice = RNG.choice(products["product_id"].values, size=total_items)
prod_lookup = products.set_index("product_id")
unit_price = prod_lookup.loc[product_id_choice, "selling_price"].values
category_rep = prod_lookup.loc[product_id_choice, "category"].values

quantity = RNG.integers(1, 4, size=total_items)  # 1-3 units

discount_mean = 0.05 + 0.10 * (month_idx_rep / (N_MONTHS - 1))  # 5% -> 15% drift
discount_rate = np.clip(RNG.normal(loc=discount_mean, scale=0.03, size=total_items), 0, 0.5)
gross_amount = quantity * unit_price
discount_amount = np.round(gross_amount * discount_rate, 2)
revenue = np.round(gross_amount - discount_amount, 2)

order_items = pd.DataFrame({
    "order_item_id": range(1, total_items + 1),
    "order_id": order_id_rep,
    "product_id": product_id_choice,
    "quantity": quantity,
    "unit_price": unit_price,
    "discount": discount_amount,
    "revenue": revenue,
})

print(f"[3/6] Order items generated: {len(order_items):,} line items "
      f"(avg {len(order_items) / n_orders_total:.2f} items/order)")

# ---------------------------------------------------------------------------
# 8. RETURNS
# ---------------------------------------------------------------------------
return_base = np.array([CATEGORY_RETURN_BASE[c] for c in category_rep])
return_drift = np.array([CATEGORY_RETURN_DRIFT[c] for c in category_rep])
return_prob = return_base + return_drift * (month_idx_rep / (N_MONTHS - 1))
is_returned = RNG.random(total_items) < return_prob

RETURN_REASONS = ["Wrong size", "Defective item", "Not as described",
                   "Changed mind", "Better price found elsewhere", "Late delivery"]

returned_items_idx = np.where(is_returned)[0]
order_id_for_returns = order_items["order_id"].values[returned_items_idx]
order_date_lookup = orders.set_index("order_id")["order_date"]
return_dates = order_date_lookup.loc[order_id_for_returns].values + \
    pd.to_timedelta(RNG.integers(2, 21, size=len(returned_items_idx)), unit="D").values

returns = pd.DataFrame({
    "return_id": range(1, len(returned_items_idx) + 1),
    "order_id": order_id_for_returns,
    "return_date": return_dates,
    "return_reason": RNG.choice(RETURN_REASONS, size=len(returned_items_idx)),
    "return_amount": order_items["revenue"].values[returned_items_idx],
})

print(f"[4/6] Returns generated: {len(returns):,} returned line items "
      f"({len(returns) / total_items:.1%} of items)")

# ---------------------------------------------------------------------------
# 9. COSTS (per order)
# ---------------------------------------------------------------------------
order_revenue = order_items.groupby("order_id")["revenue"].sum().reindex(orders["order_id"]).values
region_for_order = orders["customer_id"].map(customers.set_index("customer_id")["region"]).values
REGION_SHIPPING_BASE = {"North": 40, "South": 55, "East": 45, "West": 60, "Central": 35}
shipping_base = np.array([REGION_SHIPPING_BASE[r] for r in region_for_order])
is_online_order = (orders["channel"].values == "online")
shipping_cost = np.where(
    is_online_order,
    np.round(shipping_base + 0.02 * order_revenue + RNG.normal(0, 5, len(orders)), 2),
    np.round(RNG.normal(10, 3, len(orders)), 2),  # small in-store handling cost only
)
shipping_cost = np.clip(shipping_cost, 5, None)
operational_cost = np.round(order_revenue * RNG.uniform(0.06, 0.10, len(orders)) + 8, 2)

costs = pd.DataFrame({
    "order_id": orders["order_id"].values,
    "shipping_cost": shipping_cost,
    "operational_cost": operational_cost,
})

print(f"[5/6] Costs generated for {len(costs):,} orders")

# ---------------------------------------------------------------------------
# 10. SAVE RAW CSVs (competitors handled separately in Phase 10 - research)
# ---------------------------------------------------------------------------
customers_raw = customers.drop(
    columns=["_signup_month_idx", "_purchase_propensity", "_churn_hazard"]
).rename(columns={"region": "region_name"})
orders_raw = orders.drop(columns=["_month_idx"])
orders_raw["store_id"] = orders_raw["store_id"].astype("Int64")  # nullable int for online orders

regions.to_csv(OUT_DIR / "regions.csv", index=False)
stores.to_csv(OUT_DIR / "stores.csv", index=False)
products.to_csv(OUT_DIR / "products.csv", index=False)
customers_raw.to_csv(OUT_DIR / "customers.csv", index=False)
campaigns.to_csv(OUT_DIR / "marketing_campaigns.csv", index=False)
orders_raw.to_csv(OUT_DIR / "orders.csv", index=False)
order_items.to_csv(OUT_DIR / "order_items.csv", index=False)
returns.to_csv(OUT_DIR / "returns.csv", index=False)
costs.to_csv(OUT_DIR / "costs.csv", index=False)

print("[6/6] All raw CSVs written to data/raw/")

# ---------------------------------------------------------------------------
# 11. SANITY / CONSISTENCY CHECKS (fail loudly if the data is broken)
# ---------------------------------------------------------------------------
assert (order_items["discount"] <= order_items["quantity"] * order_items["unit_price"] + 0.01).all(), \
    "Discount exceeds gross amount somewhere"
assert (order_items["revenue"] >= -0.01).all(), "Negative revenue found"
assert order_items["order_id"].isin(orders["order_id"]).all(), "Orphan order_items found"
assert returns["order_id"].isin(orders["order_id"]).all(), "Orphan returns found"
assert (campaigns["customers_converted"] <= campaigns["customers_targeted"]).all(), \
    "A campaign converted more customers than targeted"
assert costs["order_id"].nunique() == len(orders), "Costs do not have exactly one row per order"
valid_regions = set(regions.region_name)
assert customers_raw["region_name"].isin(valid_regions).all(), "Invalid region in customers"

print("\n✅ All consistency checks passed.")
print(f"\nDataset summary:")
print(f"  Regions:              {len(regions)}")
print(f"  Stores:               {len(stores)}")
print(f"  Products:             {len(products)}")
print(f"  Customers:            {len(customers_raw):,}")
print(f"  Marketing campaigns:  {len(campaigns)}")
print(f"  Orders:               {len(orders):,}")
print(f"  Order items:          {len(order_items):,}")
print(f"  Returns:              {len(returns):,}")
print(f"  Cost records:         {len(costs):,}")
print(f"  Total gross revenue:  ₹{order_items['revenue'].sum():,.0f}")
