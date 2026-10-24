variable "cluster_endpoint" {
  description = "API endpoint supplied by operator for adoption; inert loopback default for local validation."
  type        = string
  default     = "https://127.0.0.1:65535"
  validation {
    condition     = startswith(var.cluster_endpoint, "https://")
    error_message = "Use an HTTPS API endpoint."
  }
}
