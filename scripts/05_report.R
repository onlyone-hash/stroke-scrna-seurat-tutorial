md_table <- function(d) {
  for (nm in names(d)) {
    x <- d[[nm]]
    d[[nm]] <- if (!is.numeric(x)) as.character(x) else if (all(x == trunc(x))) format(x, trim = TRUE, scientific = FALSE) else if (nm == "FDR") formatC(x, format = "e", digits = 3) else formatC(x, format = "f", digits = 3)
  }
  c(paste0("| ", paste(names(d), collapse = " | "), " |"),
    paste0("| ", paste(rep("---", ncol(d)), collapse = " | "), " |"),
    apply(d, 1, function(x) paste0("| ", paste(x, collapse = " | "), " |")))
}
n_up <- sum(de$direction == "Higher_in_MCAO"); n_down <- sum(de$direction == "Lower_in_MCAO")
highlights <- de[match(c("P2ry12", "Tmem119", "Spp1", "Lpl", "Apoe", "Il1b"), de$gene), c("gene", "logFC", "FDR", "direction")]
highlights <- highlights[!is.na(highlights$gene), ]
gene_list <- function(direction) {
  gs <- highlights$gene[highlights$direction == direction]
  if (length(gs)) paste(gs, collapse = "、") else "无"
}
gene_summary <- sprintf("本次结果的预选基因中，MCAO 较高且达到联合阈值：%s；MCAO 较低且达到联合阈值：%s；未达到联合阈值：%s。表达差异反映该数据和分析条件下的转录关联。这里没有验证细胞起源、因果关系或蛋白功能，也不能据此把细胞简单命名为 M1/M2。", gene_list("Higher_in_MCAO"), gene_list("Lower_in_MCAO"), gene_list("Below_threshold"))
report <- c(
  "# GSE174574 小鼠脑缺血单细胞：本次实际运行结果", "",
  "这是公开数据的教学再分析，从作者上传的 UMI 计数矩阵开始。不是新开展的动物实验，也不是对原论文所有图的重现。", "",
  "## 数据与样本", "",
  "数据来自 [GSE174574](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174574)，背景见 [Zheng 等原始研究](https://doi.org/10.1177/0271678X211026770)。小鼠左侧脑半球，Sham 与 MCAO 后 24 小时各 3 个样本。", "",
  md_table(qc_stats), "",
  sprintf("下载矩阵共包含 **%s 个细胞条形码**；本教程阈值下有 **%s 个细胞合格**；实际分析 **%s 个细胞、%s 个基因（含未检出基因行）、%s 个聚类**。", format(sum(qc_stats$input_cells), big.mark = ","), format(sum(qc_stats$qc_pass_cells), big.mark = ","), format(ncol(obj), big.mark = ","), format(nrow(obj), big.mark = ","), nrow(annotation)), "",
  sprintf("每个样本最多抽取 %s 个合格细胞；种子 %s。抽样条形码见 analyzed_cell_metadata.csv，全部下载细胞的筛选记录见 qc_all_cells.csv。", cfg$max_cells_per_sample, cfg$seed), "",
  "![质控](figures/01_qc_before.png)", "",
  "## 聚类与细胞身份", "",
  "UMAP 每个点代表一个细胞。颜色显示基于多个经典标记的暂定谱系注释；聚类编号本身不携带细胞身份。所有注释应结合标记点图、top10 标记和样本来源审阅。", "",
  "![细胞注释](figures/07_umap_celltypes.png)", "",
  md_table(annotation[, c("cluster", "n_cells", "cell_type", "candidate", "score_gap")]), "",
  "人工复核将 cluster 4 标为血管壁细胞（Mural_cells）：它同时富集 Rgs5/Pdgfrb 与 Acta2/Tagln/Myh11，不强行分成纯周细胞或纯平滑肌。cluster 13 同时带有小胶质细胞与内皮标记，标为 Uncertain，并排除在小胶质细胞差异分析之外。具体表达比例和均值见 `tables/cluster_marker_evidence.csv`，复核理由保存在 `config/annotation_overrides.tsv`。", "",
  "本次 Ttr 在多个非脉络丛谱系中也普遍检出，提示需要关注环境 RNA 等背景信号。只有脉络丛相关簇同时有更高 Ttr 与 Folr1 等组合证据；不能把所有 Ttr 阳性细胞都叫脉络丛细胞。本教程未进行污染校正。", "",
  "![标记证据](figures/09_marker_dotplot.png)", "",
  "## 细胞组成", "",
  "以下比例仅指经过取材、消化、捕获、质控和抽样后留下的细胞。柱子不能证明脑组织中某类细胞的绝对数量增减。抽样保留每个样本的组成趋势，但可能遗漏稀有细胞。", "",
  "![细胞组成](figures/11_composition.png)", "",
  "## 小胶质细胞的样本层面差异表达", "",
  "按每个样本中的小胶质细胞累加原始 UMI，形成 6 个伪 bulk 文库；edgeR TMM + quasi-likelihood 检验，模型 ~ group，对比 MCAO / Sham。统计单位是样本。", "",
  md_table(pb_n), "",
  sprintf("本次检验 %s 个达到表达过滤标准的基因。按 FDR < %.2f 且 |log2FC| >= %.1f，有 **%s 个 MCAO 较高基因、%s 个 MCAO 较低基因**。这是抽样数据和暂定注释下的探索结果。", nrow(de), cfg$fdr, cfg$log2fc, n_up, n_down), "",
  "![差异火山图](figures/12_microglia_volcano.png)", "",
  "预先选定的一组身份/反应相关基因：正 logFC 表示 MCAO 较高；FDR 是多重检验校正后的统计量。", "",
  md_table(highlights), "",
  "### 怎样概括这组结果", "",
  gene_summary, "",
  "![样本表达](figures/14_microglia_sample_expression.png)", "",
  "每个点是一份样本，3 vs 3。盒图只概括这 3 个数；不能用细胞数替代样本数。对任一基因的解释应同时查看效应方向、FDR 和三个样本的一致性。", "",
  "![热图](figures/13_microglia_heatmap.png)", "",
  "热图每行单独标准化，因此颜色不能比较不同基因的绝对高低；基因来自同一数据的差异排序，组间分离不是独立验证。", "",
  "## 局限与可继续做的事", "",
  "- 每组只有 3 个样本，且采用教学抽样；全量运行、阈值敏感性分析和独立数据验证仍然需要。",
  "- 本流程没有执行专门的双细胞检测、环境 RNA 校正或批次整合。高 UMI/高基因数阈值不等于双细胞检测。",
  "- 未进行样本批次整合；UMAP 和聚类可能混有技术差异。真实疾病变化也会导致组间分离，不能一律消除。",
  "- 小胶质细胞与单核/巨噬细胞的活化状态会共享标记，粗粒度注释存在边界不确定性。",
  "- 未测量蛋白、细胞功能或因果关系，不能把某基因表达变化直接解释为药物靶点已被证明。",
  "- 只包含急性期小鼠数据，不能直接推断人类患者、长期恢复或治疗效果。", "",
  "完整复现步骤、术语解释和每张图的读法见 [详细中文教程](../docs/中文详细教程.md)。", "",
  "## 可审计文件", "",
  "- `tables/input_manifest.csv`：18 个下载文件的 HTTPS 来源、大小及 SHA256。",
  "- `tables/qc_summary.csv`、`tables/qc_all_cells.csv`：每份样本和每个条形码的筛选记录。",
  "- `tables/cluster_annotation.csv`、`tables/cluster_top10_markers.csv`：注释与标记证据。",
  "- `tables/microglia_pseudobulk_DE_all.csv`：完整检验表，避免只展示显著结果。",
  "- `logs/sessionInfo.txt`、`logs/analysis.log`：实际 R 运行环境及步骤记录。", ""
)
writeLines(enc2utf8(report), "results/分析报告.md", useBytes = TRUE)
summary <- list(accession = cfg$accession, seed = cfg$seed, max_cells_per_sample = cfg$max_cells_per_sample,
  input_cells = sum(qc_stats$input_cells), qc_pass = sum(qc_stats$qc_pass_cells), analyzed_cells = ncol(obj),
  clusters = nrow(annotation), tentative_cell_types = sort(unique(obj$cell_type)), tested_genes = nrow(de),
  microglia_higher_MCAO = n_up, microglia_lower_MCAO = n_down)
jsonlite::write_json(summary, "results/run_summary.json", auto_unbox = TRUE, pretty = TRUE)
writeLines(capture.output(dput(cfg)), "results/logs/parameters.R")
renv::snapshot(project = getwd(), type = "explicit", prompt = FALSE)
