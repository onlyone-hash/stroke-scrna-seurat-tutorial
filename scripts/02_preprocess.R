objects <- vector("list", nrow(samples)); qc_all <- vector("list", nrow(samples)); qc_summary <- vector("list", nrow(samples))
for (i in seq_len(nrow(samples))) {
  s <- samples[i, ]; prefix <- file.path("data/raw", paste0(s$gsm, "_", s$file_label, "_"))
  cat("Reading", s$sample_id, "\n")
  genes <- read.delim(gzfile(paste0(prefix, "genes.tsv.gz")), header = FALSE, stringsAsFactors = FALSE)
  barcodes <- readLines(gzfile(paste0(prefix, "barcodes.tsv.gz")))
  counts <- as(readMM(gzfile(paste0(prefix, "matrix.mtx.gz"))), "CsparseMatrix")
  stopifnot(nrow(counts) == nrow(genes), ncol(counts) == length(barcodes), all(counts@x >= 0), all(counts@x == round(counts@x)))
  rownames(counts) <- make.unique(if (ncol(genes) >= 2) genes[[2]] else genes[[1]])
  colnames(counts) <- paste0(s$sample_id, "_", barcodes)
  mt <- grepl("^mt-", rownames(counts), ignore.case = TRUE)
  stopifnot(sum(mt) >= 10)
  ncount <- Matrix::colSums(counts); nfeature <- Matrix::colSums(counts > 0)
  pctmt <- 100 * Matrix::colSums(counts[mt, , drop = FALSE]) / pmax(ncount, 1)
  keep <- nfeature >= cfg$min_features & nfeature <= cfg$max_features & ncount <= cfg$max_counts & pctmt <= cfg$max_percent_mt
  eligible <- which(keep)
  # 每个样本独立设种子，便于审计抽样；抽样发生在质控之后。
  set.seed(cfg$seed + i)
  chosen <- if (is.finite(cfg$max_cells_per_sample) && length(eligible) > cfg$max_cells_per_sample) sort(sample(eligible, cfg$max_cells_per_sample)) else eligible
  q <- data.frame(cell = colnames(counts), sample_id = s$sample_id, group = s$group,
    nCount_RNA = ncount, nFeature_RNA = nfeature, percent.mt = pctmt,
    pass_qc = keep, selected = seq_along(barcodes) %in% chosen, row.names = NULL)
  qc_all[[i]] <- q
  qc_summary[[i]] <- data.frame(sample_id = s$sample_id, group = s$group, input_cells = ncol(counts), qc_pass_cells = sum(keep), analyzed_cells = length(chosen), retained_percent = round(100 * mean(keep), 2))
  meta <- q[chosen, c("sample_id", "group", "percent.mt"), drop = FALSE]; rownames(meta) <- q$cell[chosen]
  objects[[i]] <- CreateSeuratObject(counts = counts[, chosen, drop = FALSE], min.cells = 0, min.features = 0, meta.data = meta, project = s$sample_id)
  rm(counts); gc()
}
qc <- do.call(rbind, qc_all); qc_stats <- do.call(rbind, qc_summary)
write_csv(qc, "qc_all_cells"); write_csv(qc_stats, "qc_summary")
print(qc_stats)
qc_dt <- data.table::as.data.table(qc)
for (nm in c("nFeature_RNA", "nCount_RNA", "percent.mt")) data.table::set(qc_dt, j = nm, value = as.numeric(qc_dt[[nm]]))
qc_long <- data.table::melt(qc_dt, id.vars = c("cell", "sample_id", "group", "pass_qc", "selected"), measure.vars = c("nFeature_RNA", "nCount_RNA", "percent.mt"), variable.name = "metric", value.name = "value")
p <- ggplot(qc_long, aes(sample_id, value, fill = group)) + geom_violin(scale = "width", linewidth = 0.2) +
  facet_wrap(~metric, scales = "free_y", nrow = 1) + scale_fill_manual(values = group_colors) +
  labs(title = "Quality control before filtering", subtitle = "All downloaded cell barcodes; thresholds are recorded in config/analysis_config.R", x = NULL, y = "Value") + theme(axis.text.x = element_text(angle = 45, hjust = 1))
save_plot(p, "01_qc_before", 12, 4.7)
save_plot(ggplot(subset(qc, selected), aes(nCount_RNA, nFeature_RNA, color = percent.mt)) + geom_point(size = .35, alpha = .6) + facet_wrap(~sample_id, nrow = 2) + scale_color_viridis_c() + labs(title = "Selected cells after QC", subtitle = "Count / feature relationship; color = mitochondrial UMI percentage", x = "Total UMI count", y = "Detected genes"), "02_qc_after", 11, 7)
obj <- merge(objects[[1]], y = objects[-1], merge.data = FALSE)
obj <- JoinLayers(obj)
obj$group <- factor(obj$group, levels = c("Sham", "MCAO"))
obj$sample_id <- factor(obj$sample_id, levels = samples$sample_id)
obj <- NormalizeData(obj, normalization.method = "LogNormalize", scale.factor = 10000, verbose = FALSE)
obj <- FindVariableFeatures(obj, selection.method = "vst", nfeatures = cfg$variable_features, verbose = FALSE)
obj <- ScaleData(obj, features = VariableFeatures(obj), verbose = FALSE)
obj <- RunPCA(obj, features = VariableFeatures(obj), npcs = cfg$npcs, seed.use = cfg$seed, verbose = FALSE)
obj <- FindNeighbors(obj, dims = cfg$dims, verbose = FALSE)
obj <- FindClusters(obj, resolution = cfg$resolution, algorithm = 1, random.seed = cfg$seed, verbose = FALSE)
obj <- RunUMAP(obj, dims = cfg$dims, seed.use = cfg$seed, n.threads = 1, verbose = FALSE)
save_plot(ElbowPlot(obj, ndims = cfg$npcs) + labs(title = "PCA elbow plot", subtitle = "This tutorial uses PC1-PC20; repeat with other dimensions for sensitivity checks"), "03_pca_elbow", 8, 5)
save_plot(DimPlot(obj, reduction = "umap", group.by = "seurat_clusters", label = TRUE, repel = TRUE, pt.size = .4) + labs(title = "Unsupervised clusters", subtitle = "Each dot is one selected cell; cluster numbers are arbitrary"), "04_umap_clusters", 9, 6.5)
save_plot(DimPlot(obj, group.by = "sample_id", pt.size = .35) + labs(title = "UMAP by sample", subtitle = "No batch correction: assess sample separation before biological interpretation"), "05_umap_samples", 9, 6.5)
save_plot(DimPlot(obj, group.by = "group", cols = group_colors, pt.size = .35) + labs(title = "UMAP by condition", subtitle = "Group separation can contain both disease and technical effects"), "06_umap_groups", 9, 6.5)
saveRDS(obj, "results/objects/01_preprocessed.rds", compress = TRUE)
rm(objects, qc_all, qc_summary, qc_long, qc_dt); gc()
