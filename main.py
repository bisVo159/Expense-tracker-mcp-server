import os
import aiosqlite
from fastmcp import FastMCP

mcp = FastMCP("Expense Tracker")

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
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
async def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
        return {"status": "ok", "id": cur.lastrowid,"message": "Expense added successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
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
async def edit_expense(subcategory, date, amount=None, category=None, note=None):
    '''Edit an existing expense entry by its date and subcategory.'''
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
            return {"status": "ok", "rows_affected": cur.rowcount}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
async def delete_expense(date,subcategory):
    '''Delete an expense entry by its date and subcategory.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute("DELETE FROM expenses WHERE date = ? and subcategory = ?", (date,subcategory))
            return {"status": "ok", "rows_affected": cur.rowcount}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
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
    
@mcp.resource("expense://categories",mime_type="application/json")
def get_categories():
    # Read fresh each time so you can edit the file without restarting
    try:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return {"status": "error", "message": f"Error reading categories: {str(e)}"}
    

if __name__ == "__main__":
    mcp.run()
