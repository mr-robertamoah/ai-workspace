# Terraform Conventions

## Module Structure
- `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`
- One resource type per file for large modules

## Naming
- Resources: `<type>_<name>` in snake_case
- Variables: descriptive, with descriptions and types

## Validation
- Always run `terraform fmt` and `terraform validate`
- Use `terraform plan` before apply
