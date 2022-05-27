
"""
    - texto: contenido del comentario
    - usuario: usuario que ha hecho el comentario
"""
class Comentario():
    def __init__(self, texto, usuario):
        self.__texto = texto
        self.__usuario = usuario
    
    @property
    def texto(self):
        return self.__texto

    @texto.setter
    def texto(self, texto):
        self.__texto = texto
    
    @property
    def usuario(self):
        return self.__usuario

    @usuario.setter
    def usuario(self, usuario):
        self.__usuario = usuario
