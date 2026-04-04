import io
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
import uvicorn
from typing import List, Annotated
from dotenv import load_dotenv
import os

# from google.oauth2 import service_account
# from googleapiclient.discovery import build

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from ocr_service.bank_parsers.parser_factory import ParserFactory

load_dotenv()

SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

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
        texts = pytesseract.image_to_string(img, lang="tha+eng").splitlines()
        texts = [text for text in texts if text.strip() != ""]

        # 4. ใช้ Parser Factory ค้นหา Parser ที่เหมาะสม
        try:
            parser = parser_factory.get_parser(texts)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))

        # 5. Parse ข้อมูล Transaction
        transaction = parser.parse(texts)

        # 6. คืนค่ากลับเป็น JSON (FastAPI จะแปลง Object เป็น JSON ให้โดยอัตโนมัติ)
        return {"status": "success", "data": transaction}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/scan-multiple-slip")
async def scan_multiple_slip(upload_files: List[UploadFile] = File(..., alias="files")):
    results = []

    try:
        for file in upload_files:
            # สำคัญมาก: หากฟังก์ชัน scan_slip มีการ .read() ไปแล้ว
            # ต้องมั่นใจว่า cursor อยู่ที่ 0 ก่อนเสมอ
            await file.seek(0)

            result = await scan_slip(file)
            results.append(result)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/add-to-sheet")
async def add_to_sheet(transactions: Annotated[list[list], Body()]):
    try:
        # 1. เชื่อมต่อและเลือก Sheet "Transaction"
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet("Transaction")

        # 2. ใช้ append_rows เพื่อส่งข้อมูลทั้งหมดทีเดียว
        sheet.append_rows(transactions, value_input_option='USER_ENTERED')

        return {
            "status": "success",
            "message": f"Added {len(transactions)} rows successfully",
            "data": transactions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
