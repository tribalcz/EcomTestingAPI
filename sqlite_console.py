import sqlite3

def execute_sql(cursor, sql):
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        if result:
            for row in result:
                print(row)
        else:
            print("Příkaz proveden úspěšně.")
    except sqlite3.Error as e:
        print(f"Chyba SQLite: {e}")

def show_tables(cursor):
    execute_sql(cursor, "SELECT name FROM sqlite_master WHERE type='table';")

def show_schema(cursor, table_name):
    execute_sql(cursor, f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")

def show_columns(cursor, table_name):
    execute_sql(cursor, f"PRAGMA table_info({table_name});")

def add_column(cursor, table_name, column_name, column_type):
    execute_sql(cursor, f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")

# Připojení k databázi
conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

print("Vítejte v SQLite konzoli. Zadejte SQL příkazy nebo speciální příkazy:")
print("  .tables - zobrazí seznam tabulek")
print("  .schema <table_name> - zobrazí schéma tabulky")
print("  .columns <table_name> - zobrazí sloupce tabulky")
print("  .addcolumn <table_name> <column_name> <type> - přidá nový sloupec")
print("  exit - ukončí konzoli")

while True:
    command = input("SQL> ").strip()
    if command.lower() == 'exit':
        break
    elif command == '.tables':
        show_tables(cursor)
    elif command.startswith('.schema '):
        show_schema(cursor, command.split()[1])
    elif command.startswith('.columns '):
        show_columns(cursor, command.split()[1])
    elif command.startswith('.addcolumn '):
        parts = command.split()
        if len(parts) == 4:
            add_column(cursor, parts[1], parts[2], parts[3])
        else:
            print("Nesprávný formát. Použijte: .addcolumn <table_name> <column_name> <type>")
    else:
        execute_sql(cursor, command)

conn.close()
print("Konzole ukončena.")