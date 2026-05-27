import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pulp import *
from io import BytesIO

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Dashboard de Asignación de Personal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# PARÁMETROS TÉCNICOS OCULTOS
# ============================================================

ID_LLENADORA = "9"
epsilon = 0.0001
lambda_pen = 100
peso_deficit_llenadora = 10000
peso_desviacion_otras = 1
habilidad_minima = 1

# ============================================================
# ESTILO VISUAL
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f2fbf6 0%, #eef8f2 45%, #f7fafc 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    .hero {
        background: linear-gradient(135deg, #064e3b 0%, #0f766e 48%, #16a34a 100%);
        padding: 2.3rem 2.5rem;
        border-radius: 28px;
        color: white;
        margin-bottom: 1.4rem;
        box-shadow: 0 20px 45px rgba(6, 78, 59, 0.22);
    }

    .hero h1 {
        font-size: 2.45rem;
        margin-bottom: 0.55rem;
        font-weight: 900;
        letter-spacing: -0.035em;
    }

    .hero p {
        font-size: 1.05rem;
        line-height: 1.6;
        opacity: 0.96;
        margin: 0;
        max-width: 970px;
    }

    .privacy-box {
        background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
        border: 1px solid #86efac;
        color: #14532d;
        padding: 1rem 1.2rem;
        border-radius: 20px;
        margin-bottom: 1.4rem;
        font-weight: 600;
        box-shadow: 0 6px 18px rgba(22, 163, 74, 0.08);
    }

    .section-title {
        font-size: 1.45rem;
        font-weight: 850;
        margin-top: 1.6rem;
        margin-bottom: 0.85rem;
        color: #064e3b;
        letter-spacing: -0.01em;
    }

    .card {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 24px;
        padding: 1.3rem;
        border: 1px solid #d9f2e3;
        box-shadow: 0 10px 28px rgba(6, 78, 59, 0.07);
        margin-bottom: 1rem;
    }

    .metric-card {
        background: white;
        border-radius: 24px;
        padding: 1.25rem 1.3rem;
        border: 1px solid #d9f2e3;
        box-shadow: 0 10px 26px rgba(6, 78, 59, 0.08);
        min-height: 130px;
    }

    .metric-label {
        font-size: 0.86rem;
        font-weight: 800;
        color: #407060;
        margin-bottom: 0.45rem;
    }

    .metric-value {
        font-size: 2.08rem;
        font-weight: 900;
        color: #052e26;
        margin-bottom: 0.25rem;
    }

    .metric-foot {
        font-size: 0.84rem;
        color: #64756d;
    }

    .green {
        border-left: 8px solid #16a34a;
    }

    .darkgreen {
        border-left: 8px solid #064e3b;
    }

    .mint {
        border-left: 8px solid #34d399;
    }

    .teal {
        border-left: 8px solid #0f766e;
    }

    .lime {
        border-left: 8px solid #84cc16;
    }

    .red {
        border-left: 8px solid #dc2626;
    }

    .orange {
        border-left: 8px solid #f59e0b;
    }

    .id-chip {
        display: inline-block;
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        color: #064e3b;
        border: 1px solid #86efac;
        padding: 0.48rem 0.82rem;
        border-radius: 999px;
        margin: 0.25rem;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 4px 10px rgba(22, 163, 74, 0.12);
    }

    .status-good {
        background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
        color: #14532d;
        border: 1px solid #86efac;
        padding: 1rem;
        border-radius: 20px;
        font-weight: 750;
        box-shadow: 0 6px 18px rgba(22, 163, 74, 0.10);
    }

    .soft-note {
        background: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
        padding: 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    div[data-testid="stFileUploader"] section {
        border-radius: 20px;
        border: 1px dashed #86efac;
        background: #ffffff;
    }

    .stButton > button {
        background: linear-gradient(135deg, #064e3b 0%, #16a34a 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.78rem 1.35rem;
        font-weight: 850;
        box-shadow: 0 10px 22px rgba(22, 163, 74, 0.24);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #0f766e 0%, #22c55e 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.78rem 1.35rem;
        font-weight: 850;
        box-shadow: 0 10px 22px rgba(15, 118, 110, 0.22);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def metric_card(label, value, foot="", style_class="green"):
    st.markdown(
        f"""
        <div class="metric-card {style_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def id_chips(ids):
    if len(ids) == 0:
        st.warning("No hay operarios para mostrar.")
        return

    chips = "".join(
        [f'<span class="id-chip">ID {str(i)}</span>' for i in ids]
    )

    st.markdown(chips, unsafe_allow_html=True)


def obtener_columnas_tareas(df):
    columnas_no_tareas = [
        "ID_Worker",
        "Name",
        "Nombre",
        "Position",
        "Schedule",
        "Turno"
    ]

    columnas_tareas = [
        col for col in df.columns
        if str(col).strip() not in columnas_no_tareas
    ]

    return columnas_tareas


def construir_matriz(df):
    columnas_tareas = obtener_columnas_tareas(df)

    matriz = {}

    for _, row in df.iterrows():

        worker = str(row["ID_Worker"]).strip()

        matriz[worker] = {}

        for tarea in columnas_tareas:

            valor = row[tarea]

            if pd.isna(valor):
                valor = 0

            matriz[worker][str(tarea).strip()] = float(valor)

    return matriz, columnas_tareas


def tabla_verde(df):
    columnas_numericas = df.select_dtypes(include=["number"]).columns.tolist()

    if len(columnas_numericas) > 0:
        return (
            df.style
            .background_gradient(
                subset=columnas_numericas,
                cmap="Greens"
            )
            .set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#064e3b"),
                            ("color", "white"),
                            ("font-weight", "bold")
                        ]
                    },
                    {
                        "selector": "td",
                        "props": [
                            ("border-color", "#d9f2e3")
                        ]
                    }
                ]
            )
        )

    return (
        df.style
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#064e3b"),
                        ("color", "white"),
                        ("font-weight", "bold")
                    ]
                }
            ]
        )
    )


def ordenar_maquinas(df):
    orden_deseado = [
        "Descapsuladora",
        "Lavadora",
        "Llenadora",
        "Etiquetadora",
        "Empacadora",
        "Paletizadora"
    ]

    df = df.copy()

    df["Orden_Maquina"] = df["Maquina"].apply(
        lambda x: orden_deseado.index(x)
        if x in orden_deseado
        else 999
    )

    df = df.sort_values(
        ["Orden_Maquina", "ID_Task"]
    ).drop(
        columns=["Orden_Maquina"]
    )

    return df


# ============================================================
# ENCABEZADO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>Dashboard de Asignación Óptima de Personal</h1>
        <p>
        Herramienta interactiva para apoyar la asignación de operarios por turno,
        considerando ausentismo, habilidades, velocidades relativas, prioridad de la llenadora,
        producción estimada y eficiencia de la línea.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="privacy-box">
        Por confidencialidad, el dashboard trabaja únicamente con el ID del operario.
        No se muestran nombres del personal en pantalla ni en el archivo de resultados.
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 1. CARGAR ARCHIVO
# ============================================================

st.markdown(
    '<div class="section-title">1. Cargar archivo Excel</div>',
    unsafe_allow_html=True
)

archivo = st.file_uploader(
    "Sube el archivo Excel del modelo",
    type=["xlsx"]
)

if archivo is None:
    st.info("Sube el archivo Excel para iniciar el análisis.")
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
# 3. LIMPIEZA DE TIPOS
# ============================================================

try:
    tasks_df["ID_Task"] = tasks_df["ID_Task"].astype(str).str.strip()
    rel_speed_df["ID_Task"] = rel_speed_df["ID_Task"].astype(str).str.strip()

    workers_df["ID_Worker"] = workers_df["ID_Worker"].astype(str).str.strip()
    abilities_df["ID_Worker"] = abilities_df["ID_Worker"].astype(str).str.strip()
    speed_df["ID_Worker"] = speed_df["ID_Worker"].astype(str).str.strip()

    workers_df["Schedule"] = workers_df["Schedule"].astype(str).str.strip()

    tasks_df["Task"] = tasks_df["Task"].astype(str).str.strip()
    rel_speed_df["Machine"] = rel_speed_df["Machine"].astype(str).str.strip()

    abilities_df.columns = [
        str(col).strip()
        for col in abilities_df.columns
    ]

    speed_df.columns = [
        str(col).strip()
        for col in speed_df.columns
    ]

except Exception as e:
    st.error("Hay un problema con los nombres de columnas del Excel.")
    st.exception(e)
    st.stop()

# ============================================================
# 4. REVISAR DATOS CARGADOS
# ============================================================

st.markdown(
    '<div class="section-title">2. Revisar datos cargados</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Tareas",
        "Velocidades",
        "Operarios",
        "Habilidades",
        "Factores de velocidad"
    ]
)

with tab1:
    st.dataframe(
        tabla_verde(tasks_df),
        use_container_width=True
    )

with tab2:
    st.dataframe(
        tabla_verde(rel_speed_df),
        use_container_width=True
    )

with tab3:
    columnas_workers = [
        col for col in ["ID_Worker", "Schedule"]
        if col in workers_df.columns
    ]

    st.dataframe(
        tabla_verde(workers_df[columnas_workers]),
        use_container_width=True
    )

with tab4:
    st.dataframe(
        tabla_verde(abilities_df),
        use_container_width=True
    )

with tab5:
    st.dataframe(
        tabla_verde(speed_df),
        use_container_width=True
    )

# ============================================================
# 5. CONFIGURACIÓN OPERATIVA
# ============================================================

st.markdown(
    '<div class="section-title">3. Configuración operativa</div>',
    unsafe_allow_html=True
)

col_conf1, col_conf2, col_conf3 = st.columns(
    [1.2, 1, 1]
)

with col_conf1:
    turnos_disponibles = sorted(
        workers_df["Schedule"].dropna().unique().tolist()
    )

    turno = st.selectbox(
        "Selecciona el turno",
        turnos_disponibles
    )

with col_conf2:
    max_tareas_por_trabajador = st.number_input(
        "Máximo de tareas por operario",
        min_value=1,
        max_value=10,
        value=2,
        step=1
    )

with col_conf3:
    minutos_turno = st.number_input(
        "Minutos del turno",
        min_value=1,
        value=480,
        step=1
    )

workers_turno = workers_df[
    workers_df["Schedule"] == str(turno)
].copy()

if len(workers_turno) == 0:
    st.error("No hay operarios programados para este turno.")
    st.stop()

st.markdown(
    '<div class="section-title">4. Operarios del turno</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

st.write("Operarios programados en el turno seleccionado:")

st.dataframe(
    tabla_verde(workers_turno[["ID_Worker", "Schedule"]]),
    use_container_width=True
)

st.markdown(
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# 6. AUSENTISMO
# ============================================================

st.markdown(
    '<div class="section-title">5. Seleccionar ausentes</div>',
    unsafe_allow_html=True
)

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

m1, m2, m3 = st.columns(3)

with m1:
    metric_card(
        "Operarios programados",
        len(trabajadores),
        "Total en el turno seleccionado",
        "teal"
    )

with m2:
    metric_card(
        "Operarios ausentes",
        len(ausentes),
        "IDs marcados como no disponibles",
        "orange"
    )

with m3:
    metric_card(
        "Operarios presentes",
        len(presentes),
        "Personal disponible para asignar",
        "green"
    )

st.markdown(
    '<div class="card">',
    unsafe_allow_html=True
)

st.write("ID de operarios presentes:")

id_chips(presentes)

st.markdown(
    '</div>',
    unsafe_allow_html=True
)

if len(presentes) == 0:
    st.error("No hay operarios presentes. No se puede resolver el modelo.")
    st.stop()

# ============================================================
# 7. EJECUTAR MODELO
# ============================================================

st.markdown(
    '<div class="section-title">6. Ejecutar optimización</div>',
    unsafe_allow_html=True
)

if st.button(
    "Calcular asignación óptima",
    type="primary"
):

    try:
        # ========================================================
        # CONJUNTOS Y PARÁMETROS
        # ========================================================

        tareas = list(
            tasks_df["ID_Task"]
        )

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

        # ========================================================
        # MATRICES
        # ========================================================

        H, columnas_habilidades = construir_matriz(
            abilities_df
        )

        F, columnas_speed = construir_matriz(
            speed_df
        )

        # ========================================================
        # VALIDACIONES
        # ========================================================

        errores = []

        for i in presentes:

            if i not in H:
                errores.append(
                    f"El operario con ID {i} no aparece en Abilities."
                )

            if i not in F:
                errores.append(
                    f"El operario con ID {i} no aparece en Speed_Factor."
                )

        tareas_faltantes_abilities = []
        tareas_faltantes_speed = []

        for j in tareas:

            nombre = nombre_tarea[j]

            if nombre not in columnas_habilidades:
                tareas_faltantes_abilities.append(nombre)

            if nombre not in columnas_speed:
                tareas_faltantes_speed.append(nombre)

        if len(tareas_faltantes_abilities) > 0:
            errores.append(
                "Estas tareas no aparecen como columnas en Abilities: "
                + ", ".join(sorted(set(tareas_faltantes_abilities)))
            )

        if len(tareas_faltantes_speed) > 0:
            errores.append(
                "Estas tareas no aparecen como columnas en Speed_Factor: "
                + ", ".join(sorted(set(tareas_faltantes_speed)))
            )

        if len(errores) > 0:
            st.error("Hay errores en la estructura del archivo.")
            for error in errores:
                st.write(error)
            st.stop()

        # ========================================================
        # CANDIDATOS PARA LLENADORA
        # ========================================================

        candidatos_llenadora = []

        nombre_llenadora = nombre_tarea[
            ID_LLENADORA
        ]

        for i in presentes:

            velocidad_estimada = (
                V_std[ID_LLENADORA]
                *
                F[i][nombre_llenadora]
            )

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

        # ========================================================
        # CREAR MODELO
        # ========================================================

        modelo = LpProblem(
            "Asignacion_Optima_Con_Eficiencia",
            LpMinimize
        )

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

        # ========================================================
        # FUNCIÓN OBJETIVO
        # ========================================================

        penalizacion_llenadora = (
            peso_deficit_llenadora
            *
            deficit[ID_LLENADORA]
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

        # ========================================================
        # RESTRICCIONES
        # ========================================================

        for j in tareas:
            modelo += (
                lpSum(
                    x[(i, j)]
                    for i in presentes
                ) == 1
            )

        for i in presentes:
            modelo += (
                lpSum(
                    x[(i, j)]
                    for j in tareas
                )
                <=
                1 + y[i]
            )

        for i in presentes:
            modelo += (
                lpSum(
                    x[(i, j)]
                    for j in tareas
                )
                <=
                max_tareas_por_trabajador
            )

        for i in presentes:

            for j in tareas:

                nombre = nombre_tarea[j]

                if H[i][nombre] < habilidad_minima:

                    modelo += (
                        x[(i, j)] == 0
                    )

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

        # ========================================================
        # RESOLVER
        # ========================================================

        solver = PULP_CBC_CMD(
            msg=False
        )

        modelo.solve(
            solver
        )

        estado = LpStatus[
            modelo.status
        ]

        st.markdown(
            '<div class="section-title">7. Estado del modelo</div>',
            unsafe_allow_html=True
        )

        if estado == "Optimal":

            st.markdown(
                '<div class="status-good">Solución óptima encontrada.</div>',
                unsafe_allow_html=True
            )

        else:

            st.error(
                "El modelo no encontró solución óptima. Revisa si hay suficientes operarios presentes o si las restricciones son muy fuertes."
            )

            st.write(
                "Estado:",
                estado
            )

            st.stop()

        # ========================================================
        # ASIGNACIONES
        # ========================================================

        asignaciones = []

        for i in presentes:

            tareas_asig = []

            for j in tareas:

                if value(
                    x[(i, j)]
                ) == 1:

                    tareas_asig.append(
                        nombre_tarea[j]
                    )

            if len(
                tareas_asig
            ) > 0:

                asignaciones.append(
                    [
                        i,
                        ", ".join(
                            tareas_asig
                        )
                    ]
                )

        asignaciones_df = pd.DataFrame(
            asignaciones,
            columns=[
                "ID_Worker",
                "Tareas_Asignadas"
            ]
        )

        # ========================================================
        # DESVIACIONES
        # ========================================================

        desviaciones = []

        for j in tareas:

            if m[j] == 1:

                desviaciones.append(
                    [
                        j,
                        nombre_tarea[j],
                        machine_name[j],
                        round(
                            V_std[j],
                            2
                        ),
                        round(
                            value(
                                V_real[j]
                            ),
                            2
                        ),
                        round(
                            value(
                                d[j]
                            ),
                            2
                        ),
                        round(
                            value(
                                deficit[j]
                            ),
                            2
                        ),
                        round(
                            value(
                                exceso[j]
                            ),
                            2
                        )
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

        desv_df = ordenar_maquinas(
            desv_df
        )

        # ========================================================
        # LLENADORA Y PRODUCCIÓN
        # ========================================================

        fila_llenadora = desv_df[
            desv_df["ID_Task"] == ID_LLENADORA
        ]

        velocidad_llenadora = value(
            V_real[ID_LLENADORA]
        )

        velocidad_ideal_llenadora = V_std[
            ID_LLENADORA
        ]

        deficit_llenadora = value(
            deficit[ID_LLENADORA]
        )

        botellas_reales = (
            velocidad_llenadora
            *
            minutos_turno
        )

        botellas_ideales = (
            velocidad_ideal_llenadora
            *
            minutos_turno
        )

        eficiencia = (
            botellas_reales
            /
            botellas_ideales
        ) * 100

        perdida_botellas = (
            botellas_ideales
            -
            botellas_reales
        )

        # ========================================================
        # RESUMEN EJECUTIVO
        # ========================================================

        st.markdown(
            '<div class="section-title">8. Resumen ejecutivo</div>',
            unsafe_allow_html=True
        )

        r1, r2, r3, r4 = st.columns(
            4
        )

        with r1:

            metric_card(
                "Velocidad llenadora",
                f"{round(velocidad_llenadora, 2)}",
                "botellas/min",
                "green" if deficit_llenadora <= 0 else "orange"
            )

        with r2:

            metric_card(
                "Producción estimada",
                f"{round(botellas_reales, 0):,.0f}",
                "botellas/turno",
                "teal"
            )

        with r3:

            metric_card(
                "Eficiencia estimada",
                f"{round(eficiencia, 2)}%",
                "comparada con producción ideal",
                "green" if eficiencia >= 100 else "lime"
            )

        with r4:

            metric_card(
                "Pérdida estimada",
                f"{round(perdida_botellas, 0):,.0f}",
                "botellas/turno",
                "orange" if perdida_botellas > 0 else "green"
            )

        # Se eliminó la advertencia roja de la llenadora.

        # ========================================================
        # TABLAS
        # ========================================================

        st.markdown(
            '<div class="section-title">9. Asignación óptima</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            tabla_verde(asignaciones_df),
            use_container_width=True
        )

        st.markdown(
            '<div class="section-title">10. Desviaciones por máquina</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            tabla_verde(desv_df),
            use_container_width=True
        )

        st.markdown(
            '<div class="section-title">11. Revisión especial de la llenadora</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            tabla_verde(fila_llenadora),
            use_container_width=True
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
                    round(
                        velocidad_ideal_llenadora,
                        2
                    ),
                    round(
                        velocidad_llenadora,
                        2
                    ),
                    round(
                        botellas_ideales,
                        0
                    ),
                    round(
                        botellas_reales,
                        0
                    ),
                    round(
                        perdida_botellas,
                        0
                    ),
                    round(
                        eficiencia,
                        2
                    )
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

        st.markdown(
            '<div class="section-title">12. Producción y eficiencia</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            tabla_verde(resumen_produccion_df),
            use_container_width=True
        )

        # ========================================================
        # GRÁFICA VELOCIDAD IDEAL VS ALCANZADA
        # ========================================================

        st.markdown(
            '<div class="section-title">13. Visualización de velocidades</div>',
            unsafe_allow_html=True
        )

        grafica_df = desv_df.copy()

        maquinas = grafica_df["Maquina"].tolist()
        vel_ideal = grafica_df["Velocidad_Estandar"].tolist()
        vel_real = grafica_df["Velocidad_Alcanzada"].tolist()

        fig1, ax1 = plt.subplots(
            figsize=(12, 6)
        )

        ax1.plot(
            maquinas,
            vel_ideal,
            marker="o",
            linewidth=3,
            label="Velocidad ideal",
            color="#064e3b"
        )

        ax1.plot(
            maquinas,
            vel_real,
            marker="o",
            linewidth=3,
            label="Velocidad alcanzada",
            color="#22c55e"
        )

        ax1.fill_between(
            range(len(maquinas)),
            vel_ideal,
            vel_real,
            alpha=0.12,
            color="#16a34a"
        )

        ax1.set_xlabel(
            "Máquinas"
        )

        ax1.set_ylabel(
            "Velocidad botellas/min"
        )

        ax1.set_title(
            "Curva de velocidad ideal vs alcanzada"
        )

        ax1.set_xticks(
            range(len(maquinas))
        )

        ax1.set_xticklabels(
            maquinas,
            rotation=45,
            ha="right"
        )

        ax1.grid(
            True,
            alpha=0.25
        )

        ax1.legend()

        st.pyplot(
            fig1
        )

        # Se eliminó la gráfica de producción ideal vs producción estimada.

        fig3, ax3 = plt.subplots(
            figsize=(6, 5)
        )

        ax3.bar(
            [
                "Eficiencia estimada"
            ],
            [
                eficiencia
            ],
            color="#16a34a"
        )

        ax3.axhline(
            y=100,
            linestyle="--",
            label="Meta ideal 100%",
            color="#064e3b"
        )

        ax3.set_ylabel(
            "Eficiencia (%)"
        )

        ax3.set_title(
            "Eficiencia estimada de la línea"
        )

        ax3.set_ylim(
            0,
            max(
                110,
                eficiencia + 10
            )
        )

        ax3.grid(
            axis="y",
            alpha=0.25
        )

        ax3.legend()

        st.pyplot(
            fig3
        )

        # ========================================================
        # DESCARGA
        # ========================================================

        st.markdown(
            '<div class="section-title">14. Descargar resultados</div>',
            unsafe_allow_html=True
        )

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

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

            workers_turno[
                [
                    "ID_Worker",
                    "Schedule"
                ]
            ].to_excel(
                writer,
                sheet_name="Operarios_Turno",
                index=False
            )

        output.seek(
            0
        )

        nombre_salida = (
            f"resultados_modelo_turno_{turno}_con_eficiencia.xlsx"
        )

        st.download_button(
            label="Descargar resultados en Excel",
            data=output,
            file_name=nombre_salida,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ========================================================
        # INTERPRETACIÓN FINAL
        # ========================================================

        st.markdown(
            '<div class="section-title">15. Interpretación del resultado</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="card">
                <p>
                La producción total se calcula usando la llenadora como cuello de botella.
                Esto significa que la velocidad alcanzada en la llenadora limita la producción
                estimada del turno.
                </p>
                <p>
                <b>Producción estimada = velocidad alcanzada en llenadora × minutos del turno</b>
                </p>
                <p>
                La eficiencia se obtiene comparando la producción estimada contra la producción ideal.
                La asignación generada busca proteger la llenadora porque esta tarea tiene impacto directo
                en la producción del turno.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:

        st.error(
            "Ocurrió un error al ejecutar el modelo."
        )

        st.exception(
            e
        )

else:

    st.info(
        "Selecciona el turno, marca los ausentes si aplica y presiona el botón para calcular."
    )
