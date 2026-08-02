"""
sheets_helper.py
Module hỗ trợ đọc/ghi Google Sheet mẫu bằng Service Account.
Dùng trong Flask app: from sheets_helper import get_sheet_data, update_sheet_data
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ID của file Google Sheet mẫu (lấy từ URL của Sheet)
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")

# Quyền truy cập cần thiết
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_service():
    """Khởi tạo kết nối tới Google Sheets API bằng Service Account."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError(
            "Chưa cấu hình biến môi trường GOOGLE_CREDENTIALS_JSON. "
            "Vào Render/Railway > Environment > thêm biến này, "
            "giá trị là toàn bộ nội dung file JSON của Service Account."
        )

    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials)


def get_sheet_data(range_name="Sheet1"):
    """
    Đọc dữ liệu từ Sheet mẫu.
    range_name: tên sheet hoặc vùng cụ thể, VD: "Sheet1", "Sheet1!A1:D10"
    Trả về: list các list (mỗi dòng là 1 list các giá trị ô)
    """
    service = _get_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_name
    ).execute()
    return result.get("values", [])


def update_sheet_data(range_name, values):
    """
    Ghi/cập nhật dữ liệu vào Sheet mẫu.
    range_name: vùng cần ghi, VD: "Sheet1!A1"
    values: list các list, VD: [["Nguyễn Văn A", "Kế toán", "2024-01-01"]]
    """
    service = _get_service()
    sheet = service.spreadsheets()
    body = {"values": values}
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()
    return result


def append_sheet_data(range_name, values):
    """
    Thêm dòng mới vào cuối Sheet (không ghi đè dữ liệu cũ).
    range_name: VD: "Sheet1" (Google tự tìm dòng trống tiếp theo)
    values: list các list, VD: [["Nguyễn Văn A", "Kế toán", "2024-01-01"]]
    """
    service = _get_service()
    sheet = service.spreadsheets()
    body = {"values": values}
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    return result
