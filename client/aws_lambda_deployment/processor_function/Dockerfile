# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules to /opt/python (Lambda layer location)
COPY shared /opt/python/shared

# Copy function code
COPY lambda_function.py ./

# Verify handler is available
RUN python -c "import lambda_function; print('Handler found:', hasattr(lambda_function, 'lambda_handler'))"

# Set the handler
CMD ["lambda_function.lambda_handler"]