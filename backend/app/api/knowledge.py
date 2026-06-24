import os
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from api.auth import get_current_user
from models.uploaded_file import UploadedFile
from services.qdrant_service import QdrantService
from src.models.db_models import AuditLog

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# Upload directories
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploaded_documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("Policies"),
    allowed_roles: str = Form("all"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload and index organizational documents. Only HR, Admins, and Reporting Managers are allowed.
    """
    user_role = current_user.get("role", "Employee")
    if user_role not in ["HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only HR is authorized to upload organizational documents."
        )

    # 1. Save local file copy
    filename = file.filename
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Clean roles list
    roles_list = [r.strip() for r in allowed_roles.split(",") if r.strip()]
    if not roles_list:
        roles_list = ["all"]

    # 2. Index in Qdrant
    index_res = await QdrantService.index_document(
        filename=filename,
        filepath=filepath,
        category=category,
        uploaded_by=current_user.get("email", "unknown"),
        allowed_roles=roles_list
    )

    if index_res["status"] == "error":
        # Cleanup file if indexing failed
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=index_res["message"]
        )

    # 3. Store record in DB
    try:
        db_file = UploadedFile(
            filename=filename,
            filepath=filepath,
            category=category,
            uploaded_by=current_user.get("email", "unknown"),
            allowed_roles=",".join(roles_list),
            version=1
        )
        db.add(db_file)
        
        # Audit log
        audit = AuditLog(
            action="KNOWLEDGE_DOCUMENT_UPLOAD",
            agent="knowledge_service",
            status="SUCCESS",
            details=f"User {current_user.get('email')} uploaded {filename} for category {category} with access roles: {allowed_roles}."
        )
        db.add(audit)
        await db.commit()
    except Exception as e:
        # Cleanup on DB error
        await QdrantService.delete_document(filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record upload in database: {str(e)}"
        )

    return {
        "message": f"Document '{filename}' successfully uploaded and indexed.",
        "category": category,
        "allowed_roles": roles_list,
        "chunks_count": index_res["chunks_count"]
    }

@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Lists all uploaded knowledge base files."""
    user_role = current_user.get("role", "Employee")
    
    # Non-HR/Managers get filtered list or only standard policies
    stmt = select(UploadedFile)
    res = await db.execute(stmt)
    files = res.scalars().all()
    
    formatted = []
    for f in files:
        # Filter for role-based view visibility in document directory
        allowed_roles_list = [r.strip() for r in (f.allowed_roles or "all").split(",") if r.strip()]
        if user_role != "HR" and "all" not in allowed_roles_list and user_role not in allowed_roles_list:
            continue
            
        formatted.append({
            "id": f.id,
            "filename": f.filename,
            "category": f.category,
            "uploaded_by": f.uploaded_by,
            "allowed_roles": allowed_roles_list,
            "uploaded_at": str(f.uploaded_at),
            "version": f.version
        })
    return formatted

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Deletes a document from Qdrant vector store and SQLite."""
    user_role = current_user.get("role", "Employee")
    if user_role not in ["HR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only HR is authorized to delete documents."
        )
        
    stmt = select(UploadedFile).where(UploadedFile.id == doc_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )
        
    filename = doc.filename
    filepath = doc.filepath
    
    # Delete from Qdrant
    await QdrantService.delete_document(filename)
    
    # Delete file from local storage
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass
            
    # Delete from DB
    await db.delete(doc)
    
    # Audit log
    audit = AuditLog(
        action="KNOWLEDGE_DOCUMENT_DELETE",
        agent="knowledge_service",
        status="SUCCESS",
        details=f"User {current_user.get('email')} deleted document {filename}."
    )
    db.add(audit)
    await db.commit()
    
    return {"message": f"Document '{filename}' successfully deleted."}
