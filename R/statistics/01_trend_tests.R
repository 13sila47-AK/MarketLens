# MarketLens - Phase 08: R Statistical Analysis
# 01_trend_tests.R
# ---------------------------------------------------------------------------
# Formal trend tests, as opposed to Phase 07's descriptive month-over-month
# tables. Two questions:
#
#   1. Is the month-over-month customer retention decline (Phase 07 found
#      ~18% -> ~12%) a statistically real trend, or noise?
#   2. Is revenue growth genuinely DECELERATING (not just "growing"), i.e.
#      is there a statistically significant negative curvature over time?
# ---------------------------------------------------------------------------

source("R/statistics/utils.R")

run_trend_tests <- function() {
  results <- list()

  # --- 1. Retention trend: linear regression of retention_rate_pct on month index ---
  section("1. Monthly customer retention trend (linear regression)")
  ret <- load_monthly_retention()
  ret <- ret[order(ret$month), ]
  ret$t <- seq_len(nrow(ret)) - 1

  fit_ret <- lm(retention_rate_pct ~ t, data = ret)
  s <- summary(fit_ret)
  slope <- coef(fit_ret)[["t"]]
  slope_p <- s$coefficients["t", "Pr(>|t|)"]
  r2 <- s$r.squared

  cat(sprintf("N months: %d\n", nrow(ret)))
  cat(sprintf("Slope: %.4f percentage points / month\n", slope))
  cat(sprintf("R-squared: %.4f\n", r2))
  cat(sprintf("p-value (slope != 0): %.4g\n", slope_p))
  cat(sprintf(
    "Predicted retention: %.2f%% (month 1) -> %.2f%% (month %d)\n",
    predict(fit_ret, newdata = data.frame(t = 0)),
    predict(fit_ret, newdata = data.frame(t = max(ret$t))),
    nrow(ret)
  ))
  verdict_ret <- if (slope_p < 0.05 && slope < 0) {
    "SIGNIFICANT DECLINE - the retention drop Phase 07 found descriptively is statistically real, not noise."
  } else {
    "No statistically significant declining trend detected."
  }
  cat("Verdict:", verdict_ret, "\n")

  results$retention_trend <- list(
    slope_pct_pts_per_month = round(slope, 4),
    r_squared = round(r2, 4),
    p_value = signif(slope_p, 4),
    n_months = nrow(ret),
    verdict = verdict_ret
  )

  # --- 2. Revenue deceleration: quadratic regression on log(monthly revenue) ---
  section("2. Revenue growth deceleration (quadratic regression on log-revenue)")
  rev <- load_monthly_revenue()
  rev <- rev[order(rev$month), ]
  rev$t <- seq_len(nrow(rev)) - 1
  rev$log_revenue <- log(rev$gross_revenue)

  fit_rev <- lm(log_revenue ~ t + I(t^2), data = rev)
  s2 <- summary(fit_rev)
  quad_coef <- coef(fit_rev)[["I(t^2)"]]
  quad_p <- s2$coefficients["I(t^2)", "Pr(>|t|)"]
  r2_rev <- s2$r.squared

  cat(sprintf("N months: %d\n", nrow(rev)))
  cat(sprintf("Quadratic (t^2) coefficient: %.5f\n", quad_coef))
  cat(sprintf("p-value (t^2 term): %.4g\n", quad_p))
  cat(sprintf("R-squared: %.4f\n", r2_rev))
  verdict_rev <- if (quad_p < 0.05 && quad_coef < 0) {
    "SIGNIFICANT DECELERATION - revenue is not just growing, its growth rate is statistically slowing down."
  } else {
    "No statistically significant deceleration detected."
  }
  cat("Verdict:", verdict_rev, "\n")

  results$revenue_deceleration <- list(
    quadratic_coef = round(quad_coef, 5),
    r_squared = round(r2_rev, 4),
    p_value = signif(quad_p, 4),
    n_months = nrow(rev),
    verdict = verdict_rev
  )

  results
}

if (sys.nframe() == 0) {
  run_trend_tests()
}
