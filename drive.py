import json
import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from fastapi import UploadFile

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

token_json = os.getenv("GOOGLE_TOKEN_JSON")
if not token_json:
    raise RuntimeError("GOOGLE_TOKEN_JSON not found")

creds = Credentials.from_authorized_user_info(
    info=json.loads(token_json),
    scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=creds)


def create_folder(folder_name: str) -> str:
    folder = drive_service.files().create(
        body={
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        },
        fields="id"
    ).execute()
    return folder["id"]


def upload_uploadfile_to_folder(file: UploadFile, folder_id: str):
    file.file.seek(0)

    media = MediaIoBaseUpload(
        io.BytesIO(file.file.read()),
        mimetype=file.content_type,
        resumable=True
    )

    drive_service.files().create(
        body={
            "name": file.filename,
            "parents": [folder_id]
        },
        media_body=media,
        fields="id"
    ).execute()


def get_folder_link(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"
