# MarketLens - Phase 08: R Statistical Analysis
# utils.R
# ---------------------------------------------------------------------------
# Shared path helpers and data loaders for every script in R/statistics/.
# Uses ONLY base R (no CRAN packages) so this runs on a bare R install with
# no internet access required - matches the project's "no unnecessary
# technologies" rule and mirrors the dependency-light approach used in the
# Python phases.
#
# IMPORTANT: run all scripts from the project root, e.g.:
#   Rscript R/statistics/run_statistics.R
# Paths below are relative to the project root, not to this file.
# ---------------------------------------------------------------------------

DATA_RAW       <- "data/raw"
DATA_PROCESSED <- "data/processed"
REPORTS_DIR    <- "reports"

.check_root <- function() {
  if (!dir.exists(DATA_PROCESSED)) {
    stop(
      "Can't find data/processed/. Run this script from the MarketLens ",
      "project root, e.g.: Rscript R/statistics/run_statistics.R",
      call. = FALSE
    )
  }
}

load_orders_enriched <- function() {
  .check_root()
  read.csv(file.path(DATA_PROCESSED, "orders_enriched.csv"), stringsAsFactors = FALSE)
}

load_order_items <- function() {
  .check_root()
  read.csv(file.path(DATA_RAW, "order_items.csv"), stringsAsFactors = FALSE)
}

load_products <- function() {
  .check_root()
  read.csv(file.path(DATA_RAW, "products.csv"), stringsAsFactors = FALSE)
}

load_customer_features <- function() {
  .check_root()
  read.csv(file.path(DATA_PROCESSED, "customer_features.csv"), stringsAsFactors = FALSE)
}

load_campaign_performance <- function() {
  .check_root()
  read.csv(file.path(DATA_PROCESSED, "kpi_campaign_performance.csv"), stringsAsFactors = FALSE)
}

load_monthly_retention <- function() {
  .check_root()
  read.csv(file.path(DATA_PROCESSED, "kpi_monthly_retention.csv"), stringsAsFactors = FALSE)
}

load_monthly_revenue <- function() {
  .check_root()
  read.csv(file.path(DATA_PROCESSED, "kpi_revenue_by_month.csv"), stringsAsFactors = FALSE)
}

# order-grain COGS + gross_profit + margin_pct + discount_rate_pct, built the
# same way python/analytics/profitability.py does it (quantity * product
# cost, aggregated to order_id) so R and Python are checking the same
# definition of "margin".
build_order_margin_table <- function() {
  orders <- load_orders_enriched()
  items  <- load_order_items()
  products <- load_products()

  items <- merge(items, products[, c("product_id", "cost")], by = "product_id", all.x = TRUE)
  items$item_cogs <- items$quantity * items$cost

  cogs_by_order <- aggregate(item_cogs ~ order_id, data = items, FUN = sum)
  names(cogs_by_order) <- c("order_id", "cogs")

  o <- merge(orders, cogs_by_order, by = "order_id", all.x = TRUE)
  o$cogs[is.na(o$cogs)] <- 0
  o$gross_profit <- o$gross_revenue - o$cogs
  o$margin_pct <- ifelse(o$gross_revenue > 0, o$gross_profit / o$gross_revenue * 100, NA)
  o$discount_rate_pct <- ifelse(
    (o$gross_revenue + o$total_discount) > 0,
    o$total_discount / (o$gross_revenue + o$total_discount) * 100,
    NA
  )
  o[!is.na(o$margin_pct) & !is.na(o$discount_rate_pct), ]
}

section <- function(title) {
  cat("\n" , strrep("=", 70), "\n", sep = "")
  cat(title, "\n")
  cat(strrep("=", 70), "\n")
}
