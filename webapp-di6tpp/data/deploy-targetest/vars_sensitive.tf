variable "pm_api_token_id" {
  description = "Token ID for the Terraform provider"
  type        = string
  sensitive   = true
}

variable "pm_api_token_secret" {
  description = "Secret for the Terraform provider"
  type        = string
  sensitive   = true
}
