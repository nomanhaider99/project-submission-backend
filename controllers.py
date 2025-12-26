from database import connect_to_database
from models import Submission
from datetime import datetime
from fastapi import HTTPException, UploadFile
from bson import ObjectId
from pymongo import ReturnDocument
from typing import List
from dotenv import load_dotenv
from mailer import send_email_message
from drive import create_folder, get_folder_link, upload_uploadfile_to_folder
import os

load_dotenv()

db = connect_to_database()
submissions = db.get_collection("submissions")

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def submit_project(data=None, files: List[UploadFile] = None):
    try:
        if isinstance(data, Submission):
            group_data = data
        else:
            group_data = Submission.model_validate_json(data)

        if files:
            student_ids = "_".join([m.student_id for m in group_data.members])
            folder_name = f"Project_{student_ids}"

            folder_id = create_folder(folder_name)

            for file in files:
                upload_uploadfile_to_folder(file, folder_id)

            group_data.project_details.code_file_path = get_folder_link(folder_id)

        deadline = datetime(2025, 12, 28, 21, 0)
        if datetime.now() < deadline:
            group_data.marks += 5

        result = submissions.insert_one(group_data.model_dump())

        return {
            "message": "Project Submitted Successfully!",
            "id": str(result.inserted_id),
            "drive_folder": group_data.project_details.code_file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_submission_details(id: str):
    try:
        submission = submissions.find_one({"_id": ObjectId(id)})

        if not submission:
            raise HTTPException(status_code=404, detail="Submission Not Found")

        submission["_id"] = str(submission["_id"])

        return {
            "message": "Submission Retrieved Successfully!",
            "data": submission
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_all_submissions():
    try:
        submissions_list = list(submissions.find({}))

        if not submissions_list:
            raise HTTPException(status_code=404, detail="Submissions Not Found")

        for sub in submissions_list:
            sub["_id"] = str(sub["_id"])

        return {
            "message": "Submissions Retrieved Successfully!",
            "data": submissions_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def update_marks(id: str, marks: float):
    try:
        submission = submissions.find_one_and_update(
            {"_id": ObjectId(id)},
            {
                "$inc": {"marks": marks},
                "$set": {"status": "checked"}
            },
            return_document=ReturnDocument.AFTER
        )

        if not submission:
            raise HTTPException(status_code=404, detail="Submission Not Found")

        submission["_id"] = str(submission["_id"])

        # Email notification
        teacher_email = os.getenv("SIR_AMEEN_EMAIL")
        if teacher_email:
            send_email_message(
                teacher_email,
                "Project Submission Evaluated",
                submission
            )

        return {
            "message": "Marks Updated Successfully!",
            "data": submission
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
