# Skip the system package check since Arch isn't supported and
# it currently conflicts with installed `rpm-tools`
options(renv.config.sysreqs.check = FALSE)
if (identical(.Platform$OS.type, "unix") && Sys.info()[["sysname"]] == "Linux") options(browser = "xdg-open")
# Preserve = assignments when formatting through the R language server.
options(languageserver.formatting_style = function(options) {
  style <- styler::tidyverse_style(indent_by = options$tabSize)
  style$token$force_assignment_op <- NULL
  style
})
source("renv/activate.R")
