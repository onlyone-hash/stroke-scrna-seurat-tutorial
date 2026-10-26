# Open the project .Rproj first. Run each block in order.
# Step A: confirm the project root. It must return TRUE.
getwd()
stopifnot(file.exists("run.R"))

# Step B: restore the recorded package environment (first run).
options(repos = c(CRAN = "https://cloud.r-project.org"), timeout = 900)
if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv")
}
renv::restore(project = getwd(), prompt = FALSE)
renv::load(project = getwd())

# Step C: download data and run the analysis ONCE. Wait for Completed.
source("run.R", encoding = "UTF-8")

# Step D: verify after the analysis has finished.
source("scripts/verify_results.R", encoding = "UTF-8")

