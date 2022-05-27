
# Librerias
import random
import re
from flask import (
    Flask, redirect, render_template, request, session, url_for, g, flash
)
import sirope
import json
import os
import shutil
from sirope.oid import OID
from model.UsuarioMstr import Usuario
from model.PostsMstr import Post
from model.ComentarioMstr import Comentario
from werkzeug.utils import secure_filename

# parametros de inicializacion
app = Flask(__name__)
app.config.from_file('config.json', json.load)
srp = sirope.Sirope()

# Parametros de configuracion para los archivos
ALLOWED_EXTENSIONS = set(['jpg'])

# paths
UPLOAD_FOLDER = 'static/imagenes'
PROFILE_PICS_FOLDER = 'static/fotos_perfil'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_PICS_FOLDER'] = PROFILE_PICS_FOLDER

def archivos_permitidos(nombre):
    return '.' in nombre and nombre.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""
    before_request(): inicializa una variable global con el usuario actual lo que 
    resulta muy util, ya que esta se puede llamar a lo largo del código tanto como
    en el app.py como en los templates
"""
@app.before_request
def before_request():
    g.user = None

    if 'username' in session:
        user = Usuario.find_user(srp, session['username'])
        g.user = user

"""
    Redirige a login automaticamente
"""
@app.route('/')
def index():
    if not session:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('home'))

"""
    Vistas y rutas de administracion
"""
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] 

        user = Usuario.find_user(srp, username)

        if user:
            if user.check_passwd(password):
                session['username'] = user.username
                return redirect(url_for('home'))
            else:
                flash("Lo sentimos, la contraseña es incorrecta. Verifique que la contraseña sea correcta")
        else:
           flash("Lo sentimos, usuario no encontrado. Verifique que el nombre de usuario sea correcto.")

    return render_template('login.html', login=True)

"""
    Se borra la variable de sesion del usuario
"""
@app.route('/logout')
def logout():
    if not g.user:
        return redirect(url_for('login'))

    session.pop('username', None)
    return redirect(url_for('login'))

"""
    Se registra al usuario y se le pone la imagen vacía por defecto
"""
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        alias = request.form['alias']
        password = request.form['password']
        rpasswprd = request.form['rpassword']

        if username:
            user = Usuario.find_user(srp, username)
            if not user:
                if alias:
                    if password:
                        if password == rpasswprd:
                            srp.save(Usuario(username, password, alias))
                            shutil.copyfile('static/fotos_perfil/empty_prof.jpg', f'static/fotos_perfil/{username}_prof.jpg')
                            flash("Registrado correctamente, inicie sesión para continuar")
                            return redirect(url_for('login'))
                        else:
                            flash("Las contraseñas no son iguales")
                    else:
                        flash("Introduzca una contraseña")
                else:
                    flash("Introduzca un alias")
            else:
                flash("El nombre de usuario ya existe")
        else:
            flash("Introduzca un nombre de usuario")

    return render_template('signup.html', signup=True)

"""

# Vistas principales

"""

"""
    Esta es la pagina principal con la que se recibe el usuario.
    En ella se renderizan los posts del propio usuario y los usuarios seguidos,
    una lista de usuarios recomendados segun los que haya en la BD y
    una funcionalidad de busqueda de perfiles de usuario
"""
@app.route('/home', methods=['POST', 'GET'])
def home():
    if not g.user:
        return redirect(url_for('login'))

    #Variables a recuperar de la BD
    usuarios_seguidos = []
    posts = []
    generator = srp.load_all(Post)
    usuarios_recomendados = []

    # Inicializacion de las variables
    for oid in g.user.seguidos:
        usuarios_seguidos.append(srp.load(oid).username)
        
    for post in generator:
        if post.usuario in usuarios_seguidos or post.usuario == g.user.username:
            posts.append(post)

    for post in posts:
        comentarios = []
        for comentario in post.comentarios:
            tmp = srp.load(comentario)
            comentarios.append(tmp)
        post.comentarios = comentarios

    for usuario in srp.load_all(Usuario):
        if usuario.username != g.user.username and usuario.__oid__ not in g.user.seguidos:
            usuarios_recomendados.append(usuario)

    while len(usuarios_recomendados) > 5:
        usuarios_recomendados.pop(random.randint(0, 4))

    return render_template('home.html', home=True, posts=posts, usuarios_recomendados=usuarios_recomendados)

"""
    Vista del perfil propio
"""
@app.route('/profile', methods=['POST', 'GET'])
def profile():
    if not g.user:
        return redirect(url_for('login'))

    # variables a recuperar de la BD
    user_posts = []
    liked_posts = []
    seguidores = []
    seguidos = []

    # asignacion de valores
    for post in g.user.posts:
        user_posts.append(srp.load(post))

    for post in g.user.liked_posts:
        liked_posts.append(srp.load(post))

    for seg in g.user.seguidores:
        seguidores.append(srp.load(seg))

    for s in g.user.seguidos:
        seguidos.append(srp.load(s))

    for post in user_posts:
        comentarios = []
        for comentario in post.comentarios:
            tmp = srp.load(comentario)
            comentarios.append(tmp)
        post.comentarios = comentarios

    for post in liked_posts:
        comentarios = []
        for comentario in post.comentarios:
            tmp = srp.load(comentario)
            comentarios.append(tmp)
        post.comentarios = comentarios

    # Se gestiona si se ven los posts propios o los que me han gustado
    if request.args.get('posts') != None:
        return render_template('profile.html', profile=True, user_posts=user_posts, own_profile=True, seguidores=seguidores, seguidos=seguidos, posts_tab=True)
    elif request.args.get('liked') != None:
        return render_template('profile.html', profile=True, liked_posts=liked_posts, own_profile=True, seguidores=seguidores, seguidos=seguidos, liked=True)
    else:
        return render_template('profile.html', profile=True, user_posts=user_posts, own_profile=True, seguidores=seguidores, seguidos=seguidos, posts_tab=True)

"""
    Vista del perfil de otro usuario
"""
@app.route('/profile/<string:username>', methods=['POST', 'GET'])
def other_profile(username):
    if not g.user:
        return redirect(url_for('login'))

    # variables a recuperar de la BD
    users_oids = srp.load_all(Usuario)
    usernames = []
    users = []
    user_posts = []
    seguidores = []
    seguidos = []

    # inicializacion de las variables
    for user in users_oids:
        usernames.append(user.username)
        users.append(user)

    # index out of bounds si no hay usuario
    try:
        user = [x for x in users if x.username == username][0]
    except:
        return render_template('profile.html', profile=True, user_not_found=True, user=user)

    if username not in usernames:
        return render_template('profile.html', profile=True, user_not_found=True, user=user)

    for seg in user.seguidores:
        seguidores.append(srp.load(seg))

    for s in user.seguidos:
        seguidos.append(srp.load(s))

    for post in user.posts:
        user_posts.append(srp.load(post))

    for post in user_posts:
        comentarios = []
        for comentario in post.comentarios:
            tmp = srp.load(comentario)
            comentarios.append(tmp)
        post.comentarios = comentarios

    # si me "auto-busco" que me mande a mi perfil
    if username == g.user.username:
        return render_template('profile.html', profile=True, user_posts=user_posts, own_profile=True, user=user, seguidores=seguidores, seguidos=seguidos, posts=True)

    return render_template('profile.html', profile=True, user_posts=user_posts, another_profile=True, user=user, seguidores=seguidores, seguidos=seguidos)

"""
    Vista de ajustes del usuario
"""
@app.route('/settings', methods=['POST', 'GET'])
def settings():
    if not g.user:
        return redirect(url_for('login'))
    
    return render_template('settings.html', profile=True, edit_profile=True)

"""
    Redireccion a la vista de cambio de password
"""
@app.route('/settings/change/password', methods=['POST', 'GET'])
def change_password():
    if not g.user:
        return redirect(url_for('login'))
    
    return render_template('settings.html', profile=True, edit_password=True)

"""
# funcionalidades
"""

"""
    Edicion del perfil donde se reciben los datos de un formulario 
"""
@app.route('/edit-profile', methods=['POST'])
def edit_profile():
    if not g.user:
       return redirect(url_for('login'))
    
    # campos del formulario
    alias = request.form['alias']
    username = request.form['username']
    bio = request.form['bio']

    # validaciones y guardado en la BD
    if alias:
        if username:
            users = srp.load_all(Usuario)
            not_available_usernames = []
            for user in users:
                if user.username != g.user.username:
                    not_available_usernames.append(user.username)
            
            if username not in not_available_usernames:
                usr = srp.load(OID(Usuario, g.user.__oid__.num))
                usr.alias = alias
                usr.username = username
                usr.bio = bio
                srp.save(usr)
                flash("Tu nombre de usuario ha sido cambiado correctamente, inicie sesión para continuar")
                return redirect(url_for('profile'))
            else:
                flash("Este nombre de usuario no está disponible")
        else:
            flash("Introduzca un nombre de usuario")
    else:
        flash("Introduzca un alias")
    
    return redirect(url_for('settings'))

"""
    Edicion del password donde se reciben los datos de un formulario
"""
@app.route('/edit-password', methods=['POST'])
def edit_password():
    if not g.user:
       return redirect(url_for('login'))
    
    # valores del formulario
    old_password = request.form['opassword']
    new_password = request.form['npassword']
    rnew_password = request.form['rnpassword']

    # valores de la BD para comparar y guardar los nuevos datos
    user = Usuario.find_user(srp, g.user.username)
    usr = srp.load(OID(Usuario, g.user.__oid__.num))

    # validaciones y guardado en la BD
    if old_password:
        if usr.check_passwd(old_password):
            if new_password:
                if rnew_password:
                    if new_password == rnew_password:
                        usr.password = new_password
                        srp.save(usr)
                        flash("Tu contraseña ha sido cambiado correctamente, inicie sesión para continuar")
                        return redirect(url_for('logout'))
                    else:
                        flash("Las nuevas contraseñas no son iguales")
                else:
                    flash("Por favor confirma tu contraseña")
            else:
                flash("Introduzca una nueva contraseña")
        else:
            flash("Tu contraseña anterior es incorrecta")
    else:
        flash("Introduce tu contraseña anterior")
    
    return redirect('/settings/change/password')

"""
    Se añade un post nuevo y se guarda en la carpeta /static/imagenes
    y en la BD el nombre de dicha imagen para poder recuperarla luego
"""
@app.route('/add-post', methods=['POST'])
def add_post():
    if not g.user:
        return redirect(url_for(login))
    else:
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No se ha seleccionado una imagen para subir')
            return redirect(request.url)
        if file and archivos_permitidos(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #database insertion
            usr = srp.load(OID(Usuario, g.user.__oid__.num))
            post_oid = srp.save(Post(filename, request.form['caption'], g.user.username))
            usr.posts.append(post_oid)
            usr.num_posts = usr.num_posts + 1;
            srp.save(usr)

            return redirect(request.referrer)

"""
    Editar la foto del perfil del usuario. Hay dos modos
    Si el usuario selecciona el borrar su foto actual
    se manda la peticion con el parametro delete, lo que asigna la imagen vacia.
    En el otro caso el usuario ha decidido subir una imagen, por lo que se 
    sube en la carpeta /static/fotos_perfil y se actualiza la imagen del usuario
"""
@app.route('/edit-profile-pic', methods=['POST'])
def update_profile_pic():
    if not g.user:
        return redirect(url_for(login))
    else:
        if request.args.get('delete'):
            shutil.copyfile('static/fotos_perfil/empty_prof.jpg', f'static/fotos_perfil/{g.user.username}_prof.jpg')
            return redirect(url_for('profile'))
        else:
            if 'new-prof' not in request.files:
                flash('No file part')
            file = request.files['new-prof']
            if file.filename == '':
                flash('No se ha seleccionado una imagen para subir')
            if file and archivos_permitidos(file.filename):
                filename = g.user.username + "_prof." + file.filename.split('.', 1)[1]
                file.save(os.path.join(app.config['PROFILE_PICS_FOLDER'], filename))
                #database insertion
                usr = srp.load(OID(Usuario, g.user.__oid__.num))
                usr.imagen_perfil = filename
                srp.save(usr)

                return redirect(url_for('profile'))

"""
    Se añade un comentario a un post y se actualiza la lista de comentarios en BD
"""
@app.route('/add-comment', methods=['POST'])
def add_comment():
    if not g.user:
        return redirect(url_for(login))
    else:
        comentario = request.form['comentario']
        post_num = request.args.get('number')

        comment_oid = srp.save(Comentario(comentario, g.user.username))

        post = srp.load(OID(Post, post_num))

        post.comentarios.append(comment_oid)
        post.num_comentarios += 1

        srp.save(post)

        return redirect(request.referrer)


"""
    Mandamos la peticion a la ruta de like y actualizamos los likes asociados a
    un post
"""
@app.route('/like', methods=['POST'])
def like():
    if not g.user:
        return redirect(url_for(login))
    else:
        # parametros
        oid = request.args.get('oid')
       
        # cargamos de la BD
        post = srp.load(OID(Post, oid))
        user = srp.load(OID(Usuario, g.user.__oid__.num))

        # Actualizamos post y mi usuario
        post.liked_by.append(g.user.username)
        post.likes += 1

        liked_post_oid = srp.save(post)

        # guardamos en la lista de post que me han gustado
        user.liked_posts.append(liked_post_oid)

        srp.save(user)

    return "liked"

"""
    Mandamos la peticion a la ruta de dislike y actualizamos los likes asociados a
    un post
"""
@app.route('/dislike', methods=['POST'])
def dislike():
    if not g.user:
        return redirect(url_for(login))
    else:
        # parametros
        oid = request.args.get('oid')
      
        # cargamos de la BD
        post = srp.load(OID(Post, oid))
        user = srp.load(OID(Usuario, g.user.__oid__.num))

        # Actualizamos post y mi usuario
        post.liked_by.remove(g.user.username)
        post.likes -= 1

        disliked_post_oid = srp.save(post)

        # guardamos en la lista de post que me han gustado
        user.liked_posts.remove(disliked_post_oid)

        srp.save(user)
    
    return "disliked"

"""
    Se manda la peticion a esta ruta, se actualizan dos usuarios:
    - Por una parte el usuario que sigue, aumenta su numero de seguidos y se añade a la lista de seguidos
    - Por otra parte el usuario seguido, aumenta su numero de seguidores y se añade el nuevo seguidor a la lista de seguidores
"""
@app.route('/follow', methods=['POST'])
def follow():
    if not g.user:
        return redirect(url_for(login))
    else:
        followed_user_oid = request.args.get('followedUser') # string
        
        my_user = srp.load(OID(Usuario, g.user.__oid__.num))
        followed_user = srp.load(OID(Usuario, followed_user_oid.split('@', 1)[1]))

        # rewrite
        followed_user_oid = srp.save(followed_user)

        my_user.seguidos.append(followed_user_oid)
        my_user.num_seguidos += 1

        my_user_oid = srp.save(my_user)

        followed_user.seguidores.append(my_user_oid)
        followed_user.num_seguidores += 1

        srp.save(followed_user)

    return "followed"

"""
    Se manda la peticion a esta ruta, se actualizan dos usuarios:
    - Por una parte el usuario ha dejado de seguir, decrementa su numero de seguidos y se quita de la lista de seguidos
    - Por otra parte el usuario dejado de seguir, decrementa su numero de seguidores y se quita el seguidor de la lista de seguidores
"""
@app.route('/unfollow', methods=['POST'])
def unfollow():
    if not g.user:
        return redirect(url_for(login))
    else:
        unfollowed_user_oid = request.args.get('unfollowedUser') # string
        
        my_user = srp.load(OID(Usuario, g.user.__oid__.num))
        followed_user = srp.load(OID(Usuario, unfollowed_user_oid.split('@', 1)[1]))

        # rewrite
        unfollowed_user_oid = srp.save(followed_user)

        my_user.seguidos.remove(unfollowed_user_oid)
        my_user.num_seguidos -= 1

        my_user_oid = srp.save(my_user)

        followed_user.seguidores.remove(my_user_oid)
        followed_user.num_seguidores -= 1

        srp.save(followed_user)

    return "unfollowed"

"""
    Las siguientes dos funciones se usan para la busqueda de usuarios
    mediante un filtro basado en la expr. regular que corresponde con
    las letras que se van introduciendo en el buscador
"""
def filtrar(lista, filtro) -> list:
    return [val for val in lista if re.search(f'^{filtro}', val)]

@app.route('/get-users', methods=['POST'])
def get_users():
    if not g.user:
        return redirect(url_for(login))
    else:
        filtro = request.args.get('filter')
        usuarios = srp.load_all(Usuario)
        usernames = []

        for user in usuarios:
            usernames.append(user.username)
        
        coincidencias = filtrar(usernames, filtro)
        
        return f'{coincidencias}'

"""
    Funcion de borrado de un post, al borrar el post se borra tanto de su propia "Tabla" de entidad,
    de los posts que le han gustado a un usuario (se borra de varias listas de liked_posts) y,
    ultimadamente, se borran los comentarios asociados a ese post
"""
@app.route('/delete-post', methods=['POST'] )
def delete_post():
    if not g.user:
        return redirect(url_for(login))
    else:
        num = request.args.get('num')

        user = srp.load(OID(Usuario, g.user.__oid__.num))
        u = srp.load_all(Usuario) 
        users = []
        post = srp.load(OID(Post, int(num)))
        post_oid = post.__oid__

        # borramos en el usuario propietario
        user.posts.remove(post_oid)
        user.num_posts -= 1
        srp.save(user)

        # borramos en los liked posts de los otros usuarios si es que está
        for user in u:
            users.append(user)

        for user in users:
            if post_oid in user.liked_posts:
                user.liked_posts.remove(post_oid)
                srp.save(user)

        # borramos los comentarios asociados a ese post
        for comentario in post.comentarios:
            srp.delete(OID(Comentario, comentario.num))

        srp.delete(post_oid)

        return redirect(url_for('profile'))