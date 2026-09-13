# MarketLens - Phase 08: R Statistical Analysis
# R/validation/cross_check_kpis.R
# ---------------------------------------------------------------------------
# Independent QA layer: recompute a handful of headline KPIs from the RAW
# CSVs in R, from scratch, without touching python/analytics/ at all, and
# compare against what Phase 07's Python pipeline reported in
# reports/business_analytics_report.md. Two independent implementations in
# two different languages agreeing is much stronger evidence of correctness
# than either one alone - that's the whole point of this file existing.
#
# Run from the project root:
#   Rscript R/validation/cross_check_kpis.R
# ---------------------------------------------------------------------------

source("R/statistics/utils.R")

EXPECTED <- list(
  gross_revenue = 857168939.70,
  net_revenue = 803075998.49,
  total_discount = 106043181.82,
  total_returned = 54092941.21,
  gross_margin_pct = 31.4,
  discount_impact_pct = 11.01,
  return_impact_pct = 6.31,
  n_orders = 82800
)

close_enough <- function(actual, expected, tol_pct = 0.05) {
  abs(actual - expected) / abs(expected) * 100 <= tol_pct
}

main <- function() {
  section("R-side independent cross-check of Phase 07 headline KPIs")

  orders <- load_orders_enriched()
  items  <- load_order_items()
  products <- load_products()

  items <- merge(items, products[, c("product_id", "cost")], by = "product_id", all.x = TRUE)
  items$item_cogs <- items$quantity * items$cost
  cogs_by_order <- aggregate(item_cogs ~ order_id, data = items, FUN = sum)
  names(cogs_by_order) <- c("order_id", "cogs")

  o <- merge(orders, cogs_by_order, by = "order_id", all.x = TRUE)
  o$cogs[is.na(o$cogs)] <- 0

  gross_revenue <- sum(o$gross_revenue)
  net_revenue <- sum(o$net_revenue)
  total_discount <- sum(o$total_discount)
  total_returned <- sum(o$total_returned_amount)
  total_cogs <- sum(o$cogs)
  gross_profit <- gross_revenue - total_cogs
  gross_margin_pct <- gross_profit / gross_revenue * 100
  discount_impact_pct <- total_discount / (gross_revenue + total_discount) * 100
  return_impact_pct <- total_returned / gross_revenue * 100
  n_orders <- nrow(o)

  checks <- list(
    list(name = "gross_revenue", actual = gross_revenue, expected = EXPECTED$gross_revenue, fmt = "currency"),
    list(name = "net_revenue", actual = net_revenue, expected = EXPECTED$net_revenue, fmt = "currency"),
    list(name = "total_discount", actual = total_discount, expected = EXPECTED$total_discount, fmt = "currency"),
    list(name = "total_returned", actual = total_returned, expected = EXPECTED$total_returned, fmt = "currency"),
    list(name = "gross_margin_pct", actual = gross_margin_pct, expected = EXPECTED$gross_margin_pct, fmt = "pct"),
    list(name = "discount_impact_pct", actual = discount_impact_pct, expected = EXPECTED$discount_impact_pct, fmt = "pct"),
    list(name = "return_impact_pct", actual = return_impact_pct, expected = EXPECTED$return_impact_pct, fmt = "pct"),
    list(name = "n_orders", actual = n_orders, expected = EXPECTED$n_orders, fmt = "int")
  )

  all_pass <- TRUE
  for (c in checks) {
    ok <- close_enough(c$actual, c$expected)
    all_pass <- all_pass && ok
    status <- if (ok) "MATCH" else "MISMATCH"
    if (c$fmt == "currency") {
      cat(sprintf("[%s] %-22s R=%.2f  Python=%.2f\n", status, c$name, c$actual, c$expected))
    } else if (c$fmt == "pct") {
      cat(sprintf("[%s] %-22s R=%.2f%%  Python=%.2f%%\n", status, c$name, c$actual, c$expected))
    } else {
      cat(sprintf("[%s] %-22s R=%d  Python=%d\n", status, c$name, c$actual, c$expected))
    }
  }

  cat("\n")
  if (all_pass) {
    cat("ALL CHECKS PASSED - R's independent recomputation from raw CSVs matches\n")
    cat("Phase 07's Python pipeline output within tolerance. The revenue/margin\n")
    cat("figures used throughout this project are cross-validated in two\n")
    cat("independent language implementations, not just asserted once.\n")
  } else {
    cat("MISMATCH DETECTED - investigate before trusting downstream phases.\n")
  }

  if (!dir.exists(REPORTS_DIR)) dir.create(REPORTS_DIR, recursive = TRUE)
  out <- c(
    "# MarketLens R Cross-Validation Report",
    "",
    "_Phase 08. Headline financial KPIs recomputed independently in R,",
    "straight from `data/raw/*.csv`, without importing any Python code,",
    "and compared against `reports/business_analytics_report.md`",
    "(Phase 07, computed in Python/pandas). Two independent language",
    "implementations agreeing is stronger evidence than one._",
    "",
    "| KPI | R (independent) | Python (Phase 07) | Match |",
    "|---|---:|---:|:---:|"
  )
  for (c in checks) {
    ok <- close_enough(c$actual, c$expected)
    a_str <- if (c$fmt == "int") sprintf("%d", c$actual) else sprintf("%.2f", c$actual)
    e_str <- if (c$fmt == "int") sprintf("%d", c$expected) else sprintf("%.2f", c$expected)
    out <- c(out, sprintf("| %s | %s | %s | %s |", c$name, a_str, e_str, if (ok) "Yes" else "NO"))
  }
  out <- c(out, "", if (all_pass) "**Result: all headline KPIs cross-validated.**" else "**Result: mismatch found - see above.**")
  writeLines(out, file.path(REPORTS_DIR, "r_cross_validation.md"))
  cat("\nWrote reports/r_cross_validation.md\n")
}

main()
