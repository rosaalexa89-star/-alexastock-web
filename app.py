from flask import Flask, render_template, request, jsonify

import database

app = Flask(__name__)

# Se crean las tablas al arrancar la app (si ya existen, no hace nada).
with app.app_context():
    database.crear_tablas()


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# PRODUCTOS
# ============================================================

@app.route("/api/productos", methods=["GET"])
def api_obtener_productos():
    return jsonify(database.obtener_productos())


@app.route("/api/productos", methods=["POST"])
def api_agregar_producto():
    datos = request.get_json(force=True)

    exito, mensaje, nuevo_id = database.agregar_producto(
        nombre=datos.get("nombre", ""),
        categoria=datos.get("categoria", ""),
        costo=float(datos.get("costo", 0) or 0),
        precio_venta=float(datos.get("precio_venta", 0) or 0),
        stock=int(datos.get("stock", 0) or 0),
        stock_minimo=int(datos.get("stock_minimo", 0) or 0),
    )

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje, "id": nuevo_id})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


@app.route("/api/productos/<int:producto_id>", methods=["DELETE"])
def api_eliminar_producto(producto_id):
    exito, mensaje = database.eliminar_producto(producto_id)

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


# ============================================================
# CATEGORÍAS
# ============================================================

@app.route("/api/categorias", methods=["GET"])
def api_obtener_categorias():
    return jsonify(database.obtener_categorias())


@app.route("/api/categorias", methods=["POST"])
def api_agregar_categoria():
    datos = request.get_json(force=True)
    exito, mensaje = database.agregar_categoria(datos.get("nombre", ""))

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


# ============================================================
# MÉTODOS DE PAGO
# ============================================================

@app.route("/api/metodos_pago", methods=["GET"])
def api_obtener_metodos_pago():
    return jsonify(database.obtener_metodos_pago())


@app.route("/api/metodos_pago", methods=["POST"])
def api_agregar_metodo_pago():
    datos = request.get_json(force=True)
    exito, mensaje = database.agregar_metodo_pago(datos.get("nombre", ""))

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


# ============================================================
# VENTAS
# ============================================================

@app.route("/api/ventas", methods=["GET"])
def api_obtener_ventas():
    limite = request.args.get("limite", type=int)
    return jsonify(database.obtener_ventas(limite))


@app.route("/api/ventas", methods=["POST"])
def api_registrar_venta():
    datos = request.get_json(force=True)

    exito, mensaje = database.registrar_venta(
        producto_id=int(datos.get("producto_id")),
        cantidad=int(datos.get("cantidad", 0) or 0),
        precio_unitario=float(datos.get("precio_unitario", 0) or 0),
        medio_pago=datos.get("medio_pago", ""),
        cliente=datos.get("cliente", ""),
        pagado=float(datos.get("pagado", 0) or 0),
    )

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


@app.route("/api/ventas/<int:venta_id>/pago", methods=["POST"])
def api_registrar_pago(venta_id):
    datos = request.get_json(force=True)
    exito, mensaje = database.registrar_pago(venta_id, float(datos.get("monto", 0) or 0))

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


@app.route("/api/ventas/<int:venta_id>", methods=["DELETE"])
def api_eliminar_venta(venta_id):
    exito, mensaje = database.eliminar_venta(venta_id)

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


# ============================================================
# COMPRAS
# ============================================================

@app.route("/api/compras", methods=["GET"])
def api_obtener_compras():
    limite = request.args.get("limite", type=int)
    return jsonify(database.obtener_compras(limite))


@app.route("/api/compras", methods=["POST"])
def api_registrar_compra():
    datos = request.get_json(force=True)

    exito, mensaje = database.registrar_compra(
        producto_id=int(datos.get("producto_id")),
        cantidad=int(datos.get("cantidad", 0) or 0),
        moneda=datos.get("moneda", "ARS"),
        precio_unitario=float(datos.get("precio_unitario", 0) or 0),
        cotizacion=float(datos.get("cotizacion", 0) or 0),
        proveedor=datos.get("proveedor", ""),
    )

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


@app.route("/api/compras/<int:compra_id>", methods=["DELETE"])
def api_eliminar_compra(compra_id):
    exito, mensaje = database.eliminar_compra(compra_id)

    if exito:
        return jsonify({"ok": True, "mensaje": mensaje})

    return jsonify({"ok": False, "mensaje": mensaje}), 400


# ============================================================
# REPORTE
# ============================================================

@app.route("/api/reporte", methods=["GET"])
def api_obtener_reporte():
    return jsonify(database.obtener_reporte())


if __name__ == "__main__":
    app.run(debug=True)
