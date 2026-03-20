import os
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from integrations.helpers import (
    get_channel, create_channel, check_credentials, 
    refresh_credentials, credentials_from_db, credentials_to_db, RefreshException
)
from db.models import Integrations

# Google Tasks API scope
SCOPES = ["https://www.googleapis.com/auth/tasks"]


def get_service(user_id: int, db: Session):
    """Authenticate and return Google Tasks service using database-backed credentials."""
    credentials_path = os.path.join(os.path.dirname(__file__), "credentials.json")
    
    # Get or create channel for this user
    channel = get_channel(Integrations.TASKS, user_id, db)
    
    if not channel:
        # First time - create channel
        channel = create_channel(Integrations.TASKS, user_id, db)
    
    creds = None
    
    # Try to load credentials from database
    if check_credentials(channel):
        try:
            creds = credentials_from_db(channel)
            
            # Check if credentials have all required scopes
            if creds and creds.scopes:
                required_scopes = set(SCOPES)
                actual_scopes = set(creds.scopes)
                if not required_scopes.issubset(actual_scopes):
                    creds = None
        except RefreshException:
            creds = None
    
    # Handle expired or invalid credentials
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds = refresh_credentials(channel, db)
            except RefreshException:
                creds = None
        else:
            creds = None
    
    # Need new authentication
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Store credentials in database
        credentials_to_db(creds, channel, db)

    return build("tasks", "v1", credentials=creds)


def list_task_lists(service, max_results=10):
    """
    List task lists.
    
    Args:
        service: Google Tasks service object
        max_results: Maximum number of task lists to return
    
    Returns:
        List of task list objects
    """
    try:
        results = service.tasklists().list(maxResults=max_results).execute()
        task_lists = results.get("items", [])
        return task_lists
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def create_task_list(service, title):
    """
    Create a new task list.
    
    Args:
        service: Google Tasks service object
        title: Title of the task list
    
    Returns:
        Task list object with ID and title
    """
    try:
        task_list = {"title": title}
        result = service.tasklists().insert(body=task_list).execute()
        return {
            "id": result.get("id"),
            "title": result.get("title"),
        }
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def get_task_list(service, task_list_id):
    """
    Get a task list by ID.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list
    
    Returns:
        Task list object
    """
    try:
        task_list = service.tasklists().get(tasklist=task_list_id).execute()
        return task_list
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def delete_task_list(service, task_list_id):
    """
    Delete a task list by ID.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        service.tasklists().delete(tasklist=task_list_id).execute()
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False


def list_tasks(service, task_list_id="@default", show_completed=False, show_deleted=False, max_results=100):
    """
    List tasks in a task list.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list (default: "@default" for default task list)
        show_completed: Whether to show completed tasks (default: False)
        show_deleted: Whether to show deleted tasks (default: False)
        max_results: Maximum number of tasks to return
    
    Returns:
        List of task objects
    """
    try:
        results = service.tasks().list(
            tasklist=task_list_id,
            showCompleted=show_completed,
            showDeleted=show_deleted,
            maxResults=max_results
        ).execute()
        tasks = results.get("items", [])
        return tasks
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def create_task(service, task_list_id="@default", title="", notes="", due_date=None, status="needsAction"):
    """
    Create a new task in a task list.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list (default: "@default")
        title: Title of the task
        notes: Notes/description for the task
        due_date: Due date in RFC 3339 format (e.g., "2024-01-15T10:00:00Z") or datetime object
        status: Task status ("needsAction" or "completed")
    
    Returns:
        Task object with ID and details
    """
    try:
        task = {
            "title": title,
            "notes": notes,
            "status": status,
        }
        
        if due_date:
            if isinstance(due_date, str):
                # If it's a string, use it directly
                task["due"] = due_date
            elif isinstance(due_date, datetime):
                # Convert datetime to RFC 3339 format
                task["due"] = due_date.isoformat() + "Z"
        
        result = service.tasks().insert(tasklist=task_list_id, body=task).execute()
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def get_task(service, task_list_id, task_id):
    """
    Get a task by ID.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list
        task_id: ID of the task
    
    Returns:
        Task object
    """
    try:
        task = service.tasks().get(tasklist=task_list_id, task=task_id).execute()
        return task
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def update_task(service, task_list_id, task_id, title=None, notes=None, due_date=None, status=None, completed=None):
    """
    Update a task.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list
        task_id: ID of the task to update
        title: New title (optional)
        notes: New notes (optional)
        due_date: New due date in RFC 3339 format or datetime object (optional)
        status: New status ("needsAction" or "completed") (optional)
        completed: Completion date in RFC 3339 format or datetime object (optional)
    
    Returns:
        Updated task object
    """
    try:
        # Get the existing task first
        task = service.tasks().get(tasklist=task_list_id, task=task_id).execute()
        
        # Update fields if provided
        if title is not None:
            task["title"] = title
        if notes is not None:
            task["notes"] = notes
        if due_date is not None:
            if isinstance(due_date, str):
                task["due"] = due_date
            elif isinstance(due_date, datetime):
                task["due"] = due_date.isoformat() + "Z"
        if status is not None:
            task["status"] = status
        if completed is not None:
            if isinstance(completed, str):
                task["completed"] = completed
            elif isinstance(completed, datetime):
                task["completed"] = completed.isoformat() + "Z"
        
        result = service.tasks().update(tasklist=task_list_id, task=task_id, body=task).execute()
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def delete_task(service, task_list_id, task_id):
    """
    Delete a task by ID.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list
        task_id: ID of the task to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        service.tasks().delete(tasklist=task_list_id, task=task_id).execute()
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False


def move_task(service, task_list_id, task_id, previous_task_id=None):
    """
    Move a task to a different position in the task list.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list
        task_id: ID of the task to move
        previous_task_id: ID of the task to move after (None to move to top)
    
    Returns:
        Updated task object
    """
    try:
        result = service.tasks().move(
            tasklist=task_list_id,
            task=task_id,
            previous=previous_task_id
        ).execute()
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def clear_completed_tasks(service, task_list_id):
    """
    Clear all completed tasks from a task list.
    
    Args:
        service: Google Tasks service object
        task_list_id: ID of the task list
    
    Returns:
        True if successful, False otherwise
    """
    try:
        service.tasks().clear(tasklist=task_list_id).execute()
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False


def main(user_id: int = 1, db: Session = None):
    """Example usage of Google Tasks functions."""
    if db is None:
        from db.models import SessionLocal
        db = SessionLocal()
    
    try:
        service = get_service(user_id, db)

        # 1. List task lists
        task_lists = list_task_lists(service)
        print(f"Found {len(task_lists)} task lists")
        for task_list in task_lists:
            print(f"- {task_list.get('title')} ({task_list.get('id')})")

        # 2. Create a new task list
        new_list = create_task_list(service, "Test Task List")
        if new_list:
            print(f"Created task list: {json.dumps(new_list, indent=2)}")

        # 3. List tasks in default list
        tasks = list_tasks(service)
        print(f"Found {len(tasks)} tasks in default list")

        # 4. Create a task
        if new_list:
            task = create_task(
                service,
                task_list_id=new_list["id"],
                title="Test Task",
                notes="This is a test task",
                status="needsAction"
            )
            if task:
                print(f"Created task: {json.dumps(task, indent=2)}")

    except HttpError as error:
        print("An error occurred:", error)
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    main()

