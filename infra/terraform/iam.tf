# IAM Role for EC2 Instance

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# IAM Role for EC2
resource "aws_iam_role" "openclaw_ec2" {
  name = "${local.name_prefix}-ec2-role"

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
    Name = "${local.name_prefix}-ec2-role"
  }
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "openclaw" {
  name = "${local.name_prefix}-instance-profile"
  role = aws_iam_role.openclaw_ec2.name
}

# Secrets Manager Policy
resource "aws_iam_policy" "secrets_manager_read" {
  name        = "${local.name_prefix}-secrets-manager-read"
  description = "Allow reading OpenClaw Lite secrets from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadOpenClawSecrets"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:openclaw-lite/*"
      }
    ]
  })
}

# Attach Secrets Manager policy to role
resource "aws_iam_role_policy_attachment" "secrets_manager" {
  role       = aws_iam_role.openclaw_ec2.name
  policy_arn = aws_iam_policy.secrets_manager_read.arn
}
