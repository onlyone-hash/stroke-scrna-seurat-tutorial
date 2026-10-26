# 所有会改变分析结果的主要参数集中在这里；完整模式建议另复制项目运行。
cfg <- list(
  accession = "GSE174574",
  seed = 20261026L,
  max_cells_per_sample = 1000L, # 改成 Inf 可运行全部质控合格细胞
  min_features = 200L,
  max_features = 6000L,
  max_counts = 25000L,
  max_percent_mt = 20,
  variable_features = 2000L,
  npcs = 30L,
  dims = 1:20,
  resolution = 0.4,
  min_cells_pseudobulk = 20L,
  fdr = 0.05,
  log2fc = 1
)
