# Workspace Templates

My personal workspace templates for projects, settings and some handy tool script.


## Note

`script/make-project.py` is used to create workspace from template, it will replace certain string to project name:

- `#<template_name>#` is replaced with `<project_name>`
- `#<TEMPLATE_NAME>#` is replaced with `<PROJECT_NAME>`
- `&<template_name>&` is replaced with sanitized `<project_name>` (strip front and back, make it statisfy c identifier rules)
- `&<TEMPLATE_NAME>&` is replaced with sanitized `<PROJECT_NAME>` (strip front and back, make it statisfy c identifier rules)

`&<template_name>&` and `&<TEMPLATE_NAME>&` are not applied to directory names and file names.
