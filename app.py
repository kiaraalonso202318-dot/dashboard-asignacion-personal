import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pulp import *
from io import BytesIO

# ============================================================
# CONFIGURACIÓN DE LA APP
# ============================================================

st.set_page_config(
    page_title="Dashboard de Asignación de Personal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILO VISUAL
# ============================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f7f9fc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .header-card {
        background: linear-gradient(135deg, #b00020 0%, #e53935 55%, #ff7043 100%);
        padding: 2rem;
        border-radius: 18px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }

    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }

    .header-subtitle {
        font-size: 1rem;
        opacity: 0.95;
    }

    .section-card {
        background: white;
        padding: 1.2rem;
        border-radius: 16px;
        border: 1px solid #e6e9ef;
        box-shadow: 0 4px 14px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    .small-note {
        font-size: 0.9rem;
        color: #5f6b7a;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e6e9ef;
        padding: 1rem;
        border-radius: 14px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.04);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 12px;
    }

    .stButton > button {
        border-radius: 12px;
        padding: 0.7rem 1.2rem;
        font-weight: 700;
    }

    .stDownloadButton > button {
        border-radius: 12px;
        padding: 0.7rem 1.2rem;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# ENCABEZADO
# ============================================================

st.markdown(
    """
    <div class="header-card">
        <div class="header-title">Dashboard de Asignación Óptima de Personal</div>
        <div class="header-subtitle">
            Herramienta de apoyo para asignar operarios por turno considerando ausentismo,
            habilidades, velocidades relativas, prioridad de la llenadora, producción y eficiencia.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.info(
    "Por confidencialidad, el dashboard trabaja únicamente con el ID del operario. "
    "No se muestran nombres del personal en la aplicación ni en el archivo de resultados."
)

# ============================================================
# 1. CARGAR ARCHIVO
# ============================================================

st.subheader("1. Cargar archivo Excel")

archivo = st.file_uploader(
    "Sube el archivo Excel del modelo",
    type=["xlsx"]
)

if archivo is None:
    st.warning("Sube el archivo Excel para iniciar el análisis.")
    st.stop()

# ============================================================
# 2. LEER HOJAS
# ============================================================

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
    st.error(
        "No se pudo leer el archivo Excel. Revisa que tenga las hojas: "
        "Tasks, Rel_Speed, Workers, Abilities y Speed_Factor."
    )
    st.exception(e)
    st.stop()

st.success("Archivo cargado correctamente.")

# ============================================================
# 3. CORREGIR TIPOS
# ============================================================

try:
    tasks_df["ID_Task"] = tasks_df["ID_Task"].astype(str)
    rel_speed_df["ID_Task"] = rel_speed_df["ID_Task"].astype(str)

    workers_df["ID_Worker"] = workers_df["ID_Worker"].astype(str)
    abilities_df["ID_Worker"] = abilities_df["ID_Worker"].astype(str)
    speed_df["ID_Worker"] = speed_df["ID_Worker"].astype(str)

    workers_df["Schedule"] = workers_df["Schedule"].astype(str)

    tasks_df["Task"] = tasks_df["Task"].astype(str).str.strip()
    rel_speed_df["Machine"] = rel_speed_df["Machine"].astype(str).str.strip()

except Exception as e:
    st.error("Hay un problema con los nombres de columnas del Excel.")
    st.exception(e)
    st.stop()

# ============================================================
# 4. REVISAR DATOS CARGADOS
# ============================================================

st.subheader("2. Revisar datos cargados")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Tasks",
        "Rel_Speed",
        "Workers",
        "Abilities",
        "Speed_Factor"
    ]
)

with tab1:
    st.dataframe(
        tasks_df,
        use_container_width=True
    )

with tab2:
    st.dataframe(
        rel_speed_df,
        use_container_width=True
    )

with tab3:
    columnas_workers_mostrar = [
        col for col in ["ID_Worker", "Schedule"]
        if col in workers_df.columns
    ]

    st.dataframe(
        workers_df[columnas_workers_mostrar],
        use_container_width=True
    )

with tab4:
    st.dataframe(
        abilities_df,
        use_container_width=True
    )

with tab5:
    st.dataframe(
        speed_df,
        use_container_width=True
    )

# ============================================================
# 5. SELECCIÓN DE TURNO
# ============================================================

st.subheader("3. Seleccionar turno")

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

st.markdown(
    '<div class="section-card">',
    unsafe_allow_html=True
)

st.write("Operarios programados en el turno seleccionado:")

st.dataframe(
    workers_turno[["ID_Worker", "Schedule"]],
    use_container_width=True
)

st.markdown(
    "</div>",
    unsafe_allow_html=True
)

if len(workers_turno) == 0:
    st.error("No hay operarios programados para este turno.")
    st.stop()

# ============================================================
# 6. AUSENTISMO
# ============================================================

st.subheader("4. Seleccionar ausentes")

opciones_ausentes = sorted(
    workers_turno["ID_Worker"].dropna().astype(str).tolist()
)

ausentes = st.multiselect(
    "Selecciona los ID de los operarios ausentes. Si no faltó nadie, deja vacío.",
    opciones_ausentes
)

trabajadores = list(
    workers_turno["ID_Worker"]
)

presentes = [
    i for i in trabajadores
    if i not in ausentes
]

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Operarios programados", len(trabajadores))

with c2:
    st.metric("Operarios ausentes", len(ausentes))

with c3:
    st.metric("Operarios presentes", len(presentes))

st.write("ID de operarios presentes:")

st.write(presentes)

if len(presentes) == 0:
    st.error("No hay operarios presentes. No se puede resolver el modelo.")
    st.stop()

# ============================================================
# 7. PARÁMETROS DEL MODELO
# ============================================================

st.sidebar.header("Parámetros del modelo")

ID_LLENADORA = st.sidebar.text_input(
    "ID de la llenadora",
    value="9"
)

epsilon = st.sidebar.number_input(
    "Premio pequeño por habilidad",
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

peso_deficit_llenadora = st.sidebar.number_input(
    "Penalización si la llenadora queda por debajo",
    min_value=0.0,
    value=10000.0,
    step=100.0
)

peso_desviacion_otras = st.sidebar.number_input(
    "Penalización desviación otras máquinas",
    min_value=0.0,
    value=1.0,
    step=1.0
)

habilidad_minima = st.sidebar.number_input(
    "Habilidad mínima para asignar",
    min_value=0.0,
    value=1.0,
    step=1.0
)

max_tareas_por_trabajador = st.sidebar.number_input(
    "Máximo de tareas por operario",
    min_value=1,
    max_value=10,
    value=2,
    step=1
)

minutos_turno = st.sidebar.number_input(
    "Minutos del turno",
    min_value=1,
    value=480,
    step=1
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Nota: si la matriz de habilidades usa 1 para apto y 0 para no apto, "
    "la habilidad mínima debe quedar en 1."
)

# ============================================================
# 8. EJECUTAR MODELO
# ============================================================

st.subheader("5. Ejecutar optimización")

if st.button("Calcular asignación óptima", type="primary"):

    try:
        # =========================================================
        # CONJUNTOS
        # =========================================================

        tareas = list(
            tasks_df["ID_Task"]
        )

        # =========================================================
        # PARÁMETROS DEL EXCEL
        # =========================================================

        m = dict(
            zip(
                tasks_df["ID_Task"],
                tasks_df["Need_Mac"]
            )
        )

        nombre_tarea = dict(
            zip(
                tasks_df["ID_Task"],
                tasks_df["Task"]
            )
        )

        V_std = dict(
            zip(
                rel_speed_df["ID_Task"],
                rel_speed_df["Nominal_Sp"]
            )
        )

        machine_name = dict(
            zip(
                rel_speed_df["ID_Task"],
                rel_speed_df["Machine"]
            )
        )

        if ID_LLENADORA not in tareas:
            st.error(
                f"El ID de llenadora definido ({ID_LLENADORA}) no existe en las tareas."
            )
            st.stop()

        # =========================================================
        # MATRIZ DE HABILIDADES
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
        # VALIDACIONES
        # =========================================================

        errores = []

        for i in presentes:
            if i not in H:
                errores.append(f"El operario con ID {i} no aparece en Abilities.")

            if i not in F:
                errores.append(f"El operario con ID {i} no aparece en Speed_Factor.")

        for j in tareas:
            nombre = nombre_tarea[j]

            for i in presentes:
                if i in H and nombre not in H[i]:
                    errores.append(
                        f"La tarea {nombre} no aparece como columna en Abilities."
                    )

                if i in F and nombre not in F[i]:
                    errores.append(
                        f"La tarea {nombre} no aparece como columna en Speed_Factor."
                    )

        if len(errores) > 0:
            st.error("Hay errores en la estructura del archivo.")
            for error in errores:
                st.write(error)
            st.stop()

        # =========================================================
        # IDENTIFICAR LLENADORA
        # =========================================================

        st.subheader("6. Llenadora identificada")

        col_l1, col_l2, col_l3 = st.columns(3)

        with col_l1:
            st.metric("ID llenadora", ID_LLENADORA)

        with col_l2:
            st.metric("Tarea", nombre_tarea[ID_LLENADORA])

        with col_l3:
            st.metric("Velocidad estándar", f"{V_std[ID_LLENADORA]} botellas/min")

        st.write("Máquina:", machine_name[ID_LLENADORA])

        # =========================================================
        # TABLA DE CANDIDATOS PARA LA LLENADORA
        # =========================================================

        candidatos_llenadora = []

        nombre_llenadora = nombre_tarea[ID_LLENADORA]

        for i in presentes:

            velocidad_estimada = V_std[ID_LLENADORA] * F[i][nombre_llenadora]

            deficit_candidato = max(
                V_std[ID_LLENADORA] - velocidad_estimada,
                0
            )

            exceso_candidato = max(
                velocidad_estimada - V_std[ID_LLENADORA],
                0
            )

            candidatos_llenadora.append(
                [
                    i,
                    H[i][nombre_llenadora],
                    F[i][nombre_llenadora],
                    velocidad_estimada,
                    deficit_candidato,
                    exceso_candidato
                ]
            )

        candidatos_llenadora_df = pd.DataFrame(
            candidatos_llenadora,
            columns=[
                "ID_Worker",
                "Habilidad_Llenadora",
                "Speed_Factor_Llenadora",
                "Velocidad_Estimada_Llenadora",
                "Deficit_vs_Estandar",
                "Exceso_vs_Estandar"
            ]
        )

        candidatos_llenadora_df = candidatos_llenadora_df.sort_values(
            by=[
                "Deficit_vs_Estandar",
                "Velocidad_Estimada_Llenadora",
                "Habilidad_Llenadora"
            ],
            ascending=[
                True,
                False,
                False
            ]
        )

        st.subheader("7. Candidatos para la llenadora")

        st.dataframe(
            candidatos_llenadora_df,
            use_container_width=True
        )

        # =========================================================
        # CREAR MODELO
        # =========================================================

        modelo = LpProblem(
            "Asignacion_Optima_Con_Eficiencia",
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

        deficit = LpVariable.dicts(
            "deficit",
            tareas,
            lowBound=0
        )

        exceso = LpVariable.dicts(
            "exceso",
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

        penalizacion_llenadora = (
            peso_deficit_llenadora * deficit[ID_LLENADORA]
        )

        penalizacion_otras_maquinas = lpSum(
            peso_desviacion_otras * d[j]
            for j in tareas
            if m[j] == 1 and j != ID_LLENADORA
        )

        penalizacion_doble = lambda_pen * lpSum(
            y[i]
            for i in presentes
        )

        premio_habilidad = epsilon * lpSum(
            H[i][nombre_tarea[j]] * x[(i, j)]
            for i in presentes
            for j in tareas
        )

        modelo += (
            penalizacion_llenadora
            + penalizacion_otras_maquinas
            + penalizacion_doble
            - premio_habilidad
        )

        # =========================================================
        # RESTRICCIONES
        # =========================================================

        # Cada tarea debe cubrirse exactamente por un operario
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

        # Máximo de tareas por operario
        for i in presentes:
            modelo += (
                lpSum(
                    x[(i, j)]
                    for j in tareas
                )
                <=
                max_tareas_por_trabajador
            )

        # No asignar operario si no tiene habilidad suficiente
        for i in presentes:

            for j in tareas:

                nombre = nombre_tarea[j]

                if H[i][nombre] < habilidad_minima:

                    modelo += (
                        x[(i, j)] == 0
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
                        F[i][nombre] * x[(i, j)]
                        for i in presentes
                    )
                )

            else:

                modelo += (
                    V_real[j] == 0
                )

        # Desviación absoluta, déficit y exceso
        for j in tareas:

            if m[j] == 1:

                modelo += (
                    d[j]
                    >=
                    V_real[j] - V_std[j]
                )

                modelo += (
                    d[j]
                    >=
                    V_std[j] - V_real[j]
                )

                modelo += (
                    deficit[j]
                    >=
                    V_std[j] - V_real[j]
                )

                modelo += (
                    exceso[j]
                    >=
                    V_real[j] - V_std[j]
                )

            else:

                modelo += (
                    d[j] == 0
                )

                modelo += (
                    deficit[j] == 0
                )

                modelo += (
                    exceso[j] == 0
                )

        # =========================================================
        # RESOLVER
        # =========================================================

        solver = PULP_CBC_CMD(msg=False)

        modelo.solve(solver)

        estado = LpStatus[modelo.status]

        st.subheader("8. Estado del modelo")

        if estado == "Optimal":
            st.success("Solución óptima encontrada.")
        else:
            st.error(
                "El modelo no encontró solución óptima. "
                "Revisa si hay suficientes operarios presentes o si las restricciones son muy fuertes."
            )
            st.write("Estado:", estado)
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

                asignaciones.append(
                    [
                        i,
                        ", ".join(tareas_asig)
                    ]
                )

        asignaciones_df = pd.DataFrame(
            asignaciones,
            columns=[
                "ID_Worker",
                "Tareas Asignadas"
            ]
        )

        st.subheader("9. Asignaciones")

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
                        nombre_tarea[j],
                        machine_name[j],
                        round(V_std[j], 2),
                        round(value(V_real[j]), 2),
                        round(value(d[j]), 2),
                        round(value(deficit[j]), 2),
                        round(value(exceso[j]), 2)
                    ]
                )

        desv_df = pd.DataFrame(
            desviaciones,
            columns=[
                "ID_Task",
                "Tarea",
                "Maquina",
                "Velocidad_Estandar",
                "Velocidad_Alcanzada",
                "Desviacion_Absoluta",
                "Deficit_Por_Debajo",
                "Exceso_Por_Encima"
            ]
        )

        st.subheader("10. Desviaciones")

        st.dataframe(
            desv_df,
            use_container_width=True
        )

        # =========================================================
        # REVISIÓN ESPECIAL DE LA LLENADORA
        # =========================================================

        st.subheader("11. Revisión especial de la llenadora")

        fila_llenadora = desv_df[
            desv_df["ID_Task"] == ID_LLENADORA
        ]

        st.dataframe(
            fila_llenadora,
            use_container_width=True
        )

        velocidad_llenadora = value(
            V_real[ID_LLENADORA]
        )

        velocidad_ideal_llenadora = V_std[
            ID_LLENADORA
        ]

        deficit_llenadora = value(
            deficit[ID_LLENADORA]
        )

        exceso_llenadora = value(
            exceso[ID_LLENADORA]
        )

        r1, r2, r3, r4 = st.columns(4)

        with r1:
            st.metric(
                "Velocidad ideal llenadora",
                f"{round(velocidad_ideal_llenadora, 2)} botellas/min"
            )

        with r2:
            st.metric(
                "Velocidad alcanzada llenadora",
                f"{round(velocidad_llenadora, 2)} botellas/min"
            )

        with r3:
            st.metric(
                "Déficit llenadora",
                f"{round(deficit_llenadora, 2)} botellas/min"
            )

        with r4:
            st.metric(
                "Exceso llenadora",
                f"{round(exceso_llenadora, 2)} botellas/min"
            )

        if deficit_llenadora > 0:
            st.error(
                "La llenadora quedó por debajo de la velocidad ideal. "
                "Esto reduce la producción del turno."
            )
        else:
            st.success(
                "La llenadora no quedó por debajo de la velocidad ideal. "
                "No hay pérdida por cuello de botella en llenadora."
            )

        # =========================================================
        # PRODUCCIÓN TOTAL Y EFICIENCIA
        # =========================================================

        botellas_reales = velocidad_llenadora * minutos_turno

        botellas_ideales = velocidad_ideal_llenadora * minutos_turno

        eficiencia = (
            botellas_reales / botellas_ideales
        ) * 100

        perdida_botellas = botellas_ideales - botellas_reales

        st.subheader("12. Producción total y eficiencia")

        p1, p2, p3, p4 = st.columns(4)

        with p1:
            st.metric(
                "Producción ideal",
                f"{round(botellas_ideales, 0):,.0f} botellas/turno"
            )

        with p2:
            st.metric(
                "Producción estimada",
                f"{round(botellas_reales, 0):,.0f} botellas/turno"
            )

        with p3:
            st.metric(
                "Pérdida estimada",
                f"{round(perdida_botellas, 0):,.0f} botellas/turno"
            )

        with p4:
            st.metric(
                "Eficiencia estimada",
                f"{round(eficiencia, 2)}%"
            )

        resumen_produccion_df = pd.DataFrame(
            {
                "Indicador": [
                    "Velocidad ideal llenadora",
                    "Velocidad alcanzada llenadora",
                    "Producción ideal del turno",
                    "Producción estimada del turno",
                    "Pérdida estimada del turno",
                    "Eficiencia estimada"
                ],
                "Valor": [
                    round(velocidad_ideal_llenadora, 2),
                    round(velocidad_llenadora, 2),
                    round(botellas_ideales, 0),
                    round(botellas_reales, 0),
                    round(perdida_botellas, 0),
                    round(eficiencia, 2)
                ],
                "Unidad": [
                    "botellas/min",
                    "botellas/min",
                    "botellas/turno",
                    "botellas/turno",
                    "botellas/turno",
                    "%"
                ]
            }
        )

        st.dataframe(
            resumen_produccion_df,
            use_container_width=True
        )

        # =========================================================
        # GRÁFICA VELOCIDAD IDEAL VS ALCANZADA
        # =========================================================

        st.subheader("13. Curva velocidad ideal vs alcanzada")

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

        fig1, ax1 = plt.subplots(figsize=(12, 6))

        ax1.plot(
            maquinas,
            vel_ideal,
            marker="o",
            label="Velocidad ideal"
        )

        ax1.plot(
            maquinas,
            vel_real,
            marker="o",
            label="Velocidad alcanzada"
        )

        ax1.set_xlabel("Máquinas")
        ax1.set_ylabel("Velocidad botellas/min")
        ax1.set_title("Curva ideal vs real")
        ax1.tick_params(axis="x", rotation=45)
        ax1.grid(True)
        ax1.legend()

        st.pyplot(fig1)

        # =========================================================
        # GRÁFICA DE EFICIENCIA
        # =========================================================

        st.subheader("14. Gráfica de eficiencia")

        fig2, ax2 = plt.subplots(figsize=(6, 5))

        ax2.bar(
            ["Eficiencia estimada"],
            [eficiencia]
        )

        ax2.axhline(
            y=100,
            linestyle="--",
            label="Meta ideal 100%"
        )

        ax2.set_ylabel("Eficiencia (%)")
        ax2.set_title("Eficiencia estimada de la línea")
        ax2.set_ylim(0, max(110, eficiencia + 10))
        ax2.grid(axis="y", alpha=0.3)
        ax2.legend()

        st.pyplot(fig2)

        # =========================================================
        # PRODUCCIÓN IDEAL VS PRODUCCIÓN ESTIMADA
        # =========================================================

        st.subheader("15. Producción ideal vs producción estimada")

        fig3, ax3 = plt.subplots(figsize=(7, 5))

        ax3.bar(
            ["Producción ideal", "Producción estimada"],
            [botellas_ideales, botellas_reales]
        )

        ax3.set_ylabel("Botellas por turno")
        ax3.set_title("Producción ideal vs producción estimada")
        ax3.grid(axis="y", alpha=0.3)

        st.pyplot(fig3)

        # =========================================================
        # EXPORTAR RESULTADOS A EXCEL
        # =========================================================

        st.subheader("16. Descargar resultados")

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            asignaciones_df.to_excel(
                writer,
                sheet_name="Asignaciones",
                index=False
            )

            desv_df.to_excel(
                writer,
                sheet_name="Desviaciones",
                index=False
            )

            resumen_produccion_df.to_excel(
                writer,
                sheet_name="Produccion_Eficiencia",
                index=False
            )

            candidatos_llenadora_df.to_excel(
                writer,
                sheet_name="Candidatos_Llenadora",
                index=False
            )

            workers_turno[["ID_Worker", "Schedule"]].to_excel(
                writer,
                sheet_name="Operarios_Turno",
                index=False
            )

        output.seek(0)

        nombre_salida = f"resultados_modelo_turno_{turno}_con_eficiencia.xlsx"

        st.download_button(
            label="Descargar resultados en Excel",
            data=output,
            file_name=nombre_salida,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # =========================================================
        # EXPLICACIÓN FINAL
        # =========================================================

        st.subheader("17. Explicación del resultado")

        st.write(
            "La producción total se calcula usando la llenadora como cuello de botella."
        )

        st.latex(
            r"\text{Producción estimada} = \text{velocidad alcanzada en llenadora} \times \text{minutos del turno}"
        )

        st.write(
            "La eficiencia se calcula comparando la producción estimada contra la producción ideal."
        )

        st.latex(
            r"\text{Eficiencia} = \frac{\text{producción estimada}}{\text{producción ideal}} \times 100"
        )

        st.write(
            "Donde la producción ideal se calcula como la velocidad estándar de la llenadora "
            "multiplicada por los minutos del turno."
        )

        st.write(
            "En este modelo, la llenadora tiene prioridad porque es el cuello de botella. "
            "Por eso se penaliza fuertemente cuando la llenadora queda por debajo de su velocidad ideal."
        )

    except Exception as e:
        st.error("Ocurrió un error al ejecutar el modelo.")
        st.exception(e)

else:
    st.info(
        "Selecciona el turno, marca los ausentes y presiona el botón para calcular."
    )
