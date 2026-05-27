# ============================================================
# MODELO COMPLETO DE ASIGNACIÓN DE PERSONAL
# CON AUSENTISMO, PRIORIDAD EN LLENADORA, PRODUCCIÓN Y EFICIENCIA
# CORREGIDO A 403 MINUTOS EFECTIVOS
# ============================================================

!pip install pulp openpyxl

import pandas as pd
import matplotlib.pyplot as plt
from pulp import *
from google.colab import files


# =========================================================
# 1. CARGAR ARCHIVO
# =========================================================

print("Sube el archivo Excel")

uploaded = files.upload()

archivo = list(uploaded.keys())[0]


# =========================================================
# 2. LEER HOJAS
# =========================================================

tasks_df = pd.read_excel(
    archivo,
    sheet_name='Tasks'
)

rel_speed_df = pd.read_excel(
    archivo,
    sheet_name='Rel_Speed'
)

workers_df = pd.read_excel(
    archivo,
    sheet_name='Workers'
)

abilities_df = pd.read_excel(
    archivo,
    sheet_name='Abilities'
)

speed_df = pd.read_excel(
    archivo,
    sheet_name='Speed_Factor'
)


# =========================================================
# 3. CORREGIR TIPOS
# =========================================================

tasks_df['ID_Task'] = tasks_df['ID_Task'].astype(str)
rel_speed_df['ID_Task'] = rel_speed_df['ID_Task'].astype(str)

workers_df['ID_Worker'] = workers_df['ID_Worker'].astype(str)
abilities_df['ID_Worker'] = abilities_df['ID_Worker'].astype(str)
speed_df['ID_Worker'] = speed_df['ID_Worker'].astype(str)

workers_df['Schedule'] = workers_df['Schedule'].astype(str)

tasks_df['Task'] = tasks_df['Task'].astype(str).str.strip()
rel_speed_df['Machine'] = rel_speed_df['Machine'].astype(str).str.strip()
workers_df['Name'] = workers_df['Name'].astype(str).str.strip()


# =========================================================
# 4. SELECCIÓN TURNO
# =========================================================

print("\nTURNOS DISPONIBLES:")
print(workers_df['Schedule'].unique())

turno = input(
    "\nIngrese turno (0, 2, 3): "
).strip()


# =========================================================
# 5. FILTRAR TRABAJADORES DEL TURNO
# =========================================================

workers_turno = workers_df[
    workers_df['Schedule'] == str(turno)
].copy()

print("\nTRABAJADORES PROGRAMADOS:\n")

display(
    workers_turno[
        ['ID_Worker', 'Name']
    ]
)


# =========================================================
# 6. AUSENTISMO
# =========================================================

ausentes = input(
    "\nIngrese IDs ausentes separados por coma. Si no faltó nadie, presione Enter: "
)

ausentes = [
    x.strip()
    for x in ausentes.split(',')
    if x.strip() != ''
]


# =========================================================
# 7. TRABAJADORES PRESENTES
# =========================================================

trabajadores = list(
    workers_turno['ID_Worker']
)

presentes = [
    i for i in trabajadores
    if i not in ausentes
]

print("\nTRABAJADORES PRESENTES:\n")
print(presentes)

if len(presentes) == 0:
    raise ValueError("No hay trabajadores presentes. No se puede resolver el modelo.")


# =========================================================
# 8. CONJUNTOS
# =========================================================

tareas = list(
    tasks_df['ID_Task']
)


# =========================================================
# 9. PARÁMETROS DEL EXCEL
# =========================================================

# m_j = 1 si la tarea necesita máquina, 0 si no necesita máquina
m = dict(
    zip(
        tasks_df['ID_Task'],
        tasks_df['Need_Mac']
    )
)

# Nombre de cada tarea
nombre_tarea = dict(
    zip(
        tasks_df['ID_Task'],
        tasks_df['Task']
    )
)

# ID de tarea a partir del nombre de tarea
taskname_to_id = dict(
    zip(
        tasks_df['Task'],
        tasks_df['ID_Task']
    )
)

# Velocidad nominal de cada máquina
V_std = dict(
    zip(
        rel_speed_df['ID_Task'],
        rel_speed_df['Nominal_Sp']
    )
)

# Nombre de máquina asociada
machine_name = dict(
    zip(
        rel_speed_df['ID_Task'],
        rel_speed_df['Machine']
    )
)


# =========================================================
# 10. MATRIZ DE HABILIDADES
# =========================================================

H = {}

for _, row in abilities_df.iterrows():

    worker = row['ID_Worker']

    H[worker] = {}

    for tarea in abilities_df.columns[2:]:

        H[worker][tarea] = row[tarea]


# =========================================================
# 11. MATRIZ SPEED FACTOR
# =========================================================

F = {}

for _, row in speed_df.iterrows():

    worker = row['ID_Worker']

    F[worker] = {}

    for tarea in speed_df.columns[2:]:

        F[worker][tarea] = row[tarea]


# =========================================================
# 12. IDENTIFICAR LLENADORA
# =========================================================

# Según el archivo que vienen usando, la llenadora es ID_Task = '9'.
# Si en otro archivo cambia, modifica este valor.
ID_LLENADORA = '9'

if ID_LLENADORA not in tareas:
    raise ValueError(
        "El ID de llenadora definido no existe en las tareas. "
        "Revisa ID_LLENADORA."
    )

print("\n======================")
print("LLENADORA IDENTIFICADA")
print("======================")

print("ID llenadora:", ID_LLENADORA)
print("Tarea:", nombre_tarea[ID_LLENADORA])
print("Máquina:", machine_name[ID_LLENADORA])
print("Velocidad estándar:", V_std[ID_LLENADORA], "botellas/min")


# =========================================================
# 13. TABLA DE CANDIDATOS PARA LA LLENADORA
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

    nombre_operario = workers_df[
        workers_df['ID_Worker'] == i
    ]['Name'].values[0]

    candidatos_llenadora.append([
        i,
        nombre_operario,
        H[i][nombre_llenadora],
        F[i][nombre_llenadora],
        velocidad_estimada,
        deficit_candidato,
        exceso_candidato
    ])

candidatos_llenadora_df = pd.DataFrame(
    candidatos_llenadora,
    columns=[
        'ID_Worker',
        'Trabajador',
        'Habilidad_Llenadora',
        'Speed_Factor_Llenadora',
        'Velocidad_Estimada_Llenadora',
        'Deficit_vs_Estandar',
        'Exceso_vs_Estandar'
    ]
)

candidatos_llenadora_df = candidatos_llenadora_df.sort_values(
    by=[
        'Deficit_vs_Estandar',
        'Velocidad_Estimada_Llenadora',
        'Habilidad_Llenadora'
    ],
    ascending=[
        True,
        False,
        False
    ]
)

print("\n======================")
print("CANDIDATOS PARA LLENADORA")
print("======================")

display(candidatos_llenadora_df)


# =========================================================
# 14. CREAR MODELO
# =========================================================

modelo = LpProblem(
    "Asignacion_Optima_Con_Eficiencia",
    LpMinimize
)


# =========================================================
# 15. VARIABLES
# =========================================================

# x_ij = 1 si trabajador i se asigna a tarea j
x = LpVariable.dicts(
    "x",
    [(i, j) for i in presentes for j in tareas],
    cat='Binary'
)

# Velocidad real alcanzada en cada tarea
V_real = LpVariable.dicts(
    "V_real",
    tareas,
    lowBound=0
)

# Desviación absoluta general
d = LpVariable.dicts(
    "d",
    tareas,
    lowBound=0
)

# Déficit: solo mide cuando una máquina queda por debajo
deficit = LpVariable.dicts(
    "deficit",
    tareas,
    lowBound=0
)

# Exceso: mide cuando una máquina queda por encima
exceso = LpVariable.dicts(
    "exceso",
    tareas,
    lowBound=0
)

# y_i = 1 si trabajador i cubre más de una tarea
y = LpVariable.dicts(
    "y",
    presentes,
    cat='Binary'
)


# =========================================================
# 16. PARÁMETROS DEL MODELO
# =========================================================

# Premio pequeño por habilidad
epsilon = 0.0001

# Penalización por doble asignación
lambda_pen = 100

# Penalización muy alta si la llenadora queda por debajo
# Este valor hace que el modelo proteja la producción.
peso_deficit_llenadora = 10000

# Penalización normal para desviaciones de otras máquinas
peso_desviacion_otras = 1

# Habilidad mínima para asignar.
# Si quieres permitir todas las asignaciones, pon 0.
habilidad_minima = 0

# Máximo de tareas por trabajador
max_tareas_por_trabajador = 2

# Minutos efectivos de operación del turno
# CORRECCIÓN: antes se usaban 480 minutos.
# Ahora se usan 403 minutos efectivos.
MINUTOS_EFECTIVOS_TURNO = 403


# =========================================================
# 17. FUNCIÓN OBJETIVO CORREGIDA
# =========================================================

# Para la llenadora:
# Se penaliza fuertemente SOLO si queda por debajo.
penalizacion_llenadora = (
    peso_deficit_llenadora * deficit[ID_LLENADORA]
)

# Para las demás máquinas:
# Se minimiza la desviación absoluta normal.
penalizacion_otras_maquinas = lpSum(
    peso_desviacion_otras * d[j]
    for j in tareas
    if m[j] == 1 and j != ID_LLENADORA
)

# Penalización por doble asignación
penalizacion_doble = lambda_pen * lpSum(
    y[i]
    for i in presentes
)

# Premio por habilidad
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
# 18. RESTRICCIONES
# =========================================================

# ---------------------------------------------------------
# Cada tarea debe cubrirse exactamente por un trabajador
# ---------------------------------------------------------

for j in tareas:

    modelo += (
        lpSum(
            x[(i, j)]
            for i in presentes
        ) == 1
    )


# ---------------------------------------------------------
# Doble asignación
# Si un trabajador tiene más de una tarea, y_i se activa
# ---------------------------------------------------------

for i in presentes:

    modelo += (
        lpSum(
            x[(i, j)]
            for j in tareas
        )
        <=
        1 + y[i]
    )


# ---------------------------------------------------------
# Máximo de tareas por trabajador
# ---------------------------------------------------------

for i in presentes:

    modelo += (
        lpSum(
            x[(i, j)]
            for j in tareas
        )
        <=
        max_tareas_por_trabajador
    )


# ---------------------------------------------------------
# No asignar trabajador si no tiene habilidad suficiente
# ---------------------------------------------------------

for i in presentes:

    for j in tareas:

        nombre = nombre_tarea[j]

        if H[i][nombre] < habilidad_minima:

            modelo += (
                x[(i, j)] == 0
            )


# ---------------------------------------------------------
# Velocidad real
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Desviación absoluta, déficit y exceso
# ---------------------------------------------------------

for j in tareas:

    if m[j] == 1:

        # Desviación absoluta
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

        # Déficit por debajo
        modelo += (
            deficit[j]
            >=
            V_std[j] - V_real[j]
        )

        # Exceso por encima
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
# 19. RESOLVER
# =========================================================

modelo.solve()


# =========================================================
# 20. ESTADO
# =========================================================

print("\n======================")
print("ESTADO")
print("======================")

print(
    LpStatus[modelo.status]
)

if LpStatus[modelo.status] != "Optimal":
    print("\nEl modelo no encontró solución óptima.")
    print("Revisa si hay suficientes trabajadores presentes o si las restricciones son muy fuertes.")


# =========================================================
# 21. ASIGNACIONES
# =========================================================

print("\n======================")
print("ASIGNACIONES")
print("======================")

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
            workers_df['ID_Worker'] == i
        ]['Name'].values[0]

        asignaciones.append([
            i,
            nombre_operario,
            ", ".join(tareas_asig)
        ])

asignaciones_df = pd.DataFrame(
    asignaciones,
    columns=[
        'ID_Worker',
        'Trabajador',
        'Tareas Asignadas'
    ]
)

display(asignaciones_df)


# =========================================================
# 22. DESVIACIONES
# =========================================================

desviaciones = []

for j in tareas:

    if m[j] == 1:

        desviaciones.append([

            j,

            nombre_tarea[j],

            machine_name[j],

            round(
                V_std[j],
                2
            ),

            round(
                value(V_real[j]),
                2
            ),

            round(
                value(d[j]),
                2
            ),

            round(
                value(deficit[j]),
                2
            ),

            round(
                value(exceso[j]),
                2
            )

        ])

desv_df = pd.DataFrame(
    desviaciones,
    columns=[
        'ID_Task',
        'Tarea',
        'Maquina',
        'Velocidad_Estandar',
        'Velocidad_Alcanzada',
        'Desviacion_Absoluta',
        'Deficit_Por_Debajo',
        'Exceso_Por_Encima'
    ]
)

print("\n======================")
print("DESVIACIONES")
print("======================")

display(desv_df)


# =========================================================
# 23. REVISIÓN ESPECIAL DE LA LLENADORA
# =========================================================

print("\n======================")
print("REVISIÓN ESPECIAL LLENADORA")
print("======================")

fila_llenadora = desv_df[
    desv_df['ID_Task'] == ID_LLENADORA
]

display(fila_llenadora)

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

print("Velocidad ideal llenadora:", round(velocidad_ideal_llenadora, 2), "botellas/min")
print("Velocidad alcanzada llenadora:", round(velocidad_llenadora, 2), "botellas/min")
print("Déficit llenadora:", round(deficit_llenadora, 2), "botellas/min")
print("Exceso llenadora:", round(exceso_llenadora, 2), "botellas/min")

if deficit_llenadora > 0:
    print("\nLa llenadora quedó por debajo de la velocidad ideal.")
    print("Esto reduce la producción del turno.")
else:
    print("\nLa llenadora no quedó por debajo de la velocidad ideal.")
    print("No hay pérdida por cuello de botella en llenadora.")


# =========================================================
# 24. PRODUCCIÓN TOTAL Y EFICIENCIA
# =========================================================

# CORRECCIÓN:
# Antes se multiplicaba por 480.
# Ahora se multiplica por 403 minutos efectivos.

botellas_reales = velocidad_llenadora * MINUTOS_EFECTIVOS_TURNO

botellas_ideales = velocidad_ideal_llenadora * MINUTOS_EFECTIVOS_TURNO

eficiencia = (
    botellas_reales / botellas_ideales
) * 100

perdida_botellas = botellas_ideales - botellas_reales

print("\n======================")
print("PRODUCCIÓN TOTAL Y EFICIENCIA")
print("======================")

print("Minutos efectivos usados:", MINUTOS_EFECTIVOS_TURNO)
print("Velocidad ideal llenadora:", round(velocidad_ideal_llenadora, 2), "botellas/min")
print("Velocidad alcanzada llenadora:", round(velocidad_llenadora, 2), "botellas/min")

print("\nProducción ideal del turno:", round(botellas_ideales, 0), "botellas/turno")
print("Producción estimada del turno:", round(botellas_reales, 0), "botellas/turno")

print("\nPérdida estimada:", round(perdida_botellas, 0), "botellas/turno")

print("\nEficiencia estimada de la línea:", round(eficiencia, 2), "%")


# =========================================================
# 25. TABLA RESUMEN DE PRODUCCIÓN
# =========================================================

resumen_produccion_df = pd.DataFrame({
    'Indicador': [
        'Minutos efectivos del turno',
        'Velocidad ideal llenadora',
        'Velocidad alcanzada llenadora',
        'Producción ideal del turno',
        'Producción estimada del turno',
        'Pérdida estimada del turno',
        'Eficiencia estimada'
    ],
    'Valor': [
        MINUTOS_EFECTIVOS_TURNO,
        round(velocidad_ideal_llenadora, 2),
        round(velocidad_llenadora, 2),
        round(botellas_ideales, 0),
        round(botellas_reales, 0),
        round(perdida_botellas, 0),
        round(eficiencia, 2)
    ],
    'Unidad': [
        'minutos',
        'botellas/min',
        'botellas/min',
        'botellas/turno',
        'botellas/turno',
        'botellas/turno',
        '%'
    ]
})

print("\n======================")
print("RESUMEN PRODUCCIÓN Y EFICIENCIA")
print("======================")

display(resumen_produccion_df)


# =========================================================
# 26. CURVA VELOCIDAD IDEAL VS VELOCIDAD ALCANZADA
# =========================================================

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

plt.figure(figsize=(12, 6))

plt.plot(
    maquinas,
    vel_ideal,
    marker='o',
    label='Velocidad Ideal'
)

plt.plot(
    maquinas,
    vel_real,
    marker='o',
    label='Velocidad Alcanzada'
)

plt.xlabel("Máquinas")
plt.ylabel("Velocidad botellas/min")
plt.title("Curva Ideal vs Real")
plt.xticks(rotation=45)
plt.grid(True)
plt.legend()
plt.show()


# =========================================================
# 27. GRÁFICA DE EFICIENCIA
# =========================================================

plt.figure(figsize=(6, 5))

plt.bar(
    ["Eficiencia estimada"],
    [eficiencia]
)

plt.axhline(
    y=100,
    linestyle="--",
    label="Meta ideal 100%"
)

plt.ylabel("Eficiencia (%)")
plt.title("Eficiencia estimada de la línea")
plt.ylim(0, max(110, eficiencia + 10))
plt.grid(axis="y", alpha=0.3)
plt.legend()
plt.show()


# =========================================================
# 28. GRÁFICA PRODUCCIÓN IDEAL VS PRODUCCIÓN ESTIMADA
# =========================================================

plt.figure(figsize=(7, 5))

plt.bar(
    ["Producción ideal", "Producción estimada"],
    [botellas_ideales, botellas_reales]
)

plt.ylabel("Botellas por turno")
plt.title("Producción ideal vs producción estimada")
plt.grid(axis="y", alpha=0.3)
plt.show()


# =========================================================
# 29. EXPORTAR RESULTADOS A EXCEL
# =========================================================

nombre_salida = f"resultados_modelo_turno_{turno}_con_eficiencia_403min.xlsx"

with pd.ExcelWriter(nombre_salida, engine='openpyxl') as writer:

    asignaciones_df.to_excel(
        writer,
        sheet_name='Asignaciones',
        index=False
    )

    desv_df.to_excel(
        writer,
        sheet_name='Desviaciones',
        index=False
    )

    resumen_produccion_df.to_excel(
        writer,
        sheet_name='Produccion_Eficiencia',
        index=False
    )

    candidatos_llenadora_df.to_excel(
        writer,
        sheet_name='Candidatos_Llenadora',
        index=False
    )

    workers_turno[['ID_Worker', 'Name', 'Schedule']].to_excel(
        writer,
        sheet_name='Trabajadores_Turno',
        index=False
    )

print("\n======================")
print("ARCHIVO EXPORTADO")
print("======================")

print("Archivo creado:", nombre_salida)

files.download(nombre_salida)


# =========================================================
# 30. EXPLICACIÓN FINAL
# =========================================================

print("\n======================")
print("EXPLICACIÓN DEL RESULTADO")
print("======================")

print("""
La producción total se calcula usando la llenadora como cuello de botella.

En esta versión corregida, la producción ya no se calcula con 480 minutos,
sino con 403 minutos efectivos de operación.

Producción estimada = velocidad alcanzada en llenadora * 403 minutos efectivos

La eficiencia se calcula comparando la producción estimada contra la producción ideal:

Eficiencia = (producción estimada / producción ideal) * 100

Donde:

Producción ideal = velocidad estándar de la llenadora * 403 minutos efectivos

Si la llenadora queda por debajo de su velocidad estándar, la eficiencia baja.
Si la llenadora alcanza o supera su velocidad estándar, la eficiencia se acerca o supera el 100%.

En este modelo corregido, la llenadora tiene prioridad porque es el cuello de botella.
Por eso se penaliza fuertemente cuando la llenadora queda por debajo de su velocidad ideal.
""")
