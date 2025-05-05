import psycopg2
import ttkbootstrap as ttk
from tkinter import messagebox

DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "1234",
    "port": 5432
}

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

app = ttk.Window(themename="flatly")
app.title("Dtabase GUI")
app.geometry("1000x600")

notebook = ttk.Notebook(app)
notebook.pack(fill="both", expand=True)

def get_columns(table_name):
    cursor.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name.lower(),))
    return [col[0] for col in cursor.fetchall()]

def load_table_data(tree, table_name):
    tree.delete(*tree.get_children())
    cursor.execute(f"SELECT * FROM {table_name}")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

def create_table_tab(table_name):
    frame = ttk.Frame(notebook)
    notebook.add(frame, text=table_name)

    columns = get_columns(table_name)

    style = ttk.Style()
    style.configure("Treeview", rowheight=25, borderwidth=1, relief="solid")

    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col, anchor="center")  # Center the column headings
        tree.column(col, width=120, anchor="center")  # Center the column entries
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    entry_frame = ttk.Frame(frame)
    entry_frame.pack(fill="x", padx=10)

    entries = {} # Dictionary to hold entry widgets
    for col in columns:
        lbl = ttk.Label(entry_frame, text=col)
        lbl.pack(side="left", padx=5)
        entry = ttk.Entry(entry_frame, width=12)
        entry.pack(side="left")
        entries[col] = entry

    def on_select(event): # This function is called when a row is selected in the treeview
        selected = tree.selection()
        if selected:
            values = tree.item(selected[0])["values"]
            for i, col in enumerate(columns):
                entries[col].delete(0, "end")
                entries[col].insert(0, values[i])

    tree.bind("<<TreeviewSelect>>", on_select) # Bind the selection event

    def update_entry(): # This function is called when the update button is clicked
        values = [entries[col].get() for col in columns]
        set_clause = ", ".join(f"{col} = %s" for col in columns[1:])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {columns[0]} = %s"
        try:
            cursor.execute(sql, values[1:] + [values[0]])
            conn.commit()
            load_table_data(tree, table_name)
            messagebox.showinfo("Success", "Record updated.")
        except Exception as e:
            conn.rollback()  # <- This is the critical fix
            messagebox.showerror("Update Failed", f"{e}")


    def insert_entry():
        values = [entries[col].get() for col in columns]
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        try:
            cursor.execute(sql, values)
            conn.commit()
            load_table_data(tree, table_name)
            messagebox.showinfo("Success", "Record inserted.")
        except Exception as e:
            conn.rollback() 
            messagebox.showerror("Insert Failed", f"{e}")


    search_frame = ttk.Frame(frame)
    search_frame.pack(fill="x", padx=10, pady=5)

    search_label = ttk.Label(search_frame, text="Search:")
    search_label.pack(side="left", padx=5)

    search_entry = ttk.Entry(search_frame, width=20)
    search_entry.pack(side="left", padx=5)

    original_rows = []  # List to store original rows

    def search_table():
        nonlocal original_rows
        # Always refresh original_rows to reflect the current state of the Treeview
        original_rows = [(row, tree.item(row)["values"]) for row in tree.get_children()]
        
        query = search_entry.get().lower()
        tree.delete(*tree.get_children())  # Clear the Treeview
        for row, values in original_rows:
            if any(query in str(value).lower() for value in values):
                tree.insert("", "end", iid=row, values=values)  # Reinsert matching rows

    def reset_search():
        # Reload all data from the database
        load_table_data(tree, table_name)

    search_button = ttk.Button(search_frame, text="Search", command=search_table)
    search_button.pack(side="left", padx=5)

    reset_button = ttk.Button(search_frame, text="Reset", command=reset_search)
    reset_button.pack(side="left", padx=5)


    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="Update", command=update_entry).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Insert New", command=insert_entry).pack(side="left", padx=5)

    load_table_data(tree, table_name)

for table in ["Adresse", "Standort", "Abteilung", "Mitarbeiter", "Organisation"]:
    create_table_tab(table)

app.mainloop()
