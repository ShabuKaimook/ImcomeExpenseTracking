import io
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
import uvicorn

from ocr_service.bank_parsers.parser_factory import ParserFactory

app = FastAPI()
parser_factory = ParserFactory()

@app.post("/scan-slip")
async def scan_slip(file: UploadFile = File(...)):
    # 1. ตรวจสอบว่าเป็นไฟล์รูปภาพหรือไม่
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image")

    try:
        # 2. อ่านข้อมูลจากไฟล์ที่ Upload เข้ามา
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # 3. ประมวลผล OCR (เหมือนโค้ดเดิมของคุณ)
        texts = pytesseract.image_to_string(img, lang='tha+eng').splitlines()
        texts = [text for text in texts if text.strip() != '']

        # 4. ใช้ Parser Factory ค้นหา Parser ที่เหมาะสม
        try:
            parser = parser_factory.get_parser(texts)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))

        # 5. Parse ข้อมูล Transaction
        transaction = parser.parse(texts)

        # 6. คืนค่ากลับเป็น JSON (FastAPI จะแปลง Object เป็น JSON ให้โดยอัตโนมัติ)
        return {
            "status": "success",
            "data": transaction
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)