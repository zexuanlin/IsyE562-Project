# ISyE 562 Project

## Data preparation

You need to download the data from kaggle and unzip it. More instructions can be
found in the separate [documentation](data/README.md)

## `renv` R package manager

You should first install `renv` package in R, then run `renv::restore()` before
first run. This makes sure that everyone is using the same R package.

Overall workflow should be like this:

- `install.packages("renv")`
- `library("renv")`
- `renv::restore()`

- Put persistent packages (not yet covered in code) in `_dependencies.R`
  - Some packages like `rlang` might need to be explicitly put there
- Run `renv::init()` inside a R command line.
- Run `renv::install()` to resolve other dependencies not automatically handled.
- ~~Run `renv::update()` to see if the latest version works.~~ (Do NOT do that unless you know what you are doing! May have breaking change.)
- Run `renv::snapshot()` after you confirm that the current installations would work.
- Run `renv::restore()` to restore to a previous checkpoint saved by `snapshot()` -- You may want to do that on a new machine for exact version match.
