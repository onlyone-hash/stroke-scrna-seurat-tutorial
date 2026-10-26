# 候选谱系标记组合，评分只用于辅助注释，不是细胞身份概率。
marker_sets <- list(
  Microglia = c("P2ry12", "Tmem119", "Cx3cr1", "Hexb", "C1qa"),
  Monocytes = c("Ccr2", "Ly6c2", "Plac8", "Lyz2", "Ms4a7"),
  Macrophages = c("Mrc1", "Lyve1", "Pf4", "F13a1", "Cd163"),
  Neutrophils = c("S100a8", "S100a9", "Retnlg", "Ly6g", "Ngp"),
  Astrocytes = c("Aqp4", "Slc1a3", "Aldoc", "Gja1", "Sox9"),
  Oligodendrocytes = c("Mbp", "Plp1", "Mog", "Mag", "Cnp"),
  OPC = c("Pdgfra", "Cspg4", "Olig1", "Olig2", "Vcan"),
  Neurons = c("Snap25", "Syt1", "Rbfox3", "Gad1", "Slc17a7"),
  Endothelial = c("Cldn5", "Pecam1", "Kdr", "Esam", "Flt1"),
  Pericytes = c("Rgs5", "Pdgfrb", "Kcnj8", "Abcc9", "Vtn"),
  Smooth_muscle = c("Acta2", "Tagln", "Myh11", "Cnn1", "Actg2"),
  Fibroblasts = c("Col1a1", "Col1a2", "Dcn", "Lum", "Col3a1"),
  Ependymal = c("Foxj1", "Pifo", "Ccdc153", "Dynlrb2", "Tmem212"),
  Choroid_plexus = c("Ttr", "Klotho", "Folr1", "Aqp1", "Otx2"),
  T_NK_cells = c("Cd3d", "Cd3e", "Trbc2", "Nkg7", "Ncr1"),
  B_cells = c("Cd79a", "Ms4a1", "Cd79b", "Cd74", "Cd37"),
  Erythroid = c("Hba-a1", "Hba-a2", "Hbb-bs", "Hbb-bt", "Alas2")
)
marker_table <- do.call(rbind, lapply(names(marker_sets), function(k) data.frame(cell_type = k, gene = marker_sets[[k]], present = marker_sets[[k]] %in% rownames(obj))))
write_csv(marker_table, "annotation_marker_panel")
annotation_genes <- unique(marker_table$gene[marker_table$present])
norm <- LayerData(obj, assay = "RNA", layer = "data")
evidence <- do.call(rbind, lapply(sort(unique(as.integer(obj$seurat_clusters))), function(k) {
  ix <- which(obj$seurat_clusters == k)
  data.frame(cluster = k, gene = annotation_genes,
    mean_log_normalized = Matrix::rowMeans(norm[annotation_genes, ix, drop = FALSE]),
    pct_detected = 100 * Matrix::rowMeans(norm[annotation_genes, ix, drop = FALSE] > 0), row.names = NULL)
}))
write_csv(evidence, "cluster_marker_evidence")
small <- as.matrix(norm[annotation_genes, , drop = FALSE])
z <- t(scale(t(small))); z[!is.finite(z)] <- 0
cell_scores <- sapply(marker_sets, function(gs) colMeans(z[intersect(gs, rownames(z)), , drop = FALSE]))
clusters <- as.character(obj$seurat_clusters)
cluster_levels <- sort(unique(as.integer(clusters)))
cluster_scores <- t(sapply(cluster_levels, function(k) colMeans(cell_scores[clusters == k, , drop = FALSE])))
rownames(cluster_scores) <- cluster_levels
annotation <- do.call(rbind, lapply(seq_along(cluster_levels), function(i) {
  ord <- order(cluster_scores[i, ], decreasing = TRUE)
  data.frame(cluster = as.character(cluster_levels[i]), n_cells = sum(clusters == cluster_levels[i]),
    candidate = colnames(cluster_scores)[ord[1]], second_candidate = colnames(cluster_scores)[ord[2]],
    top_score = cluster_scores[i, ord[1]], score_gap = cluster_scores[i, ord[1]] - cluster_scores[i, ord[2]])
}))
annotation$cell_type <- ifelse(annotation$top_score >= .25 & annotation$score_gap >= .15, annotation$candidate, "Uncertain")
annotation$annotation_basis <- ifelse(annotation$cell_type == "Uncertain", "ambiguous marker score; review required", "canonical multi-gene cluster score; provisional")
# 可在读完 marker dot plot / top markers 后填写人工复核表。
override_file <- "config/annotation_overrides.tsv"
if (file.exists(override_file)) {
  ov <- read.delim(override_file, stringsAsFactors = FALSE)
  if (nrow(ov)) {
    stopifnot(all(c("cluster", "cell_type", "reason") %in% names(ov)), !anyDuplicated(ov$cluster), all(ov$cluster %in% annotation$cluster))
    idx <- match(as.character(ov$cluster), annotation$cluster)
    annotation$cell_type[idx] <- ov$cell_type
    annotation$annotation_basis[idx] <- paste("manual review:", ov$reason)
  }
}
obj$cell_type <- annotation$cell_type[match(clusters, annotation$cluster)]
write_csv(annotation, "cluster_annotation")
write_csv(data.frame(cluster = rownames(cluster_scores), cluster_scores, check.names = FALSE), "cluster_annotation_scores")
print(annotation)
palette_types <- c(Microglia = "#477A47", Monocytes = "#C45A47", Macrophages = "#9467BD", Neutrophils = "#D4A52A", Astrocytes = "#329BA6", Oligodendrocytes = "#6084C3", OPC = "#9AC0DC", Neurons = "#D878AB", Endothelial = "#A17E50", Pericytes = "#9D5B71", Smooth_muscle = "#B89E75", Mural_cells = "#B89E75", Fibroblasts = "#9AA94B", Ependymal = "#55B89E", Choroid_plexus = "#D4A8C3", T_NK_cells = "#7D72B5", B_cells = "#E19D56", Erythroid = "#BD4242", Uncertain = "#A7ADB5")
save_plot(DimPlot(obj, group.by = "cell_type", cols = palette_types, pt.size = .35) + labs(title = "Brain cells: provisional lineage annotation", subtitle = "Marker-based labels; inspect the marker panel and cluster annotation table"), "07_umap_celltypes", 11, 7)
save_plot(DimPlot(obj, group.by = "cell_type", split.by = "group", cols = palette_types, pt.size = .3, ncol = 2) + labs(title = "Selected cells in Sham and MCAO"), "08_umap_split", 14, 6)
plot_markers <- unique(unlist(lapply(marker_sets, head, 2)))
plot_markers <- intersect(plot_markers, rownames(obj))
save_plot(DotPlot(obj, features = plot_markers, group.by = "seurat_clusters", dot.scale = 5, scale = TRUE) + RotatedAxis() + scale_color_gradient2(low = "#4477AA", mid = "#F5F5F5", high = "#C44E52") + labs(title = "Canonical markers across clusters", subtitle = "Dot size = percent detected; color = relative mean expression per gene", x = NULL, y = "Cluster"), "09_marker_dotplot", 15, 7.5)
key_genes <- intersect(c("P2ry12", "Tmem119", "Spp1", "Lpl", "Aqp4", "Cldn5"), rownames(obj))
save_plot(FeaturePlot(obj, features = key_genes, ncol = 3, order = TRUE, pt.size = .3, cols = c("#E4E9EE", "#C05046")), "10_gene_featureplots", 13, 8)
Idents(obj) <- "seurat_clusters"
set.seed(cfg$seed)
markers <- FindAllMarkers(obj, only.pos = TRUE, test.use = "wilcox", min.pct = .25, logfc.threshold = .25, max.cells.per.ident = 150, random.seed = cfg$seed, verbose = FALSE)
write_csv(markers, "cluster_markers_exploratory")
top_markers <- do.call(rbind, lapply(split(markers, markers$cluster), function(d) head(d[order(-d$avg_log2FC, d$p_val_adj), ], 10)))
rownames(top_markers) <- NULL; write_csv(top_markers, "cluster_top10_markers")
composition <- as.data.frame(table(sample_id = obj$sample_id, cell_type = obj$cell_type), stringsAsFactors = FALSE)
names(composition)[3] <- "n_cells"; composition$group <- samples$group[match(composition$sample_id, samples$sample_id)]
composition$proportion <- composition$n_cells / ave(composition$n_cells, composition$sample_id, FUN = sum)
write_csv(composition, "celltype_composition")
save_plot(ggplot(composition, aes(sample_id, proportion, fill = cell_type)) + geom_col(width = .72) + scale_fill_manual(values = palette_types) + scale_y_continuous(labels = scales::label_percent()) + labs(title = "Cell composition in each selected sample", subtitle = "Captured-cell proportions; not absolute cell abundance in brain tissue", x = NULL, y = "Fraction of selected cells", fill = "Provisional type") + theme(axis.text.x = element_text(angle = 45, hjust = 1)), "11_composition", 11, 6)
um <- Embeddings(obj, "umap")
cell_meta <- data.frame(cell = colnames(obj), obj[[]], UMAP_1 = um[, 1], UMAP_2 = um[, 2], row.names = NULL)
write_csv(cell_meta, "analyzed_cell_metadata")
saveRDS(obj, "results/objects/02_annotated.rds", compress = TRUE)
rm(z, small, cell_scores, norm); gc()
