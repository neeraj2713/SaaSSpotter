locals {
  name_prefix = "${var.project_name}-${var.environment}"

  state_machine_arn = "arn:aws:states:${var.aws_region}:${data.aws_caller_identity.current.account_id}:stateMachine:${local.name_prefix}-pipeline"

  lambda_env = {
    MONGODB_URI                     = var.mongodb_uri
    MONGODB_DB_NAME                 = "dev"
    GEMINI_API_KEY                  = var.gemini_api_key
    GEMINI_MODEL                    = "gemini-2.0-flash"
    FIRECRAWL_API_KEY               = var.firecrawl_api_key
    CORS_ORIGINS                    = var.cors_origins
    ADMIN_API_KEY                   = var.admin_api_key
    AWS_SECRETS_MANAGER_SECRET_NAME = aws_secretsmanager_secret.app.name
    STEP_FUNCTIONS_STATE_MACHINE_ARN = local.state_machine_arn
    SCRAPE_TARGETS                  = "reddit.com/r/Entrepreneur,reddit.com/r/SaaS,reddit.com/r/startups,reddit.com/r/smallbusiness"
    SCRAPE_KEYWORDS                 = "frustrated,struggling,wish there was,problem with,how do you handle,any tool for"
    SCRAPE_POST_LIMIT               = "50"
    LOCAL_PIPELINE_MODE             = "false"
  }
}

resource "aws_lambda_layer_version" "dependencies" {
  layer_name          = "${local.name_prefix}-deps"
  filename            = var.lambda_layer_zip_path
  compatible_runtimes = ["python3.11"]
  source_code_hash    = fileexists(var.lambda_layer_zip_path) ? filebase64sha256(var.lambda_layer_zip_path) : null
}

resource "aws_lambda_function" "api" {
  function_name = "${local.name_prefix}-api"
  role          = aws_iam_role.api_lambda.arn
  handler       = "app.handlers.api_handler.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256
  filename      = var.lambda_zip_path
  source_code_hash = fileexists(var.lambda_zip_path) ? filebase64sha256(var.lambda_zip_path) : null
  layers        = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = local.lambda_env
  }

  depends_on = [aws_cloudwatch_log_group.api_lambda]
}

resource "aws_lambda_function" "scrape" {
  function_name = "${local.name_prefix}-scrape"
  role          = aws_iam_role.worker_lambda.arn
  handler       = "app.handlers.scrape_handler.handler"
  runtime       = "python3.11"
  timeout       = 300
  memory_size   = 512
  filename      = var.lambda_zip_path
  source_code_hash = fileexists(var.lambda_zip_path) ? filebase64sha256(var.lambda_zip_path) : null
  layers        = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = local.lambda_env
  }

  depends_on = [aws_cloudwatch_log_group.scrape_lambda]
}

resource "aws_lambda_function" "process" {
  function_name = "${local.name_prefix}-process"
  role          = aws_iam_role.worker_lambda.arn
  handler       = "app.handlers.process_handler.handler"
  runtime       = "python3.11"
  timeout       = 120
  memory_size   = 512
  filename      = var.lambda_zip_path
  source_code_hash = fileexists(var.lambda_zip_path) ? filebase64sha256(var.lambda_zip_path) : null
  layers        = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = local.lambda_env
  }

  depends_on = [aws_cloudwatch_log_group.process_lambda]
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "sfn_scrape" {
  statement_id  = "AllowStepFunctionsInvokeScrape"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scrape.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.pipeline.arn
}

resource "aws_lambda_permission" "sfn_process" {
  statement_id  = "AllowStepFunctionsInvokeProcess"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.pipeline.arn
}
