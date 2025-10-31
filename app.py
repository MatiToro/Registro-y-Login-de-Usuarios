from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from flask_bcrypt import Bcrypt

# contraseña usuario 1: 09876543
# contraseña admin: 12345678

app = Flask(__name__)
app.secret_key = 'clave_secreta_super_segura'
bcrypt = Bcrypt(app)
DB_NAME = "sistema.db"


@app.route('/')
def index():
    usuario_id = session.get('usuario_id')
    nombre = session.get('nombre')
    tipo = session.get('tipo')
    return render_template('index.html', usuario_id=usuario_id, nombre=nombre, tipo=tipo)

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def pagina_no_encontrada2(e):
    return render_template('404.html'), 405

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contra = request.form['contra']
        confirmar = request.form['confirmar']

        if contra != confirmar:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html', nombre=nombre, email=email)
        
        

        hash_contra = bcrypt.generate_password_hash(contra).decode('utf-8')
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, contrasena)
                VALUES (?, ?, ?)
            """, (nombre, email, hash_contra))
            conn.commit()
            conn.close()

            flash("Registro exitoso", "success")
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash("El email ya está registrado", "error")
            return redirect(url_for('registro'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contra = request.form['contra']
    
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, contrasena, tipo, estado FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            #----------------BANEAR USUARIO----------------
            if usuario[4] == 'baneado':
                flash('Tu cuenta ha sido baneada', 'error')
                return render_template('login.html', email=email)
            #----------------------------------------------

            if bcrypt.check_password_hash(usuario[2], contra):
                session['usuario_id'] = usuario[0]
                session['nombre'] = usuario[1]
                session['tipo'] = usuario[3]
                flash("Inicio de sesión exitoso", "success")
                return redirect(url_for('index'))
        
        flash("Credenciales incorrectas", "error")
        return render_template('login.html', email=email)

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('index'))


@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para acceder al perfil', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (session['usuario_id'],))
    usuario = cursor.fetchone()
    conn.close()

    return render_template('perfil.html', usuario=usuario)


@app.route('/usuarios')
def ver_usuarios():
    if session.get('tipo') != 'admin':
        return render_template('404.html'), 404
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, tipo, estado FROM usuarios")
    usuarios = cursor.fetchall()
    conn.close()

    return render_template('usuarios.html', usuarios=usuarios)

#-----------------------------BANEAR USUARIOS----------------------------------------
@app.route('/banear/<int:usuario_id>', methods=['POST'])
def banear_usuario(usuario_id):
    if 'tipo' not in session or session['tipo'] != 'admin':
        return render_template('404.html'), 404

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT tipo, estado FROM usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        flash("Usuario no encontrado", "error")
        return redirect(url_for('ver_usuarios'))

    if usuario[0] == 'admin':
        conn.close()
        flash("No podés banear a un administrador", "error")
        return redirect(url_for('ver_usuarios'))

    nuevo_estado = 'baneado' if usuario[1] == 'activo' else 'activo'
    cursor.execute("UPDATE usuarios SET estado = ? WHERE id = ?", (nuevo_estado, usuario_id))
    conn.commit()
    conn.close()

    mensaje = 'Usuario baneado' if nuevo_estado == 'baneado' else 'Usuario desbaneado'
    flash(mensaje, 'success')

    return redirect(url_for('ver_usuarios'))
#---------------------------------------------------------------------------------------


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)