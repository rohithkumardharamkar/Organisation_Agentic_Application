import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db, SessionLocal
from api.auth import get_current_user
from schemas.chat import ChatRequest, ApprovalRequest
from services.langgraph_service import LanggraphService
from services.chat_service import ChatService
from models.session import Session
from sqlalchemy import select

router = APIRouter(prefix="/copilot", tags=["Copilot"])

@router.get("/history")
async def get_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_svc = ChatService(db)
    user_id = current_user["user_id"]
    
    # Get latest active thread for user
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if not sess:
        return []
        
    return await chat_svc.get_thread_history(user_id, sess.session_id)

@router.get("/status")
async def get_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user["user_id"]
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if not sess:
        return {"status": "COMPLETED"}
        
    from src.workflow.graph import get_graph_app
    graph_app = get_graph_app()
    if not graph_app:
        return {"status": "COMPLETED"}
        
    config = {"configurable": {"thread_id": sess.session_id}}
    state_desc = await graph_app.aget_state(config)
    
    if state_desc and state_desc.values and state_desc.values.get("approval_required"):
        return {"status": "PAUSED_FOR_APPROVAL"}
        
    return {"status": "COMPLETED"}


from src.agents.router import stream_callback_var

@router.post("/chat")
async def chat(
    req: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user["user_id"]
    user_role = current_user.get("role", "Employee")
    
    # Find latest active session or create new one (read-only query on request session)
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if sess:
        thread_id = sess.session_id
    else:
        import uuid
        thread_id = str(uuid.uuid4())
        
    async def event_generator():
        queue = asyncio.Queue()
        
        async def callback(token: str):
            await queue.put(token)
            
        token_ctx = stream_callback_var.set(callback)
        
        async def run_chat_task():
            async with SessionLocal() as task_db:
                # 1. Fetch or create Session record in the isolated task_db session
                stmt_sess = select(Session).where(Session.session_id == thread_id)
                res_sess = await task_db.execute(stmt_sess)
                task_sess = res_sess.scalar_one_or_none()
                if not task_sess:
                    task_sess = Session(session_id=thread_id, user_id=user_id)
                    task_db.add(task_sess)
                    await task_db.commit()
                
                # 2. Execute the agent invocation
                lang_svc = LanggraphService(task_db)
                res_data = await lang_svc.invoke_chat(req.message, user_id, thread_id, user_role)
                
                # 3. Update session timestamp
                task_sess.updated_at = task_sess.updated_at
                await task_db.commit()
                return res_data
                
        # Create task for graph execution
        task = asyncio.create_task(run_chat_task())
        
        try:
            yielded_content = False
            while not task.done() or not queue.empty():
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"
                    yielded_content = True
                    queue.task_done()
                except asyncio.TimeoutError:
                    continue
            
            res_data = await task
            
            # Flush any remaining items in queue
            while not queue.empty():
                chunk = await queue.get()
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"
                yielded_content = True
                queue.task_done()
                
            if not yielded_content and res_data.get("response"):
                yield f"data: {json.dumps({'type': 'content', 'delta': res_data['response']})}\n\n"
                
            meta = {k: v for k, v in res_data.items() if k != "response"}
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': meta})}\n\n"
            
        except Exception as e:
            print(f"Streaming error in chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'details': str(e)})}\n\n"
        finally:
            stream_callback_var.reset(token_ctx)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/approve")
async def approve(
    req: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    # Get latest active session for thread_id (read-only query on request session)
    stmt = select(Session).where(Session.user_id == user_id).order_by(Session.updated_at.desc()).limit(1)
    res = await db.execute(stmt)
    sess = res.scalar_one_or_none()
    
    if not sess:
        raise HTTPException(status_code=404, detail="No active session found for user.")
        
    thread_id = sess.session_id
    
    async def event_generator():
        queue = asyncio.Queue()
        
        async def callback(token: str):
            await queue.put(token)
            
        token_ctx = stream_callback_var.set(callback)
        
        async def run_approve_task():
            async with SessionLocal() as task_db:
                lang_svc = LanggraphService(task_db)
                res_data = await lang_svc.approve_action(thread_id, req.approve, user_id)
                return res_data
                
        task = asyncio.create_task(run_approve_task())
        
        try:
            while not task.done() or not queue.empty():
                try:
                    chunk = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"
                    queue.task_done()
                except asyncio.TimeoutError:
                    continue
                    
            res_data = await task
            
            while not queue.empty():
                chunk = await queue.get()
                yield f"data: {json.dumps({'type': 'content', 'delta': chunk})}\n\n"
                queue.task_done()
                
            meta = {k: v for k, v in res_data.items() if k != "response"}
            yield f"data: {json.dumps({'type': 'metadata', 'metadata': meta})}\n\n"
            
        except Exception as e:
            print(f"Streaming error in approve: {e}")
            yield f"data: {json.dumps({'type': 'error', 'details': str(e)})}\n\n"
        finally:
            stream_callback_var.reset(token_ctx)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
