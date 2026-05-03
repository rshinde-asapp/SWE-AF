terraform {
  required_version = ">= 1.0"

  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.80"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "snowflake" {
  # Configure via environment variables:
  # SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD
}

provider "aws" {
  region = var.aws_region
}

# S3 bucket for staging data
resource "aws_s3_bucket" "etl_staging" {
  bucket = "simple-etl-staging-${var.environment}"

  tags = {
    Name        = "Simple ETL Staging"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_versioning" "etl_staging" {
  bucket = aws_s3_bucket.etl_staging.id

  versioning_configuration {
    status = "Enabled"
  }
}

# IAM role for Airflow to access S3
resource "aws_iam_role" "airflow_s3_access" {
  name = "airflow-s3-access-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "Airflow S3 Access Role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "airflow_s3_policy" {
  name = "airflow-s3-policy"
  role = aws_iam_role.airflow_s3_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.etl_staging.arn,
          "${aws_s3_bucket.etl_staging.arn}/*"
        ]
      }
    ]
  })
}

# Outputs
output "warehouse_name" {
  value       = snowflake_warehouse.etl_warehouse.name
  description = "Name of the Snowflake warehouse"
}

output "database_name" {
  value       = snowflake_database.analytics.name
  description = "Name of the analytics database"
}

output "s3_bucket" {
  value       = aws_s3_bucket.etl_staging.bucket
  description = "S3 bucket for staging data"
}
