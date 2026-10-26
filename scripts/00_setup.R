# 只安装缺少的包；不自动升级已有包。
cran_pkgs <- c("Seurat", "SeuratObject", "Matrix", "ggplot2", "patchwork", "data.table", "digest", "jsonlite", "ragg", "ggrepel", "renv", "statmod")
missing <- cran_pkgs[!vapply(cran_pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) install.packages(missing)
if (!requireNamespace("edgeR", quietly = TRUE)) {
  if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")
  BiocManager::install("edgeR", ask = FALSE, update = FALSE)
}
suppressPackageStartupMessages({
  library(Seurat); library(Matrix); library(ggplot2); library(patchwork)
})
set.seed(cfg$seed)
future::plan("sequential")
theme_set(theme_minimal(base_size = 12) + theme(
  plot.title = element_text(face = "bold", color = "#17324D"),
  plot.subtitle = element_text(color = "#526777", size = 10),
  panel.grid.minor = element_blank(), legend.position = "right"
))
group_colors <- c(Sham = "#3C8DAD", MCAO = "#D9634C")
save_plot <- function(p, name, width = 10, height = 6) {
  ggsave(file.path("results/figures", paste0(name, ".png")), p,
         width = width, height = height, dpi = 220, device = ragg::agg_png, bg = "white", limitsize = FALSE)
  ggsave(file.path("results/figures", paste0(name, ".pdf")), p,
         width = width, height = height, device = grDevices::cairo_pdf, bg = "white", limitsize = FALSE)
}
write_csv <- function(x, name) data.table::fwrite(x, file.path("results/tables", paste0(name, ".csv")), bom = TRUE)
pk <- installed.packages()
used_pkgs <- unique(c(cran_pkgs, "edgeR", "limma", "uwot", "igraph", "future"))
write_csv(data.frame(package = used_pkgs, version = pk[used_pkgs, "Version"]), "package_versions")
