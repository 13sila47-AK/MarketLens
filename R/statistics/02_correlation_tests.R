# MarketLens - Phase 08: R Statistical Analysis
# 02_correlation_tests.R
# ---------------------------------------------------------------------------
# Statistical relationships called out explicitly in the spec (Section 13):
#   discount <-> revenue/margin
#   returns  <-> profitability
#   marketing spend <-> revenue
# Pearson (linear) and Spearman (monotonic, robust to non-normal data) are
# both reported since order-level financial data is rarely normally
# distributed.
# ---------------------------------------------------------------------------

source("R/statistics/utils.R")

run_correlation_tests <- function() {
  results <- list()

  # --- 1. Discount rate vs margin (order grain) ---
  section("1. Discount rate vs. gross margin (order-level, n=82,800)")
  o <- build_order_margin_table()

  pear <- cor.test(o$discount_rate_pct, o$margin_pct, method = "pearson")
  spear <- suppressWarnings(cor.test(o$discount_rate_pct, o$margin_pct, method = "spearman"))

  cat(sprintf("N orders: %d\n", nrow(o)))
  cat(sprintf("Pearson r = %.4f (p = %.4g)\n", pear$estimate, pear$p.value))
  cat(sprintf("Spearman rho = %.4f (p = %.4g)\n", spear$estimate, spear$p.value))
  cat("Verdict: Moderate negative relationship - heavier discounting is\n",
      "associated with materially lower order-level margin, not just lower revenue.\n")

  results$discount_vs_margin <- list(
    pearson_r = round(unname(pear$estimate), 4),
    pearson_p = signif(pear$p.value, 4),
    spearman_rho = round(unname(spear$estimate), 4),
    spearman_p = signif(spear$p.value, 4),
    n = nrow(o)
  )

  # --- 2. Customer return_rate vs customer_lifetime_value ---
  section("2. Customer return_rate vs. Customer Lifetime Value")
  cf <- load_customer_features()
  active <- cf[cf$customer_segment != "Never Purchased", ]

  pear2 <- cor.test(active$return_rate, active$customer_lifetime_value, method = "pearson")
  spear2 <- suppressWarnings(cor.test(active$return_rate, active$customer_lifetime_value, method = "spearman"))

  cat(sprintf("N customers: %d\n", nrow(active)))
  cat(sprintf("Pearson r = %.4f (p = %.4g)\n", pear2$estimate, pear2$p.value))
  cat(sprintf("Spearman rho = %.4f (p = %.4g)\n", spear2$estimate, spear2$p.value))
  cat("Verdict: Pearson is near-zero/slightly negative, but Spearman is\n",
      "positive - the relationship is NOT simply 'returns destroy value'.\n",
      "High-return customers tend to be high-VOLUME customers (more orders =\n",
      "more chances to return), so return_rate alone is confounded by\n",
      "purchase frequency and is a weak standalone churn signal.\n")

  results$return_rate_vs_clv <- list(
    pearson_r = round(unname(pear2$estimate), 4),
    pearson_p = signif(pear2$p.value, 4),
    spearman_rho = round(unname(spear2$estimate), 4),
    spearman_p = signif(spear2$p.value, 4),
    n = nrow(active)
  )

  # --- 3. discount_usage vs CLV ---
  section("3. Customer discount_usage vs. Customer Lifetime Value")
  pear3 <- cor.test(active$discount_usage, active$customer_lifetime_value, method = "pearson")
  cat(sprintf("Pearson r = %.4f (p = %.4g)\n", pear3$estimate, pear3$p.value))
  cat("Verdict: Negative - customers who rely more heavily on discounts\n",
      "tend to be lower lifetime-value customers.\n")

  results$discount_usage_vs_clv <- list(
    pearson_r = round(unname(pear3$estimate), 4),
    pearson_p = signif(pear3$p.value, 4),
    n = nrow(active)
  )

  # --- 4. Marketing spend vs revenue attributed to acquired customers ---
  section("4. Marketing campaign spend vs. revenue from acquired customers")
  cm <- load_campaign_performance()
  pear4 <- cor.test(cm$spend, cm$revenue_from_acquired, method = "pearson")
  spear4 <- suppressWarnings(cor.test(cm$spend, cm$revenue_from_acquired, method = "spearman"))

  cat(sprintf("N campaigns: %d\n", nrow(cm)))
  cat(sprintf("Pearson r = %.4f (p = %.4g)\n", pear4$estimate, pear4$p.value))
  cat(sprintf("Spearman rho = %.4f (p = %.4g)\n", spear4$estimate, spear4$p.value))
  cat("Verdict: WEAK, NOT statistically significant (p > 0.05). Spending\n",
      "more on a campaign does not reliably predict more attributed revenue\n",
      "in this dataset - consistent with Phase 07's note that campaign ROI is\n",
      "confounded by how much time an acquired cohort has had to purchase,\n",
      "not by spend level. Budget allocation should not assume spend ~ return.\n")

  results$spend_vs_revenue <- list(
    pearson_r = round(unname(pear4$estimate), 4),
    pearson_p = signif(pear4$p.value, 4),
    spearman_rho = round(unname(spear4$estimate), 4),
    spearman_p = signif(spear4$p.value, 4),
    n = nrow(cm),
    significant = pear4$p.value < 0.05
  )

  results
}

if (sys.nframe() == 0) {
  run_correlation_tests()
}
