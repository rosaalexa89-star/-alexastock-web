import os
import psycopg2
import psycopg2.extras


# ==========================================
# CONEXIÓN A LA BASE DE DATOS (POSTGRES EN LA NUBE)
# ==========================================

def conectar():
    url = os.environ.get("DATABASE_URL")

    if not url:
        raise RuntimeError(
            "Falta la variable de entorno DATABASE_URL. "
            "En Render, esto se configura solo si usás el archivo render.yaml."
        )

    conexion = psycopg2.connect(url, sslmode="require")
    return conexion


# ==========================================
# CREAR TABLAS (se ejecuta solo, al iniciar la app)
# ==========================================

def crear_tablas():

    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                categoria TEXT,
                costo REAL NOT NULL DEFAULT 0,
                precio_venta REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                stock_minimo INTEGER NOT NULL DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metodos_pago (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER NOT NULL,
                producto_nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                costo_unitario REAL NOT NULL,
                total REAL NOT NULL,
                ganancia REAL NOT NULL,
                medio_pago TEXT NOT NULL,
                cliente TEXT DEFAULT '',
                pagado REAL DEFAULT 0,
                saldo REAL DEFAULT 0,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER NOT NULL,
                producto_nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario_bs REAL DEFAULT 0,
                total_bs REAL DEFAULT 0,
                cotizacion REAL DEFAULT 0,
                costo_unitario_ars REAL NOT NULL,
                total_ars REAL NOT NULL,
                proveedor TEXT DEFAULT '',
                moneda TEXT DEFAULT 'ARS',
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_costos (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER NOT NULL,
                producto_nombre TEXT NOT NULL,
                costo_anterior REAL NOT NULL,
                costo_nuevo REAL NOT NULL,
                motivo TEXT DEFAULT '',
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id SERIAL PRIMARY KEY,
                motivo TEXT DEFAULT '',
                monto REAL NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER NOT NULL,
                producto_nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                cliente TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                clave TEXT PRIMARY KEY,
                valor REAL NOT NULL DEFAULT 0
            )
        """)

        cursor.execute("""
            INSERT INTO config (clave, valor)
            VALUES ('inversion_inicial', 0)
            ON CONFLICT (clave) DO NOTHING
        """)

        metodos_iniciales = ["Transferencia", "Efectivo", "Mercado Pago"]

        for metodo in metodos_iniciales:
            cursor.execute("""
                INSERT INTO metodos_pago (nombre)
                VALUES (%s)
                ON CONFLICT (nombre) DO NOTHING
            """, (metodo,))

        conexion.commit()

    except Exception as error:
        conexion.rollback()
        print(f"Error al crear tablas: {error}")
        raise

    finally:
        cursor.close()
        conexion.close()


def _dict_cursor(conexion):
    return conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ==========================================
# PRODUCTOS
# ==========================================

def obtener_productos():
    conexion = conectar()
    cursor = _dict_cursor(conexion)

    try:
        cursor.execute("""
            SELECT id, nombre, categoria, costo, precio_venta, stock, stock_minimo
            FROM productos
            ORDER BY nombre
        """)
        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def obtener_producto(producto_id):
    conexion = conectar()
    cursor = _dict_cursor(conexion)

    try:
        cursor.execute("""
            SELECT id, nombre, categoria, costo, precio_venta, stock, stock_minimo
            FROM productos WHERE id = %s
        """, (producto_id,))
        fila = cursor.fetchone()
        return dict(fila) if fila else None

    finally:
        cursor.close()
        conexion.close()


def obtener_productos_stock_bajo():
    conexion = conectar()
    cursor = _dict_cursor(conexion)

    try:
        cursor.execute("""
            SELECT id, nombre, categoria, stock, stock_minimo
            FROM productos
            WHERE stock_minimo > 0 AND stock <= stock_minimo
            ORDER BY nombre
        """)
        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def agregar_producto(nombre, categoria, costo, precio_venta, stock, stock_minimo):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if not nombre or not nombre.strip():
            return False, "Ingresá el nombre del producto.", None

        cursor.execute("""
            INSERT INTO productos (nombre, categoria, costo, precio_venta, stock, stock_minimo)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (nombre.strip(), categoria, costo, precio_venta, stock, stock_minimo))

        nuevo_id = cursor.fetchone()[0]
        conexion.commit()
        return True, "Producto agregado correctamente.", nuevo_id

    except Exception as error:
        conexion.rollback()
        return False, f"Error al agregar el producto: {error}", None

    finally:
        cursor.close()
        conexion.close()


def editar_producto(producto_id, nombre, categoria, costo, precio_venta, stock, stock_minimo):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if not nombre or not nombre.strip():
            return False, "Ingresá el nombre del producto."

        cursor.execute("""
            UPDATE productos
            SET nombre = %s, categoria = %s, costo = %s, precio_venta = %s,
                stock = %s, stock_minimo = %s
            WHERE id = %s
        """, (nombre.strip(), categoria, costo, precio_venta, stock, stock_minimo, producto_id))

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "El producto no existe."

        conexion.commit()
        return True, "Producto actualizado correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al editar el producto: {error}"

    finally:
        cursor.close()
        conexion.close()


def eliminar_producto(producto_id):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
        conexion.commit()
        return True, "Producto eliminado correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al eliminar el producto: {error}"

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# CATEGORÍAS
# ==========================================

def obtener_categorias():
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT nombre FROM categorias ORDER BY nombre")
        return [fila[0] for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def agregar_categoria(nombre):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if not nombre or not nombre.strip():
            return False, "Ingresá un nombre para la categoría."

        cursor.execute("""
            INSERT INTO categorias (nombre) VALUES (%s)
            ON CONFLICT (nombre) DO NOTHING
        """, (nombre.strip(),))

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "Esa categoría ya existe."

        conexion.commit()
        return True, "Categoría agregada."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al agregar la categoría: {error}"

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# MÉTODOS DE PAGO
# ==========================================

def obtener_metodos_pago():
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT nombre FROM metodos_pago ORDER BY nombre")
        return [fila[0] for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def agregar_metodo_pago(nombre):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if not nombre or not nombre.strip():
            return False, "Ingresá un nombre para el método de pago."

        cursor.execute("""
            INSERT INTO metodos_pago (nombre) VALUES (%s)
            ON CONFLICT (nombre) DO NOTHING
        """, (nombre.strip(),))

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "Ese método de pago ya existe."

        conexion.commit()
        return True, "Método de pago agregado."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al agregar el método de pago: {error}"

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# VENTAS
# ==========================================

def obtener_ventas(limite=None):
    conexion = conectar()
    cursor = _dict_cursor(conexion)

    try:
        consulta = """
            SELECT id, producto_id, producto_nombre, cantidad, precio_unitario,
                   total, ganancia, medio_pago, cliente, pagado, saldo, fecha
            FROM ventas
            ORDER BY fecha DESC, id DESC
        """
        if limite:
            consulta += " LIMIT %s"
            cursor.execute(consulta, (limite,))
        else:
            cursor.execute(consulta)

        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def registrar_venta(producto_id, cantidad, precio_unitario, medio_pago, cliente, pagado):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT nombre, costo, stock FROM productos WHERE id = %s", (producto_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            return False, "El producto no existe."

        producto_nombre, costo_unitario, stock_actual = resultado

        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero."

        if cantidad > stock_actual:
            return False, f"No hay suficiente stock. Stock disponible: {stock_actual}"

        total = precio_unitario * cantidad

        if pagado < 0:
            return False, "El monto pagado no puede ser negativo."

        if pagado > total:
            return False, "El monto pagado no puede ser mayor que el total de la venta."

        ganancia = (precio_unitario - costo_unitario) * cantidad
        saldo = total - pagado

        cursor.execute("""
            INSERT INTO ventas
            (producto_id, producto_nombre, cantidad, precio_unitario, costo_unitario,
             total, ganancia, medio_pago, cliente, pagado, saldo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (producto_id, producto_nombre, cantidad, precio_unitario, costo_unitario,
              total, ganancia, medio_pago, cliente or "", pagado, saldo))

        cursor.execute("UPDATE productos SET stock = stock - %s WHERE id = %s",
                        (cantidad, producto_id))

        conexion.commit()
        return True, "Venta registrada correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al registrar la venta: {error}"

    finally:
        cursor.close()
        conexion.close()


def registrar_pago(venta_id, monto):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT total, pagado, saldo FROM ventas WHERE id = %s", (venta_id,))
        venta = cursor.fetchone()

        if venta is None:
            return False, "La venta no existe."

        total, pagado_actual, saldo_actual = venta

        if monto <= 0:
            return False, "El monto debe ser mayor a cero."

        if monto > saldo_actual:
            return False, f"El cliente debe pagar como máximo $ {saldo_actual:,.2f}"

        nuevo_pagado = pagado_actual + monto
        nuevo_saldo = total - nuevo_pagado

        if abs(nuevo_saldo) < 0.01:
            nuevo_saldo = 0

        cursor.execute("UPDATE ventas SET pagado = %s, saldo = %s WHERE id = %s",
                        (nuevo_pagado, nuevo_saldo, venta_id))

        conexion.commit()
        return True, "Pago registrado correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al registrar el pago: {error}"

    finally:
        cursor.close()
        conexion.close()


def editar_venta(venta_id, cantidad, precio_unitario, medio_pago, cliente, pagado):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT producto_id, cantidad, costo_unitario FROM ventas WHERE id = %s", (venta_id,))
        venta = cursor.fetchone()

        if venta is None:
            return False, "La venta no existe."

        producto_id, cantidad_anterior, costo_unitario = venta

        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero."

        cursor.execute("SELECT stock FROM productos WHERE id = %s", (producto_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            return False, "El producto de esta venta ya no existe."

        # Si "devolviéramos" la cantidad anterior de esta venta, este es el
        # stock disponible real para validar la nueva cantidad.
        stock_disponible = resultado[0] + cantidad_anterior

        if cantidad > stock_disponible:
            return False, f"No hay suficiente stock. Stock disponible: {stock_disponible}"

        total = precio_unitario * cantidad

        if pagado < 0:
            return False, "El monto pagado no puede ser negativo."

        if pagado > total:
            return False, "El monto pagado no puede ser mayor que el total de la venta."

        ganancia = (precio_unitario - costo_unitario) * cantidad
        saldo = total - pagado

        if abs(saldo) < 0.01:
            saldo = 0

        cursor.execute("""
            UPDATE ventas
            SET cantidad = %s, precio_unitario = %s, total = %s, ganancia = %s,
                medio_pago = %s, cliente = %s, pagado = %s, saldo = %s
            WHERE id = %s
        """, (cantidad, precio_unitario, total, ganancia, medio_pago, cliente or "", pagado, saldo, venta_id))

        cursor.execute("UPDATE productos SET stock = %s WHERE id = %s",
                        (stock_disponible - cantidad, producto_id))

        conexion.commit()
        return True, "Venta actualizada correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al editar la venta: {error}"

    finally:
        cursor.close()
        conexion.close()


def eliminar_venta(venta_id):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT producto_id, cantidad FROM ventas WHERE id = %s", (venta_id,))
        venta = cursor.fetchone()

        if venta is None:
            return False, "La venta no existe."

        producto_id, cantidad = venta

        cursor.execute("UPDATE productos SET stock = stock + %s WHERE id = %s",
                        (cantidad, producto_id))
        cursor.execute("DELETE FROM ventas WHERE id = %s", (venta_id,))

        conexion.commit()
        return True, "Venta eliminada correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al eliminar la venta: {error}"

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# COMPRAS
# ==========================================

def obtener_compras(limite=None):
    conexion = conectar()
    cursor = _dict_cursor(conexion)

    try:
        consulta = """
            SELECT id, producto_id, producto_nombre, cantidad, precio_unitario_bs,
                   total_bs, cotizacion, costo_unitario_ars, total_ars, proveedor,
                   moneda, fecha
            FROM compras
            ORDER BY fecha DESC, id DESC
        """
        if limite:
            consulta += " LIMIT %s"
            cursor.execute(consulta, (limite,))
        else:
            cursor.execute(consulta)

        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def registrar_compra(producto_id, cantidad, moneda, precio_unitario, cotizacion, proveedor):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT nombre, costo FROM productos WHERE id = %s", (producto_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            return False, "El producto no existe."

        producto_nombre, costo_anterior = resultado

        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero."

        if precio_unitario <= 0:
            return False, "El precio debe ser mayor a cero."

        if moneda == "ARS":
            precio_unitario_ars = precio_unitario
            total_ars = precio_unitario_ars * cantidad
            precio_unitario_bs = 0
            total_bs = 0
            cotizacion_guardada = 0

        elif moneda == "Bs":
            if cotizacion <= 0:
                return False, "La cotización debe ser mayor a cero."

            precio_unitario_bs = precio_unitario
            total_bs = precio_unitario_bs * cantidad
            precio_unitario_ars = precio_unitario_bs / cotizacion
            total_ars = total_bs / cotizacion
            cotizacion_guardada = cotizacion

        else:
            return False, "Moneda de compra inválida."

        cursor.execute("""
            INSERT INTO compras
            (producto_id, producto_nombre, cantidad, precio_unitario_bs, total_bs,
             cotizacion, costo_unitario_ars, total_ars, proveedor, moneda)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (producto_id, producto_nombre, cantidad, precio_unitario_bs, total_bs,
              cotizacion_guardada, precio_unitario_ars, total_ars, proveedor or "", moneda))

        cursor.execute("UPDATE productos SET stock = stock + %s, costo = %s WHERE id = %s",
                        (cantidad, precio_unitario_ars, producto_id))

        if costo_anterior != precio_unitario_ars:
            cursor.execute("""
                INSERT INTO historial_costos
                (producto_id, producto_nombre, costo_anterior, costo_nuevo, motivo)
                VALUES (%s, %s, %s, %s, %s)
            """, (producto_id, producto_nombre, costo_anterior, precio_unitario_ars, "Compra"))

        conexion.commit()
        return True, "Compra registrada correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al registrar la compra: {error}"

    finally:
        cursor.close()
        conexion.close()


def eliminar_compra(compra_id):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT producto_id, cantidad FROM compras WHERE id = %s", (compra_id,))
        compra = cursor.fetchone()

        if compra is None:
            return False, "La compra no existe."

        producto_id, cantidad = compra

        cursor.execute("SELECT stock FROM productos WHERE id = %s", (producto_id,))
        resultado = cursor.fetchone()

        if resultado is not None:
            stock_actual = resultado[0]

            if cantidad > stock_actual:
                return False, (
                    "No se puede eliminar la compra porque el stock actual "
                    "es menor que la cantidad de la compra."
                )

            cursor.execute("UPDATE productos SET stock = stock - %s WHERE id = %s",
                            (cantidad, producto_id))

        cursor.execute("DELETE FROM compras WHERE id = %s", (compra_id,))

        conexion.commit()
        return True, "Compra eliminada correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al eliminar la compra: {error}"

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# REPORTE
# ==========================================

def obtener_reporte():
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM ventas")
        total_ventas = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(pagado), 0) FROM ventas")
        total_cobrado = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(saldo), 0) FROM ventas")
        total_pendiente = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(ganancia), 0) FROM ventas")
        ganancia = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_ars), 0) FROM compras")
        total_compras = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM productos
            WHERE stock_minimo > 0 AND stock <= stock_minimo
        """)
        productos_stock_bajo = cursor.fetchone()[0]

        return {
            "total_ventas": float(total_ventas),
            "total_cobrado": float(total_cobrado),
            "total_pendiente": float(total_pendiente),
            "ganancia": float(ganancia),
            "total_compras": float(total_compras),
            "productos_stock_bajo": productos_stock_bajo
        }

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# GASTOS EXTRA
# ==========================================

def obtener_gastos():
    conexion = conectar()
    cursor = _dict_cursor(conexion)

    try:
        cursor.execute("""
            SELECT id, motivo, monto, fecha
            FROM gastos
            ORDER BY fecha DESC, id DESC
        """)
        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def agregar_gasto(motivo, monto):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if monto is None or monto <= 0:
            return False, "El monto debe ser mayor a cero.", None

        cursor.execute("""
            INSERT INTO gastos (motivo, monto)
            VALUES (%s, %s)
            RETURNING id
        """, (motivo or "", monto))

        nuevo_id = cursor.fetchone()[0]
        conexion.commit()
        return True, "Gasto agregado correctamente.", nuevo_id

    except Exception as error:
        conexion.rollback()
        return False, f"Error al agregar el gasto: {error}", None

    finally:
        cursor.close()
        conexion.close()


def eliminar_gasto(gasto_id):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("DELETE FROM gastos WHERE id = %s", (gasto_id,))
        conexion.commit()
        return True, "Gasto eliminado correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al eliminar el gasto: {error}"

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# CONFIG (inversión inicial, etc.)
# ==========================================

def obtener_config():
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT clave, valor FROM config")
        filas = cursor.fetchall()
        return {clave: float(valor) for clave, valor in filas}

    finally:
        cursor.close()
        conexion.close()


def guardar_inversion_inicial(monto):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        if monto is None or monto < 0:
            return False, "El monto no puede ser negativo."

        cursor.execute("""
            INSERT INTO config (clave, valor)
            VALUES ('inversion_inicial', %s)
            ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor
        """, (monto,))

        conexion.commit()
        return True, "Inversión inicial actualizada."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al guardar la inversión inicial: {error}"

    finally:
        cursor.close()
        conexion.close()


# ==========================================
# PEDIDOS (encargos de clientes, todavía sin pagar ni entregar)
# ==========================================

def obtener_pedidos():
    conexion = conectar()
    cursor = _dict_cursor(conexion)

    try:
        cursor.execute("""
            SELECT id, producto_id, producto_nombre, cantidad, precio_unitario,
                   cliente, notas, fecha
            FROM pedidos
            ORDER BY fecha ASC, id ASC
        """)
        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()


def agregar_pedido(producto_id, cantidad, cliente, notas=""):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT nombre, precio_venta FROM productos WHERE id = %s", (producto_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            return False, "El producto no existe.", None

        producto_nombre, precio_venta = resultado

        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero.", None

        cursor.execute("""
            INSERT INTO pedidos (producto_id, producto_nombre, cantidad, precio_unitario, cliente, notas)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (producto_id, producto_nombre, cantidad, precio_venta, cliente or "", notas or ""))

        nuevo_id = cursor.fetchone()[0]
        conexion.commit()
        return True, "Pedido agregado correctamente.", nuevo_id

    except Exception as error:
        conexion.rollback()
        return False, f"Error al agregar el pedido: {error}", None

    finally:
        cursor.close()
        conexion.close()


def eliminar_pedido(pedido_id):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
        conexion.commit()
        return True, "Pedido eliminado correctamente."

    except Exception as error:
        conexion.rollback()
        return False, f"Error al eliminar el pedido: {error}"

    finally:
        cursor.close()
        conexion.close()


def entregar_pedido(pedido_id, precio_unitario, medio_pago, pagado):
    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT producto_id, cantidad, cliente
            FROM pedidos WHERE id = %s
        """, (pedido_id,))
        pedido = cursor.fetchone()

        if pedido is None:
            return False, "El pedido no existe."

        producto_id, cantidad, cliente = pedido

    finally:
        cursor.close()
        conexion.close()

    # Reutilizamos la misma lógica que una venta nueva: valida stock,
    # calcula ganancia con el costo actual del producto y descuenta stock.
    exito, mensaje = registrar_venta(
        producto_id, cantidad, precio_unitario, medio_pago, cliente, pagado
    )

    if not exito:
        return False, mensaje

    conexion = conectar()
    cursor = conexion.cursor()

    try:
        cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
        conexion.commit()
        return True, "Pedido entregado y registrado como venta."

    except Exception as error:
        conexion.rollback()
        return False, f"La venta se registró, pero hubo un error al borrar el pedido: {error}"

    finally:
        cursor.close()
        conexion.close()
