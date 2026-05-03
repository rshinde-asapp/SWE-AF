variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for infrastructure resources"
  type        = string
  default     = "us-east-1"
}

variable "warehouse_size" {
  description = "Snowflake warehouse size"
  type        = string
  default     = "XSMALL"

  validation {
    condition     = contains(["XSMALL", "SMALL", "MEDIUM", "LARGE", "XLARGE"], var.warehouse_size)
    error_message = "Warehouse size must be a valid Snowflake warehouse size."
  }
}
