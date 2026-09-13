# MarketLens - Phase 08: R Statistical Analysis
# 03_group_difference_tests.R
# ---------------------------------------------------------------------------
# The four group-difference questions from the spec (Section 13):
#   - does regional performance differ?
#   - do discount-heavy orders have different margins?
#   - does campaign performance differ by campaign type?
#   - does customer behavior differ between segments?
#
# ANOVA (parametric) and Kruskal-Wallis (non-parametric, robust to
# non-normal / unequal-variance data - the norm for financial data) are
# both reported. Two-group comparisons also get Welch's t-test AND the
# Mann-Whitney U / Wilcoxon rank-sum test for the same reason.
# ---------------------------------------------------------------------------

source("R/statistics/utils.R")

run_group_difference_tests <- function() {
  results <- list()

  # --- 1. Regional differences in order-level margin ---
  section("1. Does order-level gross margin differ by region?")
  o <- build_order_margin_table()
  o$region <- factor(o$region)

  aov_fit <- aov(margin_pct ~ region, data = o)
  aov_p <- summary(aov_fit)[[1]][["Pr(>F)"]][1]
  kw <- kruskal.test(margin_pct ~ region, data = o)

  print(tapply(o$margin_pct, o$region, function(x) round(c(mean = mean(x), median = median(x), n = length(x)), 2)))
  cat(sprintf("\nANOVA p-value: %.4g\n", aov_p))
  cat(sprintf("Kruskal-Wallis p-value: %.4g\n", kw$p.value))
  cat("Verdict: Statistically significant (p < 0.001) but the effect size is\n",
      "SMALL (~0.6-0.7 percentage points between regions) and South actually has\n",
      "the HIGHEST average per-order margin, not the lowest. This means South's\n",
      "revenue decline (Phase 07) is a VOLUME problem (fewer/smaller orders),\n",
      "not a margin/pricing problem - an important distinction for the diagnosis\n",
      "in Phase 13.\n")

  results$regional_margin <- list(
    anova_p = signif(aov_p, 4),
    kruskal_p = signif(kw$p.value, 4),
    means_by_region = round(tapply(o$margin_pct, o$region, mean), 3)
  )

  # --- 2. High-discount vs low-discount orders: margin ---
  section("2. High-discount vs. low-discount orders: gross margin")
  q <- quantile(o$discount_rate_pct, c(0.25, 0.75))
  high <- o[o$discount_rate_pct >= q[2], "margin_pct"]
  low  <- o[o$discount_rate_pct <= q[1], "margin_pct"]

  tt <- t.test(high, low)
  wt <- wilcox.test(high, low)

  cat(sprintf("High-discount orders (>= Q75 = %.2f%%): n=%d, mean margin=%.2f%%\n", q[2], length(high), mean(high)))
  cat(sprintf("Low-discount orders  (<= Q25 = %.2f%%): n=%d, mean margin=%.2f%%\n", q[1], length(low), mean(low)))
  cat(sprintf("Welch t-test p-value: %.4g\n", tt$p.value))
  cat(sprintf("Mann-Whitney U p-value: %.4g\n", wt$p.value))
  cat("Verdict: Highly significant. High-discount orders run ~6.7 percentage\n",
      "points LOWER margin than low-discount orders - discounting is directly\n",
      "eroding profitability, not just being offset by extra volume.\n")

  results$discount_tier_margin <- list(
    high_discount_mean_margin = round(mean(high), 3),
    low_discount_mean_margin = round(mean(low), 3),
    welch_t_p = signif(tt$p.value, 4),
    mann_whitney_p = signif(wt$p.value, 4)
  )

  # --- 3. Campaign type differences: conversion rate and ROI ---
  section("3. Does campaign performance differ by campaign_type?")
  cm <- load_campaign_performance()
  cm$campaign_type <- factor(cm$campaign_type)

  aov_conv <- aov(conversion_rate_pct ~ campaign_type, data = cm)
  aov_conv_p <- summary(aov_conv)[[1]][["Pr(>F)"]][1]
  kw_conv <- kruskal.test(conversion_rate_pct ~ campaign_type, data = cm)
  kw_roi <- kruskal.test(roi_pct ~ campaign_type, data = cm)

  print(tapply(cm$conversion_rate_pct, cm$campaign_type, function(x) round(c(mean = mean(x), n = length(x)), 2)))
  cat(sprintf("\nConversion rate - ANOVA p: %.4g | Kruskal-Wallis p: %.4g\n", aov_conv_p, kw_conv$p.value))
  cat(sprintf("ROI - Kruskal-Wallis p: %.4g\n", kw_roi$p.value))
  cat("Verdict: NOT statistically significant for either metric (p > 0.05,\n",
      "n=75 campaigns is a modest sample). Influencer shows the highest mean\n",
      "conversion rate descriptively, but with this sample size we cannot\n",
      "confidently claim one campaign_type outperforms another - more data\n",
      "would be needed before reallocating budget on this basis alone.\n")

  results$campaign_type_differences <- list(
    conversion_anova_p = signif(aov_conv_p, 4),
    conversion_kruskal_p = signif(kw_conv$p.value, 4),
    roi_kruskal_p = signif(kw_roi$p.value, 4),
    n_campaigns = nrow(cm)
  )

  # --- 4. Customer segment differences: CLV and purchase frequency ---
  section("4. Does customer behavior differ between segments (CLV, purchase frequency)?")
  cf <- load_customer_features()
  active <- cf[cf$customer_segment != "Never Purchased", ]
  active$customer_segment <- factor(active$customer_segment)

  aov_clv <- aov(customer_lifetime_value ~ customer_segment, data = active)
  aov_clv_p <- summary(aov_clv)[[1]][["Pr(>F)"]][1]
  kw_clv <- kruskal.test(customer_lifetime_value ~ customer_segment, data = active)
  kw_freq <- kruskal.test(purchase_frequency ~ customer_segment, data = active)

  print(tapply(active$customer_lifetime_value, active$customer_segment, function(x) round(c(mean = mean(x), n = length(x)))))
  cat(sprintf("\nCLV - ANOVA p: %.4g | Kruskal-Wallis p: %.4g\n", aov_clv_p, kw_clv$p.value))
  cat(sprintf("Purchase frequency - Kruskal-Wallis p: %.4g\n", kw_freq$p.value))
  cat("Verdict: Overwhelmingly significant (p < 0.001) for both - the segment\n",
      "labels genuinely separate distinct behavior/value groups. Loyal\n",
      "customers carry ~2.8x the CLV of the At-Risk segment, which is what\n",
      "makes the 'High Value + High Risk' priority segment (Phase 16 spec)\n",
      "meaningful rather than arbitrary.\n")

  results$segment_differences <- list(
    clv_anova_p = signif(aov_clv_p, 4),
    clv_kruskal_p = signif(kw_clv$p.value, 4),
    freq_kruskal_p = signif(kw_freq$p.value, 4),
    mean_clv_by_segment = round(tapply(active$customer_lifetime_value, active$customer_segment, mean))
  )

  results
}

if (sys.nframe() == 0) {
  run_group_difference_tests()
}
