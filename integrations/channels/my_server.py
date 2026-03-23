from fastmcp import FastMCP
import sys
import os
from fastmcp.server.auth import JWTVerifier
from fastmcp.server.auth.providers.jwt import RSAKeyPair
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import all integration functions
from integrations.channels import gmail, google_calender, google_docs, google_drive, google_meet, google_sheets, google_tasks


mcp = FastMCP("Google Workspace MCP Server 🚀")


@mcp.tool
def gmail_list_messages(db_user_id: int = 1, max_results: int = 10, query: str = "") -> dict:
    """List messages from Gmail inbox"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = gmail.get_service(db_user_id, db)
        return {"messages": gmail.list_messages(service, max_results=max_results, query=query)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def gmail_get_message(message_id: str, db_user_id: int = 1) -> dict:
    """Get a specific Gmail message by ID with full content"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = gmail.get_service(db_user_id, db)
        message = gmail.get_message(service, message_id)
        if message:
            return gmail.get_message_content(message)
        return {"error": "Message not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def gmail_send_email(to: str, subject: str, body: str, db_user_id: int = 1, is_html: bool = False) -> dict:
    """Send an email via Gmail"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = gmail.get_service(db_user_id, db)
        result = gmail.send_email(service, to, subject, body, is_html=is_html)
        if result:
            return {"success": True, "message_id": result.get("id")}
        return {"error": "Failed to send email"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def gmail_delete_message(message_id: str, db_user_id: int = 1) -> dict:
    """Delete a Gmail message by ID"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = gmail.get_service(db_user_id, db)
        success = gmail.delete_message(service, message_id)
        return {"success": success}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def gmail_mark_as_read(message_id: str, db_user_id: int = 1) -> dict:
    """Mark a Gmail message as read"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = gmail.get_service(db_user_id, db)
        result = gmail.mark_as_read(service, message_id)
        return {"success": result is not None}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def gmail_mark_as_unread(message_id: str, db_user_id: int = 1) -> dict:
    """Mark a Gmail message as unread"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = gmail.get_service(db_user_id, db)
        result = gmail.mark_as_unread(service, message_id)
        return {"success": result is not None}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# ============================================================================
# Google Calendar Tools
# ============================================================================

@mcp.tool
def calendar_list_events(db_user_id: int = 1, max_results: int = 10) -> dict:
    """List upcoming calendar events"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_calender.get_service(db_user_id, db)
        return {"events": google_calender.list_events(service, max_results=max_results)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def calendar_create_event(summary: str, start_time: str, end_time: str, description: str = "", db_user_id: int = 1) -> dict:
    """Create a calendar event with custom title, start time, end time, and description. Times should be in ISO format (e.g., '2024-03-23T19:45:00')"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_calender.get_service(db_user_id, db)
        event = google_calender.create_event_dynamic(service, summary, start_time, end_time, description)
        return {"success": True, "event": event}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# ============================================================================
# Google Docs Tools
# ============================================================================

@mcp.tool
def docs_create_document(title: str = "Untitled Document", db_user_id: int = 1) -> dict:
    """Create a new Google Doc"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_docs.get_service(db_user_id, db)
        return google_docs.create_document(service, title)
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def docs_get_document(document_id: str, db_user_id: int = 1) -> dict:
    """Get Google Doc content by ID"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_docs.get_service(db_user_id, db)
        doc = google_docs.get_document(service, document_id)
        if doc:
            return google_docs.get_document_content(doc)
        return {"error": "Document not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def docs_insert_text(document_id: str, text: str, index: int = 1, db_user_id: int = 1) -> dict:
    """Insert text into a Google Doc"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_docs.get_service(db_user_id, db)
        result = google_docs.insert_text(service, document_id, text, index)
        return {"success": result is not None}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def docs_list_documents(max_results: int = 10, db_user_id: int = 1) -> dict:
    """List Google Docs"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        drive_service = google_docs.get_drive_service(db_user_id, db)
        return {"documents": google_docs.list_documents(drive_service, max_results)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# ============================================================================
# Google Drive Tools
# ============================================================================

@mcp.tool
def drive_list_files(page_size: int = 10, query: str = "", db_user_id: int = 1) -> dict:
    """List files in Google Drive"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_drive.get_service(db_user_id, db)
        return {"files": google_drive.list_files(service, page_size, query)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def drive_get_file(file_id: str, db_user_id: int = 1) -> dict:
    """Get file metadata by ID"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_drive.get_service(db_user_id, db)
        file = google_drive.get_file(service, file_id)
        return file if file else {"error": "File not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def drive_create_folder(name: str, parent_folder_id: str = None, db_user_id: int = 1) -> dict:
    """Create a folder in Google Drive"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_drive.get_service(db_user_id, db)
        folder = google_drive.create_folder(service, name, parent_folder_id)
        return folder if folder else {"error": "Failed to create folder"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def drive_delete_file(file_id: str, db_user_id: int = 1) -> dict:
    """Delete a file or folder by ID"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_drive.get_service(db_user_id, db)
        success = google_drive.delete_file(service, file_id)
        return {"success": success}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def drive_share_file(file_id: str, email: str, role: str = "reader", db_user_id: int = 1) -> dict:
    """Share a file with a user"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_drive.get_service(db_user_id, db)
        result = google_drive.share_file(service, file_id, email, role)
        return {"success": result is not None}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# ============================================================================
# Google Meet Tools
# ============================================================================

@mcp.tool
def meet_create_meeting_now(summary: str, duration_minutes: int = 30, attendees: list = None, db_user_id: int = 1) -> dict:
    """Create a Google Meet meeting starting now"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_meet.get_service(db_user_id, db)
        meeting = google_meet.create_meeting_now(service, summary, duration_minutes, attendees)
        return meeting if meeting else {"error": "Failed to create meeting"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def meet_list_meetings(max_results: int = 10, db_user_id: int = 1) -> dict:
    """List upcoming meetings with Meet links"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_meet.get_service(db_user_id, db)
        return {"meetings": google_meet.list_meetings(service, max_results=max_results)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def meet_delete_meeting(event_id: str, db_user_id: int = 1) -> dict:
    """Delete a meeting by ID"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_meet.get_service(db_user_id, db)
        success = google_meet.delete_meeting(service, event_id)
        return {"success": success}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# ============================================================================
# Google Sheets Tools
# ============================================================================

@mcp.tool
def sheets_create_spreadsheet(title: str = "Untitled Spreadsheet", db_user_id: int = 1) -> dict:
    """Create a new Google Spreadsheet"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_sheets.get_service(db_user_id, db)
        return google_sheets.create_spreadsheet(service, title)
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def sheets_read_range(spreadsheet_id: str, range_name: str, db_user_id: int = 1) -> dict:
    """Read data from a spreadsheet range"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_sheets.get_service(db_user_id, db)
        values = google_sheets.read_range(service, spreadsheet_id, range_name)
        return {"values": values}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def sheets_write_range(spreadsheet_id: str, range_name: str, values: list, db_user_id: int = 1) -> dict:
    """Write data to a spreadsheet range"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_sheets.get_service(db_user_id, db)
        result = google_sheets.write_range(service, spreadsheet_id, range_name, values)
        return {"success": result is not None}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def sheets_append_row(spreadsheet_id: str, range_name: str, values: list, db_user_id: int = 1) -> dict:
    """Append a row to a spreadsheet"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_sheets.get_service(db_user_id, db)
        result = google_sheets.append_row(service, spreadsheet_id, range_name, values)
        return {"success": result is not None}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# ============================================================================
# Google Tasks Tools
# ============================================================================

@mcp.tool
def tasks_list_task_lists(max_results: int = 10, db_user_id: int = 1) -> dict:
    """List task lists"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_tasks.get_service(db_user_id, db)
        return {"task_lists": google_tasks.list_task_lists(service, max_results)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def tasks_list_tasks(task_list_id: str = "@default", show_completed: bool = False, max_results: int = 100, db_user_id: int = 1) -> dict:
    """List tasks in a task list"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_tasks.get_service(db_user_id, db)
        return {"tasks": google_tasks.list_tasks(service, task_list_id, show_completed, max_results=max_results)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def tasks_create_task(title: str, notes: str = "", task_list_id: str = "@default", db_user_id: int = 1) -> dict:
    """Create a new task"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_tasks.get_service(db_user_id, db)
        task = google_tasks.create_task(service, task_list_id, title, notes)
        return task if task else {"error": "Failed to create task"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def tasks_delete_task(task_list_id: str, task_id: str, db_user_id: int = 1) -> dict:
    """Delete a task by ID"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_tasks.get_service(db_user_id, db)
        success = google_tasks.delete_task(service, task_list_id, task_id)
        return {"success": success}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

@mcp.tool
def tasks_update_task(task_list_id: str, task_id: str, title: str = None, notes: str = None, status: str = None, db_user_id: int = 1) -> dict:
    """Update a task"""
    from db.models import SessionLocal
    db = SessionLocal()
    try:
        service = google_tasks.get_service(db_user_id, db)
        task = google_tasks.update_task(service, task_list_id, task_id, title, notes, status=status)
        return task if task else {"error": "Failed to update task"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    #print(f"ARYAN-NOOB {access_token}")
    mcp.run(transport="http", port=8000)