import sqlite3

conn = sqlite3.connect('sistema.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        contrasena TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'usuario',
        estado TEXT DEFAULT 'activo'
    )
''')



conn.commit()
conn.close()

print("✅ Base de datos y tabla 'usuarios' creadas correctamente.")

