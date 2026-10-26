# Run AFTER the analysis has finished. Use the project root as getwd().
# Load the project environment when you start a new R session.
if (requireNamespace("renv", quietly = TRUE)) {
  renv::load(project = getwd())
}
library(Seurat)
library(ggplot2)

# Open a small result table in RStudio's data viewer.
qc_table <- read.csv("results/tables/qc_summary.csv",
                     fileEncoding = "UTF-8-BOM")
View(qc_table)

# The RDS is created by run.R; it is not included in the GitHub ZIP.
obj <- readRDS("results/objects/02_annotated.rds")
obj
table(obj$sample_id, obj$cell_type)

# Assigning a plot to a name does not always display it. Use print().
p_umap <- DimPlot(obj, reduction = "umap", group.by = "cell_type",
                  pt.size = 0.35)
print(p_umap)

# A gene expression map (descriptive; no disease hypothesis test here).
p_spp1 <- FeaturePlot(obj, features = "Spp1", order = TRUE,
                      pt.size = 0.35)
print(p_spp1)

# Save practice figures separately so the baseline figures are preserved.
dir.create("results/practice", recursive = TRUE, showWarnings = FALSE)
ggsave("results/practice/my_celltype_umap.png", plot = p_umap,
       width = 10, height = 7, dpi = 300, bg = "white")
ggsave("results/practice/my_Spp1_map.pdf", plot = p_spp1,
       width = 8, height = 6, bg = "white")

# Inspect the sample-level disease comparison. One row is one gene.
de_table <- read.csv("results/tables/microglia_pseudobulk_DE_all.csv",
                     fileEncoding = "UTF-8-BOM")
View(de_table)
de_table[de_table$gene %in% c("Spp1", "Lpl", "P2ry12", "Apoe"), ]

# Select a subset using the same joint threshold as the main workflow.
de_selected <- subset(de_table, FDR < 0.05 & abs(logFC) >= 1)
nrow(de_selected)

