base_geo <- "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE174nnn/GSE174574/"
download_safe <- function(url, dest) {
  # 临时文件完整下载后才重命名，避免把中断下载误当成成功文件。
  if (file.exists(dest) && file.info(dest)$size > 0) return(invisible(dest))
  tmp <- paste0(dest, ".part")
  for (attempt in 1:3) {
    ok <- tryCatch({download.file(url, tmp, mode = "wb", method = "libcurl", quiet = TRUE); TRUE}, error = function(e) FALSE)
    if (ok && file.exists(tmp) && file.info(tmp)$size > 0) {
      if (!file.rename(tmp, dest)) stop("无法重命名下载文件：", dest)
      return(invisible(dest))
    }
  }
  stop("下载失败：", url, "；可按教程手动下载到 ", dest)
}
soft_file <- "data/metadata/GSE174574_family.soft.gz"
download_safe(paste0(base_geo, "soft/GSE174574_family.soft.gz"), soft_file)
soft <- readLines(gzfile(soft_file), warn = FALSE)
# 使用明确样本表：GEO 的 MCAO2/3 treatment 字段都误写为 MCAO1；以标题和文件名区分。
samples <- data.frame(
  sample_id = c("Sham1", "Sham2", "Sham3", "MCAO1", "MCAO2", "MCAO3"),
  gsm = paste0("GSM", 5319987:5319992),
  group = rep(c("Sham", "MCAO"), each = 3),
  file_label = c("sham1", "sham2", "sham3", "MCAO1", "MCAO2", "MCAO3"),
  timepoint = c(rep("sham", 3), rep("24h_after_MCAO", 3))
)
write.table(samples, "config/samples.tsv", sep = "\t", row.names = FALSE, quote = FALSE)
urls <- sub("^!Sample_supplementary_file_[0-9]+ = ftp:", "https:", soft[grepl("^!Sample_supplementary_file_", soft)])
stopifnot(length(urls) == 18L, all(vapply(samples$gsm, function(g) any(grepl(g, urls)), logical(1))))
for (url in urls) { cat("Data:", basename(url), "\n"); download_safe(url, file.path("data/raw", basename(url))) }
manifest <- data.frame(file = basename(urls), url = urls, bytes = file.info(file.path("data/raw", basename(urls)))$size,
  sha256 = vapply(file.path("data/raw", basename(urls)), digest::digest, character(1), algo = "sha256", file = TRUE))
expected <- "config/input_checksums.tsv"
if (file.exists(expected)) {
  old <- read.delim(expected, stringsAsFactors = FALSE)
  stopifnot(setequal(old$file, manifest$file))
  if (any(old$sha256[match(manifest$file, old$file)] != manifest$sha256)) stop("数据 SHA256 与本项目基准不一致，请检查下载文件。")
} else write.table(manifest[, c("file", "sha256")], expected, sep = "\t", row.names = FALSE, quote = FALSE)
write_csv(manifest, "input_manifest")
writeLines(c("Source: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174574", soft[grepl("^!Series_(title|summary|overall_design|pubmed_id)|^!Sample_(title|geo_accession|characteristics_ch1)", soft)]), "data/metadata/source_summary.txt")
