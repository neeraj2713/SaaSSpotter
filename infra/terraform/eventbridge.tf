resource "aws_cloudwatch_event_rule" "daily_scrape" {
  name                = "${local.name_prefix}-daily-scrape"
  description         = "Trigger PainPoint.io pipeline daily at 6:00 UTC"
  schedule_expression = "cron(0 6 * * ? *)"
}

resource "aws_iam_role" "eventbridge_sfn" {
  name = "${local.name_prefix}-eventbridge-sfn"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name = "${local.name_prefix}-eventbridge-sfn"
  role = aws_iam_role.eventbridge_sfn.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["states:StartExecution"]
      Resource = aws_sfn_state_machine.pipeline.arn
    }]
  })
}

resource "aws_cloudwatch_event_target" "daily_scrape" {
  rule      = aws_cloudwatch_event_rule.daily_scrape.name
  target_id = "StartPipeline"
  arn       = aws_sfn_state_machine.pipeline.arn
  role_arn  = aws_iam_role.eventbridge_sfn.arn

  input = jsonencode({
    source = "eventbridge"
  })
}
