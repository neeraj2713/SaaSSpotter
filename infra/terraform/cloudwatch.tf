resource "aws_cloudwatch_log_group" "api_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-api"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "scrape_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-scrape"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "process_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-process"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/vendedlogs/states/${local.name_prefix}-pipeline"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_resource_policy" "sfn" {
  policy_name = "${local.name_prefix}-sfn-logs"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "delivery.logs.amazonaws.com"
      }
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "${aws_cloudwatch_log_group.sfn.arn}:*"
    }]
  })
}

resource "aws_cloudwatch_metric_alarm" "sfn_failures" {
  alarm_name          = "${local.name_prefix}-sfn-executions-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "PainPoint.io pipeline execution failed"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.pipeline.arn
  }
}
