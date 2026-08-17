terraform {
  required_version = "= 1.14.8"
}

variable "project_name" {
  type    = string
  default = "ci-template-fixture"
}

output "project_name" {
  value = var.project_name
}
