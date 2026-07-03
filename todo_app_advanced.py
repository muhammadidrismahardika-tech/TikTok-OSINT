#!/usr/bin/env python3
"""
Enhanced To-Do List Application with Advanced Local Storage
Features: Categories, Priority, Due Dates, Search, Export, Import, Recurring Tasks
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum
import os
import sys


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('todo_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Priority(Enum):
    """Priority levels for todos"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

    def __str__(self):
        return self.name


class Recurrence(Enum):
    """Recurrence options for todos"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

    def __str__(self):
        return self.value


class TodoApp:
    """Enhanced to-do list application with advanced features"""

    def __init__(self, storage_file: str = "todos.json", backup_enabled: bool = True):
        """
        Initialize the TodoApp
        
        Args:
            storage_file: Path to JSON file for storing todos
            backup_enabled: Whether to create automatic backups
        """
        self.storage_file = Path(storage_file)
        self.backup_enabled = backup_enabled
        self.backup_dir = Path("backups")
        
        if backup_enabled:
            self.backup_dir.mkdir(exist_ok=True)
        
        self.todos = self._load_todos()
        logger.info(f"TodoApp initialized with {len(self.todos)} todos")

    def _load_todos(self) -> List[Dict]:
        """
        Load todos from local storage with validation
        
        Returns:
            List of todo dictionaries
        """
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    todos = json.load(f)
                    logger.info(f"Loaded {len(todos)} todos from storage")
                    return todos
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            self._recover_from_backup()
            return []
        except IOError as e:
            logger.error(f"Error loading todos: {e}")
            return []

    def _recover_from_backup(self) -> None:
        """Recover from the latest backup if main file is corrupted"""
        if not self.backup_dir.exists():
            return

        backups = sorted(self.backup_dir.glob("todos_backup_*.json"), reverse=True)
        if backups:
            try:
                with open(backups[0], 'r', encoding='utf-8') as f:
                    recovered = json.load(f)
                logger.info(f"Recovered {len(recovered)} todos from backup: {backups[0]}")
                self.todos = recovered
            except Exception as e:
                logger.error(f"Failed to recover from backup: {e}")

    def _save_todos(self, create_backup: bool = True) -> bool:
        """
        Save todos to local storage with optional backup
        
        Args:
            create_backup: Whether to create a backup before saving
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup before saving
            if create_backup and self.backup_enabled and self.storage_file.exists():
                backup_file = self.backup_dir / f"todos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        backup_data = f.read()
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(backup_data)
                    # Keep only last 10 backups
                    self._cleanup_old_backups()
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")

            # Save main file
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.todos, f, indent=2, ensure_ascii=False)
            logger.info("Todos saved successfully")
            return True
        except IOError as e:
            logger.error(f"Error saving todos: {e}")
            return False

    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """Remove old backup files, keeping only the most recent ones"""
        backups = sorted(self.backup_dir.glob("todos_backup_*.json"), reverse=True)
        for old_backup in backups[keep:]:
            try:
                old_backup.unlink()
                logger.debug(f"Deleted old backup: {old_backup}")
            except Exception as e:
                logger.warning(f"Failed to delete old backup: {e}")

    def add_todo(
        self,
        title: str,
        description: str = "",
        category: str = "General",
        priority: Priority = Priority.MEDIUM,
        due_date: Optional[str] = None,
        recurrence: Recurrence = Recurrence.NONE
    ) -> bool:
        """
        Add a new todo item with enhanced features
        
        Args:
            title: The title of the todo
            description: Optional description
            category: Category for organizing todos
            priority: Priority level
            due_date: Due date in YYYY-MM-DD format
            recurrence: Recurrence pattern
            
        Returns:
            True if successful, False otherwise
        """
        if not title.strip():
            logger.warning("Attempted to add todo with empty title")
            print("❌ Error: Todo title cannot be empty")
            return False

        # Validate due date
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid due date format: {due_date}")
                print("❌ Error: Invalid due date format. Use YYYY-MM-DD")
                return False

        todo = {
            "id": self._generate_id(),
            "title": title.strip(),
            "description": description.strip(),
            "category": category.strip(),
            "priority": priority.value if isinstance(priority, Priority) else priority,
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "due_date": due_date,
            "recurrence": recurrence.value if isinstance(recurrence, Recurrence) else recurrence,
            "tags": []
        }

        self.todos.append(todo)
        logger.info(f"Added todo: {title}")
        return self._save_todos()

    def _generate_id(self) -> int:
        """Generate a unique ID for a new todo"""
        return max([t["id"] for t in self.todos], default=0) + 1

    def list_todos(
        self,
        show_completed: bool = True,
        category: Optional[str] = None,
        priority: Optional[Priority] = None,
        sort_by: str = "due_date"
    ) -> None:
        """
        Display todos with advanced filtering and sorting
        
        Args:
            show_completed: Whether to show completed todos
            category: Filter by category
            priority: Filter by priority
            sort_by: Sort by 'due_date', 'priority', 'created_at'
        """
        if not self.todos:
            print("✨ No todos found!")
            return

        # Filter todos
        filtered = self.todos
        if not show_completed:
            filtered = [t for t in filtered if not t["completed"]]
        if category:
            filtered = [t for t in filtered if t.get("category", "General") == category]
        if priority:
            filtered = [t for t in filtered if t.get("priority") == priority.value]

        if not filtered:
            print("✨ No todos match your criteria!")
            return

        # Sort todos
        if sort_by == "due_date":
            filtered = sorted(
                filtered,
                key=lambda x: (x.get("due_date") is None, x.get("due_date") or "")
            )
        elif sort_by == "priority":
            filtered = sorted(filtered, key=lambda x: -x.get("priority", 0))
        elif sort_by == "created_at":
            filtered = sorted(filtered, key=lambda x: x.get("created_at", ""))

        print("\n" + "=" * 120)
        print(f"{'ID':<4} {'Status':<8} {'Priority':<8} {'Title':<25} {'Category':<12} {'Due Date':<12} {'Created':<12}")
        print("=" * 120)

        for todo in filtered:
            status = "✓" if todo["completed"] else "○"
            priority_val = todo.get("priority", 2)
            priority_str = [p.name for p in Priority if p.value == priority_val][0] if priority_val in [p.value for p in Priority] else "MEDIUM"
            category = todo.get("category", "General")
            due_date = todo.get("due_date", "-")
            created = datetime.fromisoformat(todo["created_at"]).strftime("%Y-%m-%d")
            title = todo["title"][:25]
            
            print(f"{todo['id']:<4} {status:<8} {priority_str:<8} {title:<25} {category:<12} {due_date:<12} {created:<12}")

        print("=" * 120)
        print(f"\n📊 Showing {len(filtered)} of {len(self.todos)} todos\n")

    def mark_complete(self, todo_id: int) -> bool:
        """Mark a todo as completed"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["completed"] = True
                todo["completed_at"] = datetime.now().isoformat()
                logger.info(f"Marked todo '{todo['title']}' as complete")
                print(f"✓ Marked '{todo['title']}' as complete")
                return self._save_todos()

        logger.warning(f"Todo with ID {todo_id} not found")
        print(f"❌ Error: Todo with ID {todo_id} not found")
        return False

    def mark_incomplete(self, todo_id: int) -> bool:
        """Mark a todo as incomplete"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["completed"] = False
                todo["completed_at"] = None
                logger.info(f"Marked todo '{todo['title']}' as incomplete")
                print(f"○ Marked '{todo['title']}' as incomplete")
                return self._save_todos()

        logger.warning(f"Todo with ID {todo_id} not found")
        print(f"❌ Error: Todo with ID {todo_id} not found")
        return False

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item"""
        for i, todo in enumerate(self.todos):
            if todo["id"] == todo_id:
                title = todo["title"]
                self.todos.pop(i)
                logger.info(f"Deleted todo: {title}")
                print(f"✗ Deleted '{title}'")
                return self._save_todos()

        logger.warning(f"Todo with ID {todo_id} not found")
        print(f"❌ Error: Todo with ID {todo_id} not found")
        return False

    def update_todo(
        self,
        todo_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[Priority] = None,
        due_date: Optional[str] = None
    ) -> bool:
        """Update a todo item"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                if title:
                    todo["title"] = title.strip()
                if description is not None:
                    todo["description"] = description.strip()
                if category:
                    todo["category"] = category.strip()
                if priority:
                    todo["priority"] = priority.value if isinstance(priority, Priority) else priority
                if due_date:
                    try:
                        datetime.strptime(due_date, "%Y-%m-%d")
                        todo["due_date"] = due_date
                    except ValueError:
                        print("❌ Invalid due date format. Use YYYY-MM-DD")
                        return False
                
                logger.info(f"Updated todo ID {todo_id}")
                print(f"✓ Updated todo ID {todo_id}")
                return self._save_todos()

        logger.warning(f"Todo with ID {todo_id} not found")
        print(f"❌ Error: Todo with ID {todo_id} not found")
        return False

    def search_todos(self, query: str) -> None:
        """Search todos by title or description"""
        query_lower = query.lower()
        results = [
            t for t in self.todos
            if query_lower in t["title"].lower() or query_lower in t.get("description", "").lower()
        ]

        if not results:
            print(f"✨ No todos found matching '{query}'")
            return

        print(f"\n🔍 Found {len(results)} todo(s) matching '{query}':\n")
        for todo in results:
            status = "✓" if todo["completed"] else "○"
            print(f"[{todo['id']}] {status} {todo['title']}")
            if todo.get("description"):
                print(f"    {todo['description']}")
        print()

    def get_stats(self) -> Dict:
        """Get comprehensive statistics about todos"""
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t["completed"])
        pending = total - completed
        overdue = sum(
            1 for t in self.todos
            if not t["completed"] and t.get("due_date")
            and datetime.fromisoformat(t["due_date"]).date() < datetime.now().date()
        )
        
        categories = {}
        for todo in self.todos:
            cat = todo.get("category", "General")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_percentage": (completed / total * 100) if total > 0 else 0,
            "categories": categories
        }

    def display_stats(self) -> None:
        """Display comprehensive statistics"""
        stats = self.get_stats()
        print("\n" + "=" * 50)
        print("📊 TODO STATISTICS")
        print("=" * 50)
        print(f"Total todos:        {stats['total']}")
        print(f"Completed:          {stats['completed']}")
        print(f"Pending:            {stats['pending']}")
        print(f"Overdue:            {stats['overdue']}")
        print(f"Completion:         {stats['completion_percentage']:.1f}%")
        print("\n📁 By Category:")
        for cat, count in stats['categories'].items():
            print(f"  {cat}: {count}")
        print("=" * 50 + "\n")

    def export_to_csv(self, filename: str = "todos_export.csv") -> bool:
        """Export todos to CSV file"""
        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id", "title", "description", "category", "priority", "completed", "due_date", "created_at"]
                )
                writer.writeheader()
                writer.writerows(self.todos)
            logger.info(f"Exported {len(self.todos)} todos to {filename}")
            print(f"✓ Exported {len(self.todos)} todos to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to export todos: {e}")
            print(f"❌ Failed to export todos: {e}")
            return False

    def import_from_csv(self, filename: str) -> bool:
        """Import todos from CSV file"""
        try:
            import csv
            imported = 0
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip if todo with same title already exists
                    if any(t["title"] == row["title"] for t in self.todos):
                        continue
                    
                    row["id"] = self._generate_id()
                    row["completed"] = row.get("completed", "").lower() == "true"
                    self.todos.append(row)
                    imported += 1
            
            if imported > 0:
                self._save_todos()
                logger.info(f"Imported {imported} todos from {filename}")
                print(f"✓ Imported {imported} todos from {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to import todos: {e}")
            print(f"❌ Failed to import todos: {e}")
            return False

    def get_due_today(self) -> List[Dict]:
        """Get todos due today"""
        today = datetime.now().date()
        return [
            t for t in self.todos
            if not t["completed"] and t.get("due_date")
            and datetime.fromisoformat(t["due_date"]).date() == today
        ]

    def get_overdue(self) -> List[Dict]:
        """Get overdue todos"""
        today = datetime.now().date()
        return [
            t for t in self.todos
            if not t["completed"] and t.get("due_date")
            and datetime.fromisoformat(t["due_date"]).date() < today
        ]


def display_menu() -> None:
    """Display the main menu"""
    print("\n" + "=" * 50)
    print("📝 ADVANCED TO-DO LIST APPLICATION")
    print("=" * 50)
    print("1.  Add a new todo")
    print("2.  View all todos")
    print("3.  View todos by category")
    print("4.  Search todos")
    print("5.  Mark todo as complete")
    print("6.  Mark todo as incomplete")
    print("7.  Update a todo")
    print("8.  Delete a todo")
    print("9.  View statistics")
    print("10. View due today")
    print("11. View overdue")
    print("12. Export to CSV")
    print("13. Import from CSV")
    print("14. Exit")
    print("=" * 50)


def main():
    """Main function to run the advanced to-do list application"""
    app = TodoApp()
    
    logger.info("Application started")

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-14): ").strip()

            if choice == "1":
                title = input("Enter todo title: ").strip()
                if title:
                    description = input("Enter todo description (optional): ").strip()
                    category = input("Enter category (default: General): ").strip() or "General"
                    priority_input = input("Enter priority (1=LOW, 2=MEDIUM, 3=HIGH, 4=URGENT, default: 2): ").strip() or "2"
                    due_date = input("Enter due date (YYYY-MM-DD, optional): ").strip() or None
                    
                    try:
                        priority = Priority(int(priority_input))
                    except (ValueError, KeyError):
                        priority = Priority.MEDIUM
                    
                    if app.add_todo(title, description, category, priority, due_date):
                        print("✓ Todo added successfully!")
                    else:
                        print("❌ Failed to add todo")

            elif choice == "2":
                sort_choice = input("Sort by (1=Due Date, 2=Priority, 3=Created Date, default: 1): ").strip() or "1"
                sort_map = {"1": "due_date", "2": "priority", "3": "created_at"}
                app.list_todos(sort_by=sort_map.get(sort_choice, "due_date"))

            elif choice == "3":
                stats = app.get_stats()
                categories = list(stats["categories"].keys())
                print("\nAvailable categories:")
                for i, cat in enumerate(categories, 1):
                    print(f"{i}. {cat}")
                cat_choice = input("Select category (number): ").strip()
                try:
                    selected = categories[int(cat_choice) - 1]
                    app.list_todos(category=selected)
                except (ValueError, IndexError):
                    print("❌ Invalid selection")

            elif choice == "4":
                query = input("Enter search query: ").strip()
                if query:
                    app.search_todos(query)

            elif choice == "5":
                try:
                    todo_id = int(input("Enter todo ID to mark as complete: "))
                    app.mark_complete(todo_id)
                except ValueError:
                    print("❌ Error: Invalid ID format")

            elif choice == "6":
                try:
                    todo_id = int(input("Enter todo ID to mark as incomplete: "))
                    app.mark_incomplete(todo_id)
                except ValueError:
                    print("❌ Error: Invalid ID format")

            elif choice == "7":
                try:
                    todo_id = int(input("Enter todo ID to update: "))
                    title = input("Enter new title (press Enter to skip): ").strip()
                    description = input("Enter new description (press Enter to skip): ").strip()
                    category = input("Enter new category (press Enter to skip): ").strip()
                    priority_input = input("Enter new priority (1-4, press Enter to skip): ").strip()
                    due_date = input("Enter new due date (YYYY-MM-DD, press Enter to skip): ").strip()
                    
                    priority = None
                    if priority_input:
                        try:
                            priority = Priority(int(priority_input))
                        except (ValueError, KeyError):
                            pass
                    
                    if title or description or category or priority or due_date:
                        app.update_todo(todo_id, title or None, description or None, category or None, priority, due_date or None)
                    else:
                        print("ℹ️  No changes made")
                except ValueError:
                    print("❌ Error: Invalid ID format")

            elif choice == "8":
                try:
                    todo_id = int(input("Enter todo ID to delete: "))
                    if input("Are you sure? (y/n): ").lower() == "y":
                        app.delete_todo(todo_id)
                except ValueError:
                    print("❌ Error: Invalid ID format")

            elif choice == "9":
                app.display_stats()

            elif choice == "10":
                due_today = app.get_due_today()
                if due_today:
                    print(f"\n📅 {len(due_today)} todo(s) due today:\n")
                    for todo in due_today:
                        print(f"[{todo['id']}] {todo['title']}")
                else:
                    print("\n✨ No todos due today!")

            elif choice == "11":
                overdue = app.get_overdue()
                if overdue:
                    print(f"\n⚠️  {len(overdue)} overdue todo(s):\n")
                    for todo in overdue:
                        print(f"[{todo['id']}] {todo['title']} (Due: {todo['due_date']})")
                else:
                    print("\n✓ No overdue todos!")

            elif choice == "12":
                filename = input("Enter export filename (default: todos_export.csv): ").strip() or "todos_export.csv"
                app.export_to_csv(filename)

            elif choice == "13":
                filename = input("Enter import filename: ").strip()
                if filename:
                    app.import_from_csv(filename)

            elif choice == "14":
                print("\n👋 Goodbye! Have a productive day!\n")
                logger.info("Application closed")
                break

            else:
                print("❌ Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\n👋 Application interrupted")
            logger.info("Application interrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
