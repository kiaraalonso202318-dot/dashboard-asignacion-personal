import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pulp import *

# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Dashboard de Asignación de Personal",
    layout="wide"
)

st.title("Dashboard de Asignación Óptima de Personal")

st.write(
    "Esta aplicación permite cargar el archivo Excel, seleccionar el turno, "
    "marcar operarios ausentes y calcular la asignación óptima de trabajadores "
    "a las tareas de la línea."
)

# =========================================================
# 1. CARGAR ARCHIVO
# =========================================================

st.subheader("1. Cargar archivo Excel")

archivo = st.file_uploader(
    "Sube el archivo Excel",
    type=["xlsx"]
)

if archivo is None:
    st.info("Sube el archivo Excel para comenzar.")
    st.stop()

# =========================================================
# 2. LEER HOJAS
# =========================================================

try:
    tasks_df = pd.read_excel(
        archivo,
        sheet_name="Tasks"
    )

    archivo.seek(0)

    rel_speed_df = pd.read_excel(
        archivo,
        sheet_name="Rel_Speed"
    )

    archivo.seek(0)

    workers_df = pd.read_excel(
        archivo,
        sheet_name="Workers"
    )

    archivo.seek(0)

    abilities_df = pd.read_excel(
        archivo,
        sheet_name="Abilities"
    )

    archivo.seek(0)

    speed_df = pd.read_excel(
        archivo,
        sheet_name="Speed_Factor"
    )

except Exception as e:
    st.error("No se pudo leer el archivo Excel. Revisa que tenga las hojas correctas.")
    st.exception(e)
    st.stop()

st.success("Archivo cargado correctamente.")

# =========================================================
# 3. CORREGIR TIPOS
# =========================================================

try:
    tasks_df["ID_Task"] = tasks_df["ID_Task"].astype(str)
    rel_speed_df["ID_Task"] = rel_speed_df["ID_Task"].astype(str)
    workers_df["ID_Worker"] = workers_df["ID_Worker"].astype(str)
    abilities_df["ID_Worker"] = abilities_df["ID_Worker"].astype(str)
    speed_df["ID_Worker"] = speed_df["ID_Worker"].astype(str)
    workers_df["Schedule"] = workers_df["Schedule"].astype(str)

except Exception as e:
    st.error("Hay un problema con los nombres de columnas del Excel.")
    st.exception(e)
    st.stop()

# =========================================================
# 4. MOSTRAR DATOS CARGADOS
# =========================================================

with st.expander("Ver hoja Tasks"):
    st.dataframe(tasks_df, use_container_width=True)

with st.expander("Ver hoja Rel_Speed"):
    st.dataframe(rel_speed_df, use_container_width=True)

with st.expander("Ver hoja Workers"):
    st.dataframe(workers_df, use_container_width=True)

with st.expander("Ver hoja Abilities"):
    st.dataframe(abilities_df, use_container_width=True)

with st.expander("Ver hoja Speed_Factor"):
    st.dataframe(speed_df, use_container_width=True)

# =========================================================
# 5. SELECCIÓN DE TURNO
# =========================================================

st.subheader("2. Seleccionar turno")

turnos_disponibles = sorted(
    workers_df["Schedule"].dropna().unique().tolist()
)

turno = st.selectbox(
    "Selecciona el turno",
    turnos_disponibles
)

workers_turno = workers_df[
    workers_df["Schedule"] == str(turno)
].copy()

st.write("Trabajadores programados en el turno seleccionado:")

st.dataframe(
    workers_turno[["ID_Worker", "Name"]],
    use_container_width=True
)

# =========================================================
# 6. AUSENTISMO
# =========================================================

st.subheader("3. Seleccionar operarios ausentes")

opciones_ausentes = []

for _, row in workers_turno.iterrows():
    opciones_ausentes.append(
        f"{row['ID_Worker']} - {row['Name']}"
    )

ausentes_seleccionados = st.multiselect(
    "Marca los operarios ausentes",
    opciones_ausentes
)

ausentes = [
    opcion.split(" - ")[0]
    for opcion in ausentes_seleccionados
]

trabajadores = list(
    workers_turno["ID_Worker"]
)

presentes = [
    i for i in trabajadores
    if i not in ausentes
]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Programados", len(trabajadores))

with col2:
    st.metric("Ausentes", len(ausentes))

with col3:
    st.metric("Presentes", len(presentes))

st.write("Trabajadores presentes:")

st.write(presentes)

if len(presentes) == 0:
    st.error("No hay trabajadores presentes para ejecutar el modelo.")
    st.stop()

# =========================================================
# 7. PARÁMETROS
# =========================================================

st.sidebar.header("Parámetros del modelo")

epsilon = st.sidebar.number_input(
    "Epsilon",
    min_value=0.0,
    value=0.0001,
    step=0.0001,
    format="%.4f"
)

lambda_pen = st.sidebar.number_input(
    "Penalización por doble asignación",
    min_value=0.0,
    value=100.0,
    step=10.0
)

ID_LLENADORA = st.sidebar.text_input(
    "ID de la llenadora",
    value="9"
)

minutos_turno = st.sidebar.number_input(
    "Minutos del turno para producción",
    min_value=1,
    value=480,
    step=1
)

# =========================================================
# 8. EJECUTAR MODELO
# =========================================================

st.subheader("4. Ejecutar optimización")

if st.button("Calcular asignación óptima", type="primary"):

    try:
        tareas = list(
            tasks_df["ID_Task"]
        )

        # m_j -> tarea necesita máquina
        m = dict(
            zip(
                tasks_df["ID_Task"],
                tasks_df["Need_Mac"]
            )
        )

        # Nombre tarea
        nombre_tarea = dict(
            zip(
                tasks_df["ID_Task"],
                tasks_df["Task"]
            )
        )

        # Velocidad nominal
        V_std = dict(
            zip(
                rel_speed_df["ID_Task"],
                rel_speed_df["Nominal_Sp"]
            )
        )

        # Máquina asociada
        machine_name = dict(
            zip(
                rel_speed_df["ID_Task"],
                rel_speed_df["Machine"]
            )
        )

        # =========================================================
        # MATRIZ HABILIDADES
        # =========================================================

        H = {}

        for _, row in abilities_df.iterrows():

            worker = row["ID_Worker"]

            H[worker] = {}

            for tarea in abilities_df.columns[2:]:

                H[worker][tarea] = row[tarea]

        # =========================================================
        # MATRIZ SPEED FACTOR
        # =========================================================

        F = {}

        for _, row in speed_df.iterrows():

            worker = row["ID_Worker"]

            F[worker] = {}

            for tarea in speed_df.columns[2:]:

                F[worker][tarea] = row[tarea]

        # =========================================================
        # VALIDACIONES BÁSICAS
        # =========================================================

        errores = []

        for i in presentes:
            if i not in H:
                errores.append(f"El trabajador {i} no aparece en Abilities.")

            if i not in F:
                errores.append(f"El trabajador {i} no aparece en Speed_Factor.")

        for j in tareas:
            tarea_nombre = nombre_tarea[j]

            for i in presentes:
                if i in H and tarea_nombre not in H[i]:
                    errores.append(
                        f"La tarea {tarea_nombre} no aparece como columna en Abilities."
                    )

                if i in F and tarea_nombre not in F[i]:
                    errores.append(
                        f"La tarea {tarea_nombre} no aparece como columna en Speed_Factor."
                    )

        if len(errores) > 0:
            st.error("Hay errores en la estructura del archivo.")
            for error in errores:
                st.write(error)
            st.stop()

        # =========================================================
        # MODELO
        # =========================================================

        modelo = LpProblem(
            "Asignacion_Optima",
            LpMinimize
        )

        # =========================================================
        # VARIABLES
        # =========================================================

        x = LpVariable.dicts(
            "x",
            [(i, j) for i in presentes for j in tareas],
            cat="Binary"
        )

        V_real = LpVariable.dicts(
            "V_real",
            tareas,
            lowBound=0
        )

        d = LpVariable.dicts(
            "d",
            tareas,
            lowBound=0
        )

        y = LpVariable.dicts(
            "y",
            presentes,
            cat="Binary"
        )

        # =========================================================
        # FUNCIÓN OBJETIVO
        # =========================================================

        modelo += (
            lpSum(
                m[j] * d[j]
                for j in tareas
            )
            -
            epsilon
            *
            lpSum(
                (1 - m[j])
                *
                H[i][nombre_tarea[j]]
                *
                x[(i, j)]
                for i in presentes
                for j in tareas
            )
            +
            lambda_pen
            *
            lpSum(
                y[i]
                for i in presentes
            )
        )

        # =========================================================
        # RESTRICCIONES
        # =========================================================

        # Cada tarea debe cubrirse
        for j in tareas:
            modelo += (
                lpSum(
                    x[(i, j)]
                    for i in presentes
                ) == 1
            )

        # Doble asignación
        for i in presentes:
            modelo += (
                lpSum(
                    x[(i, j)]
                    for j in tareas
                )
                <=
                1 + y[i]
            )

        # Máximo 2 tareas
        for i in presentes:
            modelo += (
                lpSum(
                    x[(i, j)]
                    for j in tareas
                )
                <= 2
            )

        # Restricción de habilidad:
        # si el operario no sabe hacer la tarea, no se le puede asignar.
        for i in presentes:
            for j in tareas:
                modelo += (
                    x[(i, j)]
                    <=
                    H[i][nombre_tarea[j]]
                )

        # Velocidad real
        for j in tareas:

            if m[j] == 1:

                nombre = nombre_tarea[j]

                modelo += (
                    V_real[j]
                    ==
                    V_std[j]
                    *
                    lpSum(
                        F[i][nombre]
                        *
                        x[(i, j)]
                        for i in presentes
                    )
                )

            else:

                modelo += (
                    V_real[j] == 0
                )

        # Desviación
        for j in tareas:

            if m[j] == 1:

                modelo += (
                    d[j]
                    >=
                    V_real[j]
                    -
                    V_std[j]
                )

                modelo += (
                    d[j]
                    >=
                    V_std[j]
                    -
                    V_real[j]
                )

            else:

                modelo += (
                    d[j] == 0
                )

        # =========================================================
        # RESOLVER
        # =========================================================

        solver = PULP_CBC_CMD(msg=False)

        modelo.solve(solver)

        estado = LpStatus[modelo.status]

        st.subheader("5. Estado del modelo")

        st.write(estado)

        if estado != "Optimal":
            st.error(
                "No se encontró solución óptima. Puede que falten operarios, "
                "que alguna tarea no tenga trabajador capacitado o que el máximo "
                "de 2 tareas por operario no alcance."
            )
            st.stop()

        # =========================================================
        # ASIGNACIONES
        # =========================================================

        asignaciones = []

        for i in presentes:

            tareas_asig = []

            for j in tareas:

                if value(x[(i, j)]) == 1:

                    tareas_asig.append(
                        nombre_tarea[j]
                    )

            if len(tareas_asig) > 0:

                nombre_operario = workers_df[
                    workers_df["ID_Worker"] == i
                ]["Name"].values[0]

                asignaciones.append(
                    [
                        i,
                        nombre_operario,
                        ", ".join(tareas_asig)
                    ]
                )

        asignaciones_df = pd.DataFrame(
            asignaciones,
            columns=[
                "ID Trabajador",
                "Trabajador",
                "Tareas Asignadas"
            ]
        )

        st.subheader("6. Asignaciones")

        st.dataframe(
            asignaciones_df,
            use_container_width=True
        )

        # =========================================================
        # DESVIACIONES
        # =========================================================

        desviaciones = []

        for j in tareas:

            if m[j] == 1:

                desviaciones.append(
                    [
                        j,
                        machine_name[j],
                        V_std[j],
                        round(value(V_real[j]), 2),
                        round(value(d[j]), 2)
                    ]
                )

        desv_df = pd.DataFrame(
            desviaciones,
            columns=[
                "ID Tarea",
                "Máquina",
                "Velocidad ideal",
                "Velocidad alcanzada",
                "Desviación"
            ]
        )

        st.subheader("7. Desviaciones")

        st.dataframe(
            desv_df,
            use_container_width=True
        )

        # =========================================================
        # PRODUCCIÓN TOTAL
        # =========================================================

        st.subheader("8. Producción total")

        if ID_LLENADORA in tareas:

            velocidad_llenadora = value(
                V_real[ID_LLENADORA]
            )

            botellas = velocidad_llenadora * minutos_turno

            col_a, col_b = st.columns(2)

            with col_a:
                st.metric(
                    "Velocidad llenadora",
                    round(velocidad_llenadora, 2)
                )

            with col_b:
                st.metric(
                    "Producción estimada",
                    f"{round(botellas, 0):,.0f} botellas/turno"
                )

        else:

            st.warning(
                f"El ID de llenadora '{ID_LLENADORA}' no está en la lista de tareas."
            )

        # =========================================================
        # CURVA VELOCIDADES
        # =========================================================

        st.subheader("9. Curva ideal vs real")

        maquinas = []
        vel_ideal = []
        vel_real = []

        for j in tareas:

            if m[j] == 1:

                maquinas.append(
                    machine_name[j]
                )

                vel_ideal.append(
                    V_std[j]
                )

                vel_real.append(
                    value(V_real[j])
                )

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(
            maquinas,
            vel_ideal,
            marker="o",
            label="Velocidad ideal"
        )

        ax.plot(
            maquinas,
            vel_real,
            marker="o",
            label="Velocidad alcanzada"
        )

        ax.set_xlabel("Máquinas")

        ax.set_ylabel("Velocidad")

        ax.set_title(
            "Curva ideal vs real"
        )

        ax.tick_params(axis="x", rotation=45)

        ax.grid(True)

        ax.legend()

        st.pyplot(fig)

        # =========================================================
        # DESCARGA DE RESULTADOS
        # =========================================================

        st.subheader("10. Descargar resultados")

        resultado_excel = pd.ExcelWriter(
            "resultados_asignacion.xlsx",
            engine="openpyxl"
        )

        asignaciones_df.to_excel(
            resultado_excel,
            sheet_name="Asignaciones",
            index=False
        )

        desv_df.to_excel(
            resultado_excel,
            sheet_name="Desviaciones",
            index=False
        )

        resultado_excel.close()

        with open("resultados_asignacion.xlsx", "rb") as file:

            st.download_button(
                label="Descargar resultados en Excel",
                data=file,
                file_name="resultados_asignacion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:

        st.error("Ocurrió un error al ejecutar el modelo.")
        st.exception(e)

else:

    st.info("Selecciona el turno, marca ausentes y presiona el botón para calcular.")
