#!/usr/bin/env python3
"""
To-Do List Application with Local Storage
Supports adding, viewing, marking complete, and deleting tasks
"""

import json
import os
from datetime import datetime
from pathlib import Path


class TodoApp:
    """A simple to-do list application with local storage functionality"""

    def __init__(self, storage_file: str = "todos.json"):
        """
        Initialize the TodoApp
        
        Args:
            storage_file: Path to JSON file for storing todos
        """
        self.storage_file = Path(storage_file)
        self.todos = self._load_todos()

    def _load_todos(self) -> list:
        """
        Load todos from local storage
        
        Returns:
            List of todo dictionaries
        """
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading todos: {e}")
            return []

    def _save_todos(self) -> bool:
        """
        Save todos to local storage
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.todos, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving todos: {e}")
            return False

    def add_todo(self, title: str, description: str = "") -> bool:
        """
        Add a new todo item
        
        Args:
            title: The title of the todo
            description: Optional description
            
        Returns:
            True if successful, False otherwise
        """
        if not title.strip():
            print("Error: Todo title cannot be empty")
            return False

        todo = {
            "id": len(self.todos) + 1,
            "title": title.strip(),
            "description": description.strip(),
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }

        self.todos.append(todo)
        return self._save_todos()

    def list_todos(self, show_completed: bool = True) -> None:
        """
        Display all todos in a formatted table
        
        Args:
            show_completed: Whether to show completed todos
        """
        if not self.todos:
            print("No todos found!")
            return

        todos_to_show = [t for t in self.todos if show_completed or not t["completed"]]

        if not todos_to_show:
            print("No pending todos found!")
            return

        print("\n" + "=" * 80)
        print(f"{'ID':<4} {'Status':<10} {'Title':<30} {'Description':<25} {'Created':<12}")
        print("=" * 80)

        for todo in todos_to_show:
            status = "✓ Done" if todo["completed"] else "○ Pending"
            created = datetime.fromisoformat(todo["created_at"]).strftime("%Y-%m-%d")
            print(f"{todo['id']:<4} {status:<10} {todo['title']:<30} {todo['description']:<25} {created:<12}")

        print("=" * 80 + "\n")

    def mark_complete(self, todo_id: int) -> bool:
        """
        Mark a todo as completed
        
        Args:
            todo_id: The ID of the todo to mark complete
            
        Returns:
            True if successful, False otherwise
        """
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["completed"] = True
                todo["completed_at"] = datetime.now().isoformat()
                print(f"✓ Marked '{todo['title']}' as complete")
                return self._save_todos()

        print(f"Error: Todo with ID {todo_id} not found")
        return False

    def mark_incomplete(self, todo_id: int) -> bool:
        """
        Mark a todo as incomplete
        
        Args:
            todo_id: The ID of the todo to mark incomplete
            
        Returns:
            True if successful, False otherwise
        """
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["completed"] = False
                todo["completed_at"] = None
                print(f"○ Marked '{todo['title']}' as incomplete")
                return self._save_todos()

        print(f"Error: Todo with ID {todo_id} not found")
        return False

    def delete_todo(self, todo_id: int) -> bool:
        """
        Delete a todo item
        
        Args:
            todo_id: The ID of the todo to delete
            
        Returns:
            True if successful, False otherwise
        """
        for i, todo in enumerate(self.todos):
            if todo["id"] == todo_id:
                title = todo["title"]
                self.todos.pop(i)
                print(f"✗ Deleted '{title}'")
                return self._save_todos()

        print(f"Error: Todo with ID {todo_id} not found")
        return False

    def update_todo(self, todo_id: int, title: str = None, description: str = None) -> bool:
        """
        Update a todo item
        
        Args:
            todo_id: The ID of the todo to update
            title: New title (optional)
            description: New description (optional)
            
        Returns:
            True if successful, False otherwise
        """
        for todo in self.todos:
            if todo["id"] == todo_id:
                if title:
                    todo["title"] = title.strip()
                if description is not None:
                    todo["description"] = description.strip()
                print(f"✓ Updated todo ID {todo_id}")
                return self._save_todos()

        print(f"Error: Todo with ID {todo_id} not found")
        return False

    def get_stats(self) -> dict:
        """
        Get statistics about todos
        
        Returns:
            Dictionary with todo statistics
        """
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t["completed"])
        pending = total - completed

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_percentage": (completed / total * 100) if total > 0 else 0
        }

    def display_stats(self) -> None:
        """Display todo statistics"""
        stats = self.get_stats()
        print("\n" + "=" * 40)
        print("📊 TODO STATISTICS")
        print("=" * 40)
        print(f"Total todos:        {stats['total']}")
        print(f"Completed:          {stats['completed']}")
        print(f"Pending:            {stats['pending']}")
        print(f"Completion:         {stats['completion_percentage']:.1f}%")
        print("=" * 40 + "\n")


def display_menu() -> None:
    """Display the main menu"""
    print("\n" + "=" * 40)
    print("📝 TO-DO LIST APPLICATION")
    print("=" * 40)
    print("1. Add a new todo")
    print("2. View all todos")
    print("3. Mark todo as complete")
    print("4. Mark todo as incomplete")
    print("5. Delete a todo")
    print("6. Update a todo")
    print("7. View statistics")
    print("8. Exit")
    print("=" * 40)


def main():
    """Main function to run the to-do list application"""
    app = TodoApp()

    while True:
        display_menu()
        choice = input("Enter your choice (1-8): ").strip()

        if choice == "1":
            title = input("Enter todo title: ").strip()
            if title:
                description = input("Enter todo description (optional): ").strip()
                if app.add_todo(title, description):
                    print("✓ Todo added successfully!")
                else:
                    print("✗ Failed to add todo")

        elif choice == "2":
            app.list_todos()

        elif choice == "3":
            try:
                todo_id = int(input("Enter todo ID to mark as complete: "))
                app.mark_complete(todo_id)
            except ValueError:
                print("Error: Invalid ID format")

        elif choice == "4":
            try:
                todo_id = int(input("Enter todo ID to mark as incomplete: "))
                app.mark_incomplete(todo_id)
            except ValueError:
                print("Error: Invalid ID format")

        elif choice == "5":
            try:
                todo_id = int(input("Enter todo ID to delete: "))
                if input("Are you sure? (y/n): ").lower() == "y":
                    app.delete_todo(todo_id)
            except ValueError:
                print("Error: Invalid ID format")

        elif choice == "6":
            try:
                todo_id = int(input("Enter todo ID to update: "))
                new_title = input("Enter new title (press Enter to skip): ").strip()
                new_description = input("Enter new description (press Enter to skip): ").strip()
                if new_title or new_description:
                    app.update_todo(todo_id, new_title if new_title else None, 
                                  new_description if new_description else None)
                else:
                    print("No changes made")
            except ValueError:
                print("Error: Invalid ID format")

        elif choice == "7":
            app.display_stats()

        elif choice == "8":
            print("Goodbye! 👋")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
