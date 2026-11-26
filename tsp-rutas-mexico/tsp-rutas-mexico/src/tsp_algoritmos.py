"""
Problema del viajante (TSP) con ciudades de México.
Algoritmos comparados:
  1. Fuerza bruta               -> búsqueda ciega (exhaustiva)
  2. Vecino más cercano         -> búsqueda heurística (greedy)
  3. Hill climbing con 2-opt    -> búsqueda local
  4. Recocido simulado          -> búsqueda local estocástica
  5. Algoritmo genético         -> búsqueda evolutiva

Solo usa la biblioteca estándar. Si tienes matplotlib instalado
(pip install matplotlib) también guarda gráficas.
"""
import itertools
import math
import random
import time

# ---------------------------------------------------------------
# 1. DATOS DEL PROBLEMA (ciudad: (latitud, longitud))
# ---------------------------------------------------------------
CIUDADES = {
    "Puebla": (19.0414, -98.2063),
    "CDMX": (19.4326, -99.1332),
    "Cuernavaca": (18.9186, -99.2342),
    "Toluca": (19.2826, -99.6557),
    "Queretaro": (20.5888, -100.3899),
    "Pachuca": (20.1011, -98.7591),
    "Tlaxcala": (19.3139, -98.2404),
    "Veracruz": (19.1738, -96.1342),
    "Oaxaca": (17.0732, -96.7266),
    "Acapulco": (16.8531, -99.8237),
}
NOMBRES = list(CIUDADES.keys())
N = len(NOMBRES)


def haversine(a, b):
    """Distancia en km entre dos puntos (lat, lon)."""
    r = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    d = math.sin((la2 - la1) / 2) ** 2 + \
        math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(d))


# Matriz de distancias
DIST = [[haversine(CIUDADES[a], CIUDADES[b]) for b in NOMBRES] for a in NOMBRES]


def costo(ruta):
    """Distancia total de un recorrido que regresa a la ciudad de inicio."""
    return sum(DIST[ruta[i]][ruta[(i + 1) % len(ruta)]] for i in range(len(ruta)))


def mostrar(ruta):
    return " -> ".join(NOMBRES[i] for i in ruta + [ruta[0]])


# ---------------------------------------------------------------
# 2. ALGORITMOS
# ---------------------------------------------------------------
def fuerza_bruta():
    """Búsqueda ciega: prueba todas las permutaciones (ciudad 0 fija)."""
    mejor, mejor_c, evaluadas = None, float("inf"), 0
    for perm in itertools.permutations(range(1, N)):
        ruta = [0] + list(perm)
        c = costo(ruta)
        evaluadas += 1
        if c < mejor_c:
            mejor, mejor_c = ruta, c
    return mejor, mejor_c, evaluadas


def vecino_mas_cercano(inicio=0):
    """Heurística greedy: siempre ir a la ciudad no visitada más cercana."""
    ruta, pendientes = [inicio], set(range(N)) - {inicio}
    while pendientes:
        sig = min(pendientes, key=lambda j: DIST[ruta[-1]][j])
        ruta.append(sig)
        pendientes.remove(sig)
    return ruta, costo(ruta), N * N


def dos_opt(ruta, i, j):
    """Invierte el tramo ruta[i..j] (vecino 2-opt)."""
    return ruta[:i] + ruta[i:j + 1][::-1] + ruta[j + 1:]


def hill_climbing(ruta_inicial=None, semilla=None):
    """Búsqueda local: acepta solo vecinos 2-opt que mejoren la ruta."""
    rnd = random.Random(semilla)
    ruta = ruta_inicial[:] if ruta_inicial else rnd.sample(range(N), N)
    c, evaluadas, mejora = costo(ruta), 0, True
    while mejora:
        mejora = False
        for i in range(1, N - 1):
            for j in range(i + 1, N):
                nueva = dos_opt(ruta, i, j)
                nc = costo(nueva)
                evaluadas += 1
                if nc < c - 1e-9:
                    ruta, c, mejora = nueva, nc, True
    return ruta, c, evaluadas


def recocido_simulado(t0=500.0, enfriamiento=0.995, t_min=0.01, semilla=None):
    """Acepta peores soluciones con probabilidad exp(-delta/T) para escapar
    de óptimos locales; la temperatura baja poco a poco."""
    rnd = random.Random(semilla)
    ruta = rnd.sample(range(N), N)
    c = costo(ruta)
    mejor, mejor_c, t, evaluadas = ruta[:], c, t0, 0
    historial = []
    while t > t_min:
        i, j = sorted(rnd.sample(range(1, N), 2))
        nueva = dos_opt(ruta, i, j)
        nc = costo(nueva)
        evaluadas += 1
        delta = nc - c
        if delta < 0 or rnd.random() < math.exp(-delta / t):
            ruta, c = nueva, nc
            if c < mejor_c:
                mejor, mejor_c = ruta[:], c
        historial.append(mejor_c)
        t *= enfriamiento
    return mejor, mejor_c, evaluadas, historial


def algoritmo_genetico(pob=100, generaciones=300, p_mut=0.2, elite=2,
                       k_torneo=5, semilla=None):
    """Evolutivo: población de rutas, selección por torneo, cruce de orden
    (OX), mutación por intercambio y elitismo."""
    rnd = random.Random(semilla)
    poblacion = [rnd.sample(range(N), N) for _ in range(pob)]
    historial, evaluadas = [], 0

    def torneo():
        return min(rnd.sample(poblacion, k_torneo), key=costo)

    def cruce_ox(p1, p2):
        a, b = sorted(rnd.sample(range(N), 2))
        hijo = [None] * N
        hijo[a:b + 1] = p1[a:b + 1]
        resto = [g for g in p2 if g not in hijo]
        k = 0
        for idx in range(N):
            if hijo[idx] is None:
                hijo[idx] = resto[k]
                k += 1
        return hijo

    def mutar(r):
        if rnd.random() < p_mut:
            i, j = rnd.sample(range(N), 2)
            r[i], r[j] = r[j], r[i]
        return r

    for _ in range(generaciones):
        poblacion.sort(key=costo)
        historial.append(costo(poblacion[0]))
        nueva = [p[:] for p in poblacion[:elite]]
        while len(nueva) < pob:
            nueva.append(mutar(cruce_ox(torneo(), torneo())))
        evaluadas += pob
        poblacion = nueva
    poblacion.sort(key=costo)
    mejor = poblacion[0]
    # Normalizar para que la ruta empiece en la ciudad 0
    k = mejor.index(0)
    mejor = mejor[k:] + mejor[:k]
    return mejor, costo(mejor), evaluadas, historial


# ---------------------------------------------------------------
# 3. EJECUCIÓN Y COMPARACIÓN
# ---------------------------------------------------------------
def normalizar(ruta):
    k = ruta.index(0)
    return ruta[k:] + ruta[:k]


def medir(nombre, funcion, *args, **kw):
    t = time.perf_counter()
    res = funcion(*args, **kw)
    seg = time.perf_counter() - t
    ruta, c, evaluadas = normalizar(res[0]), res[1], res[2]
    hist = res[3] if len(res) > 3 else None
    return {"nombre": nombre, "ruta": ruta, "costo": c,
            "evaluadas": evaluadas, "tiempo": seg, "hist": hist}


if __name__ == "__main__":
    SEMILLA = 42
    print(f"TSP con {N} ciudades. Salida y regreso: {NOMBRES[0]}\n")

    resultados = [
        medir("Fuerza bruta (ciega)", fuerza_bruta),
        medir("Vecino mas cercano (heuristica)", vecino_mas_cercano),
        medir("Hill climbing 2-opt (local)", hill_climbing, semilla=SEMILLA),
        medir("Recocido simulado (local)", recocido_simulado, semilla=SEMILLA),
        medir("Algoritmo genetico (evolutivo)", algoritmo_genetico, semilla=SEMILLA),
    ]
    optimo = resultados[0]["costo"]

    print(f"{'Algoritmo':36}{'Distancia km':>14}{'Vs optimo':>11}"
          f"{'Evaluaciones':>14}{'Tiempo s':>10}")
    print("-" * 85)
    for r in resultados:
        extra = (r["costo"] / optimo - 1) * 100
        print(f"{r['nombre']:36}{r['costo']:14.1f}{extra:10.1f}%"
              f"{r['evaluadas']:14d}{r['tiempo']:10.3f}")

    print("\nRutas encontradas:")
    for r in resultados:
        print(f"- {r['nombre']}: {mostrar(r['ruta'])}")

    # Gráficas opcionales
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ejes = plt.subplots(1, len(resultados), figsize=(4 * len(resultados), 4))
        for ax, r in zip(ejes, resultados):
            ruta = r["ruta"] + [r["ruta"][0]]
            xs = [CIUDADES[NOMBRES[i]][1] for i in ruta]
            ys = [CIUDADES[NOMBRES[i]][0] for i in ruta]
            ax.plot(xs, ys, "-o")
            for i in r["ruta"]:
                ax.annotate(NOMBRES[i], (CIUDADES[NOMBRES[i]][1], CIUDADES[NOMBRES[i]][0]),
                            fontsize=6)
            ax.set_title(f"{r['nombre'].split(' (')[0]}\n{r['costo']:.0f} km", fontsize=8)
        plt.tight_layout()
        plt.savefig("rutas_tsp.png", dpi=150)

        plt.figure(figsize=(6, 4))
        plt.plot(resultados[3]["hist"], label="Recocido simulado")
        plt.plot(resultados[4]["hist"], label="Algoritmo genetico")
        plt.axhline(optimo, color="g", ls="--", label="Optimo (fuerza bruta)")
        plt.xlabel("Iteracion / generacion")
        plt.ylabel("Mejor distancia (km)")
        plt.legend()
        plt.tight_layout()
        plt.savefig("convergencia_tsp.png", dpi=150)
        print("\nGraficas guardadas: rutas_tsp.png y convergencia_tsp.png")
    except ImportError:
        print("\n(matplotlib no esta instalado: se omiten las graficas)")
