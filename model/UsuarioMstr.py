import werkzeug.security as safe
import flask_login
import sirope

"""
    - username: Nombre de usuario que servira como "clave primaria" ya que este sera unico
    e irrepetible por usuario
    - alias: Sobrenombre que se pone el usuario, este complementa al nombre de usuario
    - num_seguidores: Numero de seguidores que tiene el usuario
    - seguidores: Array que contiene los oids de los usuarios seguidores
    - num_seguidos: Numero de usuarios seguidos que tiene el usuario
    - seguidos: Array que contiene los oids de los usuarios seguidos
    - num_post: Numero de posts que ha publicado el usuario
    - posts: Array que contiene los oids de los posts del usuario
    - liked_posts: Array que contiene los oids de los posts a los que el usuario les ha dado me gusta
    - bio: biografia del usuario, esta es opcional
    - imagen_perfil: nombre de la imagen que luego sera indexada en la carpeta de /static/fotos_perfil
"""

class Usuario(flask_login.UserMixin):
    def __init__(
        self, username, password, alias
    ):
        self.__username = username
        self.__password = safe.generate_password_hash(password)
        self.__alias = alias
        self.__num_seguidores = 0
        self.__seguidores = []
        self.__num_seguidos = 0
        self.__seguidos = []
        self.__num_posts = 0
        self.__posts = []
        self.__liked_posts = []
        self.__bio = ''
        self.__imagen_perfil = f'{username}_prof.jpg'

    @property 
    def username(self):
        return self.__username

    @username.setter
    def username(self, username):
        self.__username = username 

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, new_password):
        self.__password = safe.generate_password_hash(new_password)

    @property
    def alias(self):
        return self.__alias

    @alias.setter
    def alias(self, alias):
        self.__alias = alias

    @property
    def num_seguidores(self):
        return self.__num_seguidores

    @num_seguidores.setter
    def num_seguidores(self, num):
        self.__num_seguidores = num
    
    @property
    def seguidores(self):
        return self.__seguidores
    
    @property
    def num_seguidos(self):
        return self.__num_seguidos

    @num_seguidos.setter
    def num_seguidos(self, num):
        self.__num_seguidos = num

    @property
    def seguidos(self):
        return self.__seguidos

    @property
    def num_posts(self):
        return self.__num_posts

    @num_posts.setter
    def num_posts(self, num):
        self.__num_posts = num
    
    @property
    def posts(self) -> list:
        return self.__posts

    @property
    def liked_posts(self):
        return self.__liked_posts

    @property
    def bio(self):
        return self.__bio

    @bio.setter
    def bio(self, bio):
        self.__bio = bio
    
    @property
    def imagen_perfil(self):
        return self.__imagen_perfil

    @imagen_perfil.setter
    def imagen_perfil(self, imagen):
        self.__imagen_perfil = imagen
    
    def check_passwd(self, password):
        return safe.check_password_hash(self.__password, password)

    @staticmethod
    def find_user(s: sirope.Sirope, username: str) -> "Usuario":
        return s.find_first(Usuario, lambda u: u.username == username)
    

        