from django.urls import path
from .views import (
    registroUsuario,
    loginManual,
    perfilUsuario,
    CategoriasView,
    DevolverActualizarEliminarCategoriaView,
    ProductosView,
    ProductoView,
    crearUrlParaSubirArchivo,
    crearMedia,
    DespachosView,
)

urlpatterns = [
    path("registro", registroUsuario),
    path("login", loginManual),
    path("perfil", perfilUsuario),
    path("categorias", CategoriasView.as_view()),
    path("categoria/<id>", DevolverActualizarEliminarCategoriaView.as_view()),
    path("productos", ProductosView.as_view({
        "get": "list",
        "post": "create",
    })),
    path("producto/<id>", ProductoView.as_view({
        "get": "retrieve",
        "delete": "destroy",
    })),
    path("generar-url", crearUrlParaSubirArchivo),
    path("media", crearMedia),
    path("despachos", DespachosView.as_view()),
]
