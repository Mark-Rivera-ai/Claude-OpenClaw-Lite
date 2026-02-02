output "public_ip" {
  description = "Public IP address of the server"
  value       = aws_eip.openclaw.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh -i ${path.module}/openclaw-key.pem ubuntu@${aws_eip.openclaw.public_ip}"
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_eip.openclaw.public_ip}"
}

output "health_check_url" {
  description = "Health check URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}/health" : "http://${aws_eip.openclaw.public_ip}/health"
}

output "ssh_private_key_path" {
  description = "Path to the SSH private key"
  value       = local_file.ssh_private_key.filename
}
