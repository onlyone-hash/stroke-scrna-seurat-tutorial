# Run from the project root: source("run.R", encoding = "UTF-8")
if (.Platform$OS.type == "windows" && !l10n_info()[["UTF-8"]]) {
  Sys.setlocale("LC_ALL", "English_United States.utf8")
}
options(timeout = 900, repos = c(CRAN = "https://cloud.r-project.org"))
Sys.setenv(OMP_NUM_THREADS = "1", OPENBLAS_NUM_THREADS = "1", MKL_NUM_THREADS = "1")
if (!file.exists("config/analysis_config.R")) stop("请先将工作目录设为项目根目录。")
source("config/analysis_config.R", encoding = "UTF-8")
for (d in c("data/raw", "data/metadata", "results/figures", "results/tables", "results/objects", "results/logs")) dir.create(d, recursive = TRUE, showWarnings = FALSE)
logfile <- "results/logs/analysis.log"
sink(logfile, split = TRUE)
tryCatch({
  cat("Started:", format(Sys.time(), tz = "Asia/Shanghai"), "\n")
  for (s in c("00_setup.R", "01_download.R", "02_preprocess.R", "03_annotation.R", "04_pseudobulk.R", "05_report.R")) {
    cat("\n=====", s, "=====\n")
    source(file.path("scripts", s), encoding = "UTF-8")
    gc()
  }
  cat("Completed:", format(Sys.time(), tz = "Asia/Shanghai"), "\n")
}, finally = {
  writeLines(capture.output(sessionInfo()), "results/logs/sessionInfo.txt")
  sink()
})
