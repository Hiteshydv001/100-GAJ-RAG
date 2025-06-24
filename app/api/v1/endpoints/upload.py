import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.settings import settings
from app.core.engine import clear_engine_cache

router = APIRouter()

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """
    Uploads a file to the data directory, deletes the on-disk cache,
    and clears the in-memory engine cache to force a rebuild on next startup.
    """
    try:
        file_path = os.path.join(settings.data_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Delete the persisted on-disk cache
        if os.path.exists(settings.cache_dir):
            print(f"Removing on-disk cache at {settings.cache_dir} to force rebuild.")
            shutil.rmtree(settings.cache_dir)
        
        # Invalidate the in-memory engine cache
        clear_engine_cache()

        return {
            "filename": file.filename,
            "message": "File uploaded and cache cleared. RAG engine will be rebuilt on the next startup or request."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )