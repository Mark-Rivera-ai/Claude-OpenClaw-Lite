# IAM role for EC2 instance
resource "aws_iam_role" "openclaw" {
  name = "openclaw-lite-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

# Policy for Secrets Manager + Logs
resource "aws_iam_role_policy" "secrets_access" {
  name = "openclaw-secrets-access"
  role = aws_iam_role.openclaw.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:us-east-1:318894386324:secret:openclaw-lite/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Instance profile
resource "aws_iam_instance_profile" "openclaw" {
  name = "openclaw-lite-instance-profile"
  role = aws_iam_role.openclaw.name
}
