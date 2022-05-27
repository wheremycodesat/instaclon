from model.ComentarioMstr import Comentario
from sirope.oid import OID

"""
    - imagen: nombre de la imagen
    - caption: pie de foto asociado al post
    - usuario: usuario que ha publicado la foto
    - likes: numero de likes de un post
    - liked_by: array con los oids de los usuarios que le han dado me gusta
    - num_comentarios: numero de comentarios
    - comentarios: array con los oids de los comentarios asociados al post
"""
class Post():
    def __init__(self, imagen, caption, usuario):
        self.__imagen = imagen
        self.__caption = caption
        self.__usuario = usuario
        self.__likes = 0
        self.__liked_by = [] # usuarios que le han dado me gusta
        self.__num_comentarios = 0
        self.__comentarios = []

    @property
    def imagen(self):
        return self.__imagen;
    
    @property
    def caption(self):
        return self.__caption;

    @caption.setter
    def caption(self, caption):
        self.__caption = caption

    @property
    def usuario(self):
        return self.__usuario;
    
    @property
    def likes(self):
        return self.__likes;
    
    @likes.setter
    def likes(self, likes):
        self.__likes = likes

    @property
    def liked_by(self):
        return self.__liked_by;

    @property
    def num_comentarios(self):
        return self.__num_comentarios;
    
    @num_comentarios.setter
    def num_comentarios(self, num):
        self.__num_comentarios = num
    
    @property
    def comentarios(self):
        return self.__comentarios;

    @comentarios.setter
    def comentarios(self, comentarios):
        self.__comentarios = comentarios