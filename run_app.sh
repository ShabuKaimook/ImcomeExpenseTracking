docker build -t my-ocr-app .

docker run -d \
  --name ocr-container \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/credentials.json:/app/credentials.json \
  my-ocr-app