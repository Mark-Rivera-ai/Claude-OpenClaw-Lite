variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance type (t3.small recommended)"
  type        = string
  default     = "t3.small"
}

variable "domain_name" {
  description = "Domain name for SSL certificate (optional, leave empty to skip SSL)"
  type        = string
  default     = ""
}

variable "ssh_allowed_ips" {
  description = "IP addresses allowed to SSH (CIDR format)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict in production!
}

variable "monthly_budget_usd" {
  description = "Monthly API budget in USD"
  type        = number
  default     = 50
}

variable "complexity_threshold" {
  description = "Complexity score threshold for Claude routing (0.0-1.0)"
  type        = number
  default     = 0.5
}

variable "admin_email" {
  description = "Admin email for Let's Encrypt and alerts"
  type        = string
  default     = ""
}
