import io
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Security, Depends
from fastapi.security.api_key import APIKeyHeader
import uvicorn
from typing import List, Annotated
from dotenv import load_dotenv
import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from ocr_service.bank_parsers.parser_factory import ParserFactory

load_dotenv()

APP_ENV = os.getenv("NODE_ENV", "production")
IS_DEBUG = APP_ENV == "development"

SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

header_name = os.getenv("API_KEY_HEADER", "X-API-Key")
api_key_header = APIKeyHeader(name=header_name, auto_error=True)


app = FastAPI(
    title="My Expense Tracker API",
    # ถ้าเป็น production จะกลายเป็น None (ปิดหน้า Docs ทันที)
    docs_url="/docs" if IS_DEBUG else None,
    redoc_url="/redoc" if IS_DEBUG else None,
    openapi_url="/openapi.json" if IS_DEBUG else None,
)
parser_factory = ParserFactory()


def get_google_creds():
    # 1. พยายามดึงจาก Environment Variable ก่อน (วิธีที่แนะนำสำหรับ Cloud)
    creds_json_str = os.getenv("GOOGLE_CREDS_JSON")

    if creds_json_str:
        try:
            # แปลงข้อความ JSON String กลับเป็น Dictionary
            creds_info = json.loads(creds_json_str)
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_info, SCOPES)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500, detail="Invalid GOOGLE_CREDS_JSON format"
            )

    # 2. ถ้าไม่มีใน Env ให้ลองหาจากไฟล์ (Fallback สำหรับรันในเครื่อง)
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        return ServiceAccountCredentials.from_json_keyfile_name(
            SERVICE_ACCOUNT_FILE, SCOPES
        )

    # 3. ถ้าไม่เจอทั้งสองที่ ให้แจ้ง Error
    raise HTTPException(
        status_code=500, detail="Google Credentials not found in ENV or File"
    )


async def get_api_key(api_key: str = Depends(api_key_header)):
    # เทียบค่าที่ส่งมากับค่าใน env
    if api_key == os.getenv("API_KEY_VALUE"):
        return api_key
    raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")


@app.post("/scan-slip", dependencies=[Depends(get_api_key)])
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
            raise HTTPException(
                status_code=422,
                detail={"file_name": file.filename, "error": str(e), "texts": texts},
            )

        # 5. Parse ข้อมูล Transaction
        transaction = parser.parse(texts)

        # 6. คืนค่ากลับเป็น JSON (FastAPI จะแปลง Object เป็น JSON ให้โดยอัตโนมัติ)
        return {"status": "success", "data": transaction}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/scan-multiple-slip", dependencies=[Depends(get_api_key)])
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


@app.post("/add-to-sheet", dependencies=[Depends(get_api_key)])
async def add_to_sheet(transactions: Annotated[list[list], Body()]):
    try:
        # 1. เชื่อมต่อและเลือก Sheet "Transaction"
        creds = get_google_creds()
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet("Transaction")

        # 2. ใช้ append_rows เพื่อส่งข้อมูลทั้งหมดทีเดียว
        sheet.append_rows(transactions, value_input_option="USER_ENTERED")

        return {
            "status": "success",
            "message": f"Added {len(transactions)} rows successfully",
            "data": transactions,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/scan-and-save-all", dependencies=[Depends(get_api_key)])
async def scan_and_save_all(upload_files: List[UploadFile] = File(..., alias="files")):
    try:
        # 1. เรียกใช้ฟังก์ชัน scan_multiple_slip ที่มีอยู่แล้ว
        # เราต้องส่ง upload_files เข้าไปตรงๆ
        scan_response = await scan_multiple_slip(upload_files)

        if scan_response["status"] != "success":
            raise HTTPException(status_code=500, detail="OCR Scanning failed")

        # 2. ดึงข้อมูลจากผลลัพธ์การสแกนมาเตรียมทำเป็น Row สำหรับ Google Sheets
        # scan_response["data"] จะเป็น list ของ transaction objects
        transactions_to_save = []
        for item in scan_response["data"]:
            # สร้าง List ของข้อมูล 1 แถว (ใส่ "" นำหน้าสำหรับคอลัมน์ A)
            row = [
                "",  # คอลัมน์ A (ว่าง)
                item.get("date"),
                item.get("type"),
                item.get("category"),
                item.get("amount"),
                item.get("description"),
            ]
            transactions_to_save.append(row)

        # 3. เรียกใช้ฟังก์ชัน add_to_sheet ที่มีอยู่แล้ว
        # โดยส่ง transactions_to_save (list of list) เข้าไป
        if transactions_to_save:
            sheet_response = await add_to_sheet(transactions_to_save)

            return {
                "status": "success",
                "ocr_count": len(scan_response["data"]),
                "sheet_message": sheet_response["message"],
                "details": scan_response["data"],
            }
        else:
            return {"status": "warning", "message": "No valid data found to save"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Integrated Process Error: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
