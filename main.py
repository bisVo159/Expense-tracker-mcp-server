import os
import aiosqlite
from fastmcp import FastMCP
from typing import Optional
import tempfile

mcp = FastMCP("Expense Tracker")

TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

def init_db():
    import sqlite3
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT DEFAULT '',
            note TEXT DEFAULT ''
        )
        """)

init_db()

@mcp.tool
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    '''
    Add a new expense entry. 
    Args:
        date: Date in YYYY-MM-DD format.
        amount: The cost of the expense (numeric).
        category: The main category (e.g., food, transport, housing, utilities, health, education etc).
        subcategory: Optional specific detail (e.g., groceries, fuel etc).
        note: Optional extra notes.
    '''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            await c.commit()
        return {"status": "ok", "id": cur.lastrowid,"message": "Expense added successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    '''List expense entries within an inclusive date range (YYYY-MM-DD).'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}
    
@mcp.tool()
async def edit_expense(subcategory: str, date: str, amount: Optional[float] = None, category: Optional[str] = None, note: Optional[str] = None):
    '''
    Edit an existing expense entry identified by date and subcategory.
    Only provide the fields that need updating.
    '''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            fields = []
            params = []

            if amount is not None:
                fields.append("amount = ?")
                params.append(amount)
            if category is not None:
                fields.append("category = ?")
                params.append(category)
            if note is not None:
                fields.append("note = ?")
                params.append(note)

            if not fields:
                return {"status": "no changes"}

            params.extend([date, subcategory])
            query = f"UPDATE expenses SET {', '.join(fields)} WHERE date = ? and subcategory = ?"
            cur = await c.execute(query, params)
            await c.commit()
            return {"status": "ok", "rows_affected": cur.rowcount}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
async def delete_expense(date: str, subcategory: str):
    '''Delete an expense entry by its date (YYYY-MM-DD) and subcategory.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute("DELETE FROM expenses WHERE date = ? and subcategory = ?", (date,subcategory))
            await c.commit()
            return {"status": "ok", "rows_affected": cur.rowcount}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def summarize(start_date: str, end_date: str, category: Optional[str] = None):
    '''Summarize expenses by category within a date range (YYYY-MM-DD).'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            query = (
                """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE date BETWEEN ? AND ?
                """
            )
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"

            cur = await c.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in await cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}
    
@mcp.resource("expense:///categories",mime_type="application/json")
def get_categories():
    # Read fresh each time so you can edit the file without restarting
    try:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return {"status": "error", "message": f"Error reading categories: {str(e)}"}
    

if __name__ == "__main__":
    # mcp.run()
    mcp.run(transport="http", host="0.0.0.0", port=8000)
