# Dockerfile for Multi-Model Luxembourg Legal Assistant Lambda
# Optimized for AWS Lambda container runtime with configurable model support

FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Lambda function code
COPY lambda_function.py ./

# Verify the handler exists and syntax is valid
RUN python -c "import lambda_function; print('Handler found:', hasattr(lambda_function, 'lambda_handler'))"

# Set the CMD to your handler (must match filename.function_name)  
CMD ["lambda_function.lambda_handler"]