locals {
  pipeline_definition = replace(
    replace(
      file("${path.module}/../stepfunctions/pipeline.asl.json"),
      "$${scrape_lambda_arn}",
      aws_lambda_function.scrape.arn
    ),
    "$${process_lambda_arn}",
    aws_lambda_function.process.arn
  )
}

resource "aws_sfn_state_machine" "pipeline" {
  name     = "${local.name_prefix}-pipeline"
  role_arn = aws_iam_role.step_functions.arn

  definition = local.pipeline_definition

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  depends_on = [aws_cloudwatch_log_resource_policy.sfn]
}
