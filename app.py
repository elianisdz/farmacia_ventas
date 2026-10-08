from datetime import date, datetime
import sqlite3
import pandas as pd
import streamlit as st

# -------------------------------------------------------------------
# CONFIGURACIÓN DE CONTRASEÑA (LOGIN)
# -------------------------------------------------------------------
PASSWORD_CORRECTA = "1234"  # Puedes cambiar "1234" por la clave que quieras


def verificar_password():
  # Si ya está autenticado en la sesión, no volvemos a pedirla
  if st.session_state.get("password_correcta", False):
    return True

  # Creamos un formulario centrado para el login
  st.markdown("<br><br><br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 2, 1])

  with col2:
    st.markdown(
        "### 🔐 Acceso Restringido - <span"
        ' style="color: #2980b9;">Droguería Valentina</span>',
        unsafe_allow_html=True,
    )
    with st.form("form_login"):
      input_pass = st.text_input(
          "Ingrese la contraseña de acceso:", type="password"
      )
      btn_login = st.form_submit_button("Entrar", type="primary")

      if btn_login:
        if input_pass == PASSWORD_CORRECTA:
          st.session_state["password_correcta"] = True
          st.rerun()
        else:
          st.error("❌ Contraseña incorrecta.")

  return False


# Si la contraseña no es correcta, detenemos la app aquí
if not verificar_password():
  st.stop()


# -------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA WEB
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Registro de Ventas - Droguería Valentina",
    page_icon="💊",
    layout="wide",
)

# Estilo CSS estricto para centrar absolutamente todo en la tabla (cuerpo y encabezados)
st.markdown(
    """
    <style>
    /* Centrar textos, números y encabezados en st.data_editor / st.dataframe */
    [data-testid="stDataFrame"] div[role="columnheader"],
    [data-testid="stDataFrame"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[role="columnheader"] *,
    [data-testid="stDataFrame"] div[role="gridcell"] * {
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# BASE DE DATOS
# -------------------------------------------------------------------


def conectar_db():
  conn = sqlite3.connect("ventas_drogueria.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            fecha_solo TEXT NOT NULL,
            producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario INTEGER NOT NULL,
            total INTEGER NOT NULL,
            metodo_pago TEXT NOT NULL
        )
    """)
  conn.commit()
  return conn


conn = conectar_db()

st.markdown(
    "💊 ## Registro de Ventas - <span"
    ' style="color: #2980b9;">Droguería Valentina</span>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# BARRA LATERAL: FORMULARIO AUTOMÁTICO
# -------------------------------------------------------------------
st.sidebar.header("📝 Registrar Nueva Venta")

# Recoger datos fuera del formulario para poder calcular el total en tiempo real
fecha_venta = st.sidebar.date_input("Fecha de la Venta", value=date.today())
producto = st.sidebar.text_input("Nombre del Producto / Medicamento")
cantidad = st.sidebar.number_input("Cantidad", min_value=1, value=1, step=1)
precio_unitario = st.sidebar.number_input(
    "Precio Unitario ($)", min_value=0, value=1000, step=500, format="%d"
)

# Cálculo dinámico del total para que se muestre antes de guardar
total_parcial = int(cantidad * precio_unitario)
total_parcial_fmt = f"${total_parcial:,.0f}".replace(",", ".")
st.sidebar.markdown(f"### 💰 Total a Pagar: **{total_parcial_fmt}**")

metodo_pago = st.sidebar.selectbox(
    "Forma de Pago", ["Efectivo", "Nequi / Daviplata", "Tarjeta", "Otro"]
)

# Formulario con botón de envío
with st.sidebar.form(key="form_venta"):
  guardar = st.form_submit_button("💾 Anotar Venta", type="primary")

if guardar:
  if not producto.strip():
    st.sidebar.error("⚠️ Debes ingresar el nombre del producto.")
  else:
    ahora_hora = datetime.now().strftime("%H:%M:%S")
    fecha_solo_str = fecha_venta.strftime("%Y-%m-%d")
    fecha_hora_str = f"{fecha_solo_str} {ahora_hora}"

    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO ventas (fecha_hora, fecha_solo, producto, cantidad, precio_unitario, total, metodo_pago)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fecha_hora_str,
            fecha_solo_str,
            producto,
            int(cantidad),
            int(precio_unitario),
            total_parcial,
            metodo_pago,
        ),
    )
    conn.commit()

    st.sidebar.success(f"✅ Venta registrada: {producto}")
    st.rerun()

# -------------------------------------------------------------------
# CONSULTA Y CALENDARIO DE VENTAS
# -------------------------------------------------------------------
st.header("📊 Consulta de Ventas")

col_filtro1, col_filtro2 = st.columns([1, 2])

with col_filtro1:
  modo_consulta = st.radio(
      "Ver ventas por:",
      ["Día Específico (Calendario)", "Rango de Fechas", "Todas las Ventas"],
  )

if modo_consulta == "Día Específico (Calendario)":
  with col_filtro2:
    fecha_seleccionada = st.date_input(
        "Selecciona la fecha en el calendario:", value=date.today()
    )
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    query = (
        "SELECT id, fecha_hora, producto, cantidad, precio_unitario, total,"
        " metodo_pago FROM ventas WHERE fecha_solo = ? ORDER BY id DESC"
    )
    params = (fecha_str,)

elif modo_consulta == "Rango de Fechas":
  with col_filtro2:
    rango = st.date_input(
        "Selecciona rango (Inicio - Fin):", value=(date.today(), date.today())
    )
    if isinstance(rango, tuple) and len(rango) == 2:
      f_inicio, f_fin = rango[0].strftime("%Y-%m-%d"), rango[1].strftime(
          "%Y-%m-%d"
      )
      query = (
          "SELECT id, fecha_hora, producto, cantidad, precio_unitario, total,"
          " metodo_pago FROM ventas WHERE fecha_solo BETWEEN ? AND ? ORDER BY id"
          " DESC"
      )
      params = (f_inicio, f_fin)
    else:
      query = (
          "SELECT id, fecha_hora, producto, cantidad, precio_unitario, total,"
          " metodo_pago FROM ventas WHERE fecha_solo = ? ORDER BY id DESC"
      )
      params = (date.today().strftime("%Y-%m-%d"),)

else:
  query = (
      "SELECT id, fecha_hora, producto, cantidad, precio_unitario, total,"
      " metodo_pago FROM ventas ORDER BY id DESC"
  )
  params = ()

df = pd.read_sql_query(query, conn, params=params)

if not df.empty:
  total_dinero = df["total"].sum()
  total_unidades = df["cantidad"].sum()
  total_transacciones = len(df)

  total_dinero_fmt = f"${total_dinero:,.0f}".replace(",", ".")

  m1, m2, m3 = st.columns(3)
  m1.metric("💵 Total Recaudado (Selección)", total_dinero_fmt)
  m2.metric("📦 Unidades Vendidas", f"{total_unidades}")
  m3.metric("🧾 Registros Realizados", f"{total_transacciones}")

  st.markdown("---")
  st.subheader("Tabla de Ventas")
  st.caption(
      "Marca la casilla al lado de la venta que quieras anular o borrar y"
      " presiona el botón inferior."
  )

  df_mostrar = df.copy()

  # Formatear números con separador de miles con punto
  df_mostrar["precio_unitario"] = df_mostrar["precio_unitario"].apply(
      lambda x: f"${x:,.0f}".replace(",", ".")
  )
  df_mostrar["total"] = df_mostrar["total"].apply(
      lambda x: f"${x:,.0f}".replace(",", ".")
  )

  df_mostrar.insert(0, "Eliminar", False)

  columnas_visibles = [
      "Eliminar",
      "fecha_hora",
      "producto",
      "cantidad",
      "precio_unitario",
      "total",
      "metodo_pago",
  ]

  df_editado = st.data_editor(
      df_mostrar[columnas_visibles + ["id"]],
      column_config={
          "Eliminar": st.column_config.CheckboxColumn(
              "Seleccionar", default=False
          ),
          "id": None,  # Oculto
          "fecha_hora": st.column_config.TextColumn(
              "Fecha / Hora", disabled=True
          ),
          "producto": st.column_config.TextColumn("Producto", disabled=True),
          "cantidad": st.column_config.NumberColumn("Cant.", disabled=True),
          "precio_unitario": st.column_config.TextColumn(
              "Precio Unit. ($)", disabled=True
          ),
          "total": st.column_config.TextColumn("Total ($)", disabled=True),
          "metodo_pago": st.column_config.TextColumn("Pago", disabled=True),
      },
      disabled=[
          "fecha_hora",
          "producto",
          "cantidad",
          "precio_unitario",
          "total",
          "metodo_pago",
      ],
      hide_index=True,
      use_container_width=True,
  )

  filas_a_eliminar = df_editado[df_editado["Eliminar"] == True]
  if not filas_a_eliminar.empty:
    if st.button("🗑️ Eliminar ventas seleccionadas", type="primary"):
      ids_borrar = filas_a_eliminar["id"].tolist()
      cursor = conn.cursor()
      cursor.executemany(
          "DELETE FROM ventas WHERE id = ?", [(i,) for i in ids_borrar]
      )
      conn.commit()
      st.success(
          f"✅ Se eliminaron {len(ids_borrar)} registro(s) de la base de"
          " datos."
      )
      st.rerun()

else:
  st.warning("No hay ventas anotadas para la fecha o criterio seleccionado.")