# RStudio 零基础配套练习

配套 [47 页 PDF 手册](../../output/pdf/GSE174574_RStudio_零基础复现手册.pdf)。先通过项目 `.Rproj` 打开项目，保持工作目录为包含 `run.R` 的根目录。

1. `01_RStudio_first_steps.R`：示例数字、赋值、均值、画第一张图、检查目录。
2. `02_reproduce_analysis.R`：依次完成依赖恢复、正式分析和结果验证。运行 Step C 一次即可，等待 Completed 后才执行 Step D。
3. `03_view_and_plot_results.R`：在本机分析完成后载入 RDS，重新画 UMAP / Spp1、导出练习图、查看和筛选 CSV。

第一次操作请在 Source 中选中完整代码块，按 Ctrl+Enter。不要把 R 代码贴到 Terminal。第三份脚本依赖第二份脚本生成的本地 RDS；GitHub ZIP 不包含这些大对象。

本机已核对三份脚本语法，并使用已安装的包验证练习绘图和读表逻辑；另从 PDF 中提取附录代码，交给 R 解析，检查复制后没有丢失引号和注释。干净电脑上的包恢复仍依赖相应网络、R 与系统环境。
