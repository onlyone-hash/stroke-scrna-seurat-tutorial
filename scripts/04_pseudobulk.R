# 教学重点：按“样本 × 同一细胞类型”累加原始 UMI，使用 3 vs 3 样本建模。
pb_type <- "Microglia"
counts <- LayerData(obj, assay = "RNA", layer = "counts")
sel <- which(obj$cell_type == pb_type)
ncells <- table(factor(obj$sample_id[sel], levels = samples$sample_id))
pb_n <- data.frame(sample_id = samples$sample_id, group = samples$group, n_cells = as.integer(ncells))
write_csv(pb_n, "microglia_pseudobulk_cell_counts")
if (any(ncells < cfg$min_cells_pseudobulk)) stop("部分样本的小胶质细胞少于最低门槛；请复核注释或提高抽样上限。不能把缺失样本计为零表达。")
pb <- sapply(samples$sample_id, function(s) Matrix::rowSums(counts[, which(obj$cell_type == pb_type & obj$sample_id == s), drop = FALSE]))
colnames(pb) <- samples$sample_id
group <- factor(samples$group, levels = c("Sham", "MCAO"))
design <- model.matrix(~group)
y <- edgeR::DGEList(counts = pb, group = group)
keep_genes <- edgeR::filterByExpr(y, design = design)
y <- y[keep_genes, , keep.lib.sizes = FALSE]
y <- edgeR::calcNormFactors(y, method = "TMM")
y <- edgeR::estimateDisp(y, design, robust = TRUE)
fit <- edgeR::glmQLFit(y, design, robust = TRUE)
test <- edgeR::glmQLFTest(fit, coef = "groupMCAO")
de <- edgeR::topTags(test, n = Inf, sort.by = "PValue")$table
de <- data.frame(gene = rownames(de), de, row.names = NULL)
de$direction <- ifelse(de$FDR < cfg$fdr & de$logFC >= cfg$log2fc, "Higher_in_MCAO", ifelse(de$FDR < cfg$fdr & de$logFC <= -cfg$log2fc, "Lower_in_MCAO", "Below_threshold"))
write_csv(de, "microglia_pseudobulk_DE_all")
write_csv(subset(de, direction != "Below_threshold"), "microglia_pseudobulk_DE_significant")
write_csv(data.frame(gene = rownames(pb), pb, check.names = FALSE), "microglia_pseudobulk_raw_counts")
logcpm <- edgeR::cpm(y, log = TRUE, prior.count = 2)
write_csv(data.frame(gene = rownames(logcpm), logcpm, check.names = FALSE), "microglia_logCPM")
write_csv(data.frame(sample_id = samples$sample_id, group = group, y$samples[, c("lib.size", "norm.factors")], row.names = NULL), "microglia_library_sizes")
v <- transform(de, neglog10FDR = -log10(pmax(FDR, 1e-300)))
labels <- head(v[v$direction != "Below_threshold", ], 10)
p <- ggplot(v, aes(logFC, neglog10FDR, color = direction)) + geom_point(alpha = .65, size = 1) +
  geom_vline(xintercept = c(-cfg$log2fc, cfg$log2fc), linetype = 2, color = "#8D99A5") +
  geom_hline(yintercept = -log10(cfg$fdr), linetype = 2, color = "#8D99A5") +
  ggrepel::geom_text_repel(data = labels, aes(label = gene), size = 3, max.overlaps = 20, seed = cfg$seed) +
  scale_color_manual(values = c(Higher_in_MCAO = "#D9634C", Lower_in_MCAO = "#3C8DAD", Below_threshold = "#BBC3CA")) +
  labs(title = "Microglia: MCAO versus Sham", subtitle = "edgeR quasi-likelihood pseudobulk; 3 samples per group; FDR < 0.05 and |log2FC| >= 1", x = "log2 fold change (MCAO / Sham)", y = "-log10 FDR", color = NULL)
save_plot(p, "12_microglia_volcano", 10, 7)
eligible_top <- de$gene[de$direction != "Below_threshold"]
if (length(eligible_top) < 2) eligible_top <- head(de$gene, 20)
heat_genes <- head(eligible_top, 20)
heat <- t(scale(t(logcpm[heat_genes, , drop = FALSE]))); heat[!is.finite(heat)] <- 0
hd <- as.data.frame(as.table(heat)); names(hd) <- c("gene", "sample_id", "zscore")
hd$gene <- factor(hd$gene, levels = rev(heat_genes)); hd$sample_id <- factor(hd$sample_id, levels = samples$sample_id)
save_plot(ggplot(hd, aes(sample_id, gene, fill = zscore)) + geom_tile(color = "white", linewidth = .15) + scale_fill_gradient2(low = "#3C8DAD", mid = "#F8F8F8", high = "#D9634C", midpoint = 0) + labs(title = "Microglia pseudobulk expression", subtitle = "Top 20 genes ranked by FDR/P value; row-scaled logCPM; selection and display use the same data", x = NULL, y = NULL, fill = "Row Z"), "13_microglia_heatmap", 9, 8)
selected_genes <- intersect(c("P2ry12", "Tmem119", "Spp1", "Lpl", "Apoe", "Il1b"), rownames(logcpm))
gd <- do.call(rbind, lapply(selected_genes, function(g) data.frame(gene = g, sample_id = samples$sample_id, group = group, logCPM = logcpm[g, ])))
save_plot(ggplot(gd, aes(group, logCPM, color = group)) + geom_boxplot(width = .4, outlier.shape = NA, alpha = .2) + geom_point(position = position_jitter(width = .07, seed = cfg$seed), size = 2.5) + facet_wrap(~gene, scales = "free_y", ncol = 3) + scale_color_manual(values = group_colors) + labs(title = "Selected genes in microglia", subtitle = "One point = one sample (not one cell); gene-wise tests are in the full DE table", x = NULL, y = "TMM log2 CPM") + theme(legend.position = "none"), "14_microglia_sample_expression", 11, 7)
pc <- prcomp(t(logcpm), scale. = FALSE)
pd <- data.frame(sample_id = samples$sample_id, group = group, PC1 = pc$x[, 1], PC2 = pc$x[, 2])
varpct <- 100 * pc$sdev^2 / sum(pc$sdev^2)
save_plot(ggplot(pd, aes(PC1, PC2, color = group, label = sample_id)) + geom_point(size = 4) + ggrepel::geom_text_repel(seed = cfg$seed) + scale_color_manual(values = group_colors) + labs(title = "Microglia pseudobulk sample PCA", subtitle = "Inspect the three biological samples in each group for separation and outliers", x = sprintf("PC1 (%.1f%%)", varpct[1]), y = sprintf("PC2 (%.1f%%)", varpct[2])), "15_microglia_pseudobulk_pca", 8, 6)
saveRDS(list(counts = pb, dge = y, design = design, fit = fit, test = test, de = de, n_cells = pb_n), "results/objects/03_pseudobulk.rds")
