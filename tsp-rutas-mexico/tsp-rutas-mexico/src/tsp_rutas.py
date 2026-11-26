"""
Problema del viajante (TSP): un vendedor sale de Puebla, visita 9 ciudades
de México (una sola vez cada una) y regresa a Puebla.

El programa revisa varias rutas y dice cuál es la más corta, cuáles
conviene tomar y cuáles no. También verifica la ruta que armes tú.

Solo usa la biblioteca estándar. Si tienes matplotlib
(pip install matplotlib) también puede guardar un mapa de la ruta.
"""
import math
import random

# ---------------------------------------------------------------
# DATOS: ciudad -> (latitud, longitud). La ciudad 0 es el origen.
# ---------------------------------------------------------------
CIUDADES = [
    ("Puebla", 19.0414, -98.2063),
    ("CDMX", 19.4326, -99.1332),
    ("Cuernavaca", 18.9186, -99.2342),
    ("Toluca", 19.2826, -99.6557),
    ("Queretaro", 20.5888, -100.3899),
    ("Pachuca", 20.1011, -98.7591),
    ("Tlaxcala", 19.3139, -98.2404),
    ("Veracruz", 19.1738, -96.1342),
    ("Oaxaca", 17.0732, -96.7266),
    ("Acapulco", 16.8531, -99.8237),
]
N = len(CIUDADES)
LIMITE_CONVIENE = 5.0  # % maximo mas larga que la mejor para que "conviene"


def haversine(a, b):
    """Distancia en km entre dos ciudades."""
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[2], b[1], b[2]))
    d = math.sin((la2 - la1) / 2) ** 2 + \
        math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(d))


DIST = [[haversine(a, b) for b in CIUDADES] for a in CIUDADES]


def costo(ruta):
    """Km totales del recorrido, regresando a la ciudad de inicio."""
    return sum(DIST[ruta[i]][ruta[(i + 1) % len(ruta)]] for i in range(len(ruta)))


def normalizar(ruta):
    """Empieza en Puebla y elige un sentido fijo para no repetir rutas
    que son la misma recorrida al reves."""
    k = ruta.index(0)
    ruta = ruta[k:] + ruta[:k]
    if ruta[1] > ruta[-1]:
        ruta = [0] + ruta[1:][::-1]
    return ruta


def texto(ruta):
    return " -> ".join(CIUDADES[i][0] for i in ruta + [ruta[0]])


# ---------------------------------------------------------------
# BUSCADORES DE RUTAS (por dentro usan distintos metodos de busqueda,
# pero al usuario solo se le muestran las rutas encontradas)
# ---------------------------------------------------------------
def buscar_la_mas_corta():
    """Revisa todas las rutas posibles (9! = 362,880) y devuelve la mejor."""
    mejor, mejor_c = None, float("inf")
    camino, usada = [0], [False] * N
    usada[0] = True

    def dfs(c):
        nonlocal mejor, mejor_c
        if len(camino) == N:
            total = c + DIST[camino[-1]][0]
            if total < mejor_c:
                mejor_c, mejor = total, camino[:]
            return
        for j in range(1, N):
            if not usada[j]:
                usada[j] = True
                camino.append(j)
                dfs(c + DIST[camino[-2]][j])
                camino.pop()
                usada[j] = False

    dfs(0)
    return mejor


def ruta_vecino_cercano():
    ruta, pend = [0], set(range(1, N))
    while pend:
        sig = min(pend, key=lambda j: DIST[ruta[-1]][j])
        ruta.append(sig)
        pend.remove(sig)
    return ruta


def dos_opt(r, i, j):
    return r[:i] + r[i:j + 1][::-1] + r[j + 1:]


def ruta_mejorando_local(rnd):
    r = rnd.sample(range(N), N)
    c, mejora = costo(r), True
    while mejora:
        mejora = False
        for i in range(1, N - 1):
            for j in range(i + 1, N):
                q = dos_opt(r, i, j)
                qc = costo(q)
                if qc < c - 1e-9:
                    r, c, mejora = q, qc, True
    return r


def ruta_enfriando(rnd):
    r = rnd.sample(range(N), N)
    c = costo(r)
    mejor, mejor_c, t = r[:], c, 500.0
    while t > 0.01:
        i, j = sorted(rnd.sample(range(1, N), 2))
        q = dos_opt(r, i, j)
        qc = costo(q)
        d = qc - c
        if d < 0 or rnd.random() < math.exp(-d / t):
            r, c = q, qc
            if c < mejor_c:
                mejor, mejor_c = r[:], c
        t *= 0.995
    return mejor


def ruta_evolucionando(rnd, pob=100, gens=300):
    poblacion = [rnd.sample(range(N), N) for _ in range(pob)]

    def torneo():
        return min(rnd.sample(poblacion, 5), key=costo)

    def cruce(p1, p2):
        a, b = sorted(rnd.sample(range(N), 2))
        hijo = [None] * N
        hijo[a:b + 1] = p1[a:b + 1]
        resto = [g for g in p2 if g not in hijo]
        k = 0
        for i in range(N):
            if hijo[i] is None:
                hijo[i] = resto[k]
                k += 1
        return hijo

    for _ in range(gens):
        poblacion.sort(key=costo)
        nueva = [p[:] for p in poblacion[:2]]
        while len(nueva) < pob:
            h = cruce(torneo(), torneo())
            if rnd.random() < 0.2:
                i, j = rnd.sample(range(N), 2)
                h[i], h[j] = h[j], h[i]
            nueva.append(h)
        poblacion = nueva
    return min(poblacion, key=costo)


# ---------------------------------------------------------------
# REVISION DE RUTAS
# ---------------------------------------------------------------
OPTIMA = normalizar(buscar_la_mas_corta())
KM_OPTIMA = costo(OPTIMA)


def veredicto(km):
    extra = km - KM_OPTIMA
    pct = extra / KM_OPTIMA * 100
    if extra < 0.01:
        return "LA MAS CORTA", extra, pct
    if pct <= LIMITE_CONVIENE:
        return "CONVIENE", extra, pct
    return "NO CONVIENE", extra, pct


def generar_rutas(semilla):
    rnd = random.Random(semilla)
    candidatas = [
        OPTIMA,
        ruta_vecino_cercano(),
        ruta_mejorando_local(rnd),
        ruta_enfriando(rnd),
        ruta_evolucionando(rnd),
        rnd.sample(range(N), N),
        rnd.sample(range(N), N),
        rnd.sample(range(N), N),
    ]
    vistas, rutas = set(), []
    for r in candidatas:
        n = normalizar(list(r))
        if tuple(n) not in vistas:
            vistas.add(tuple(n))
            rutas.append(n)
    rutas.sort(key=costo)
    return rutas


def mostrar_rutas(rutas):
    print("\nRUTAS REVISADAS (de la mas corta a la mas larga)")
    print("=" * 74)
    for i, r in enumerate(rutas, 1):
        km = costo(r)
        v, extra, pct = veredicto(km)
        mas = "mejor opcion" if extra < 0.01 else f"+{extra:.0f} km ({pct:.1f}%)"
        print(f"Ruta {i}: {km:7.1f} km | {v:<13} | {mas}")
        print(f"        {texto(r)}")
    print("=" * 74)
    print(f"Conviene si es hasta {LIMITE_CONVIENE:.0f}% mas larga que la mejor "
          f"({KM_OPTIMA:.1f} km).")


def verificar_mi_ruta():
    print("\nCiudades disponibles (sales de Puebla y regresas al final):")
    for i in range(1, N):
        print(f"  {i}. {CIUDADES[i][0]}")
    print("Escribe los 9 numeros en el orden en que visitarias las ciudades,")
    print("separados por espacios. Ejemplo: 6 1 5 4 3 2 9 8 7")
    try:
        entrada = input("Tu ruta: ").split()
        orden = [int(x) for x in entrada]
    except ValueError:
        print("Solo se permiten numeros. Intenta de nuevo.")
        return None
    if sorted(orden) != list(range(1, N)):
        print(f"Debes usar cada numero del 1 al {N - 1} una sola vez.")
        return None
    ruta = [0] + orden
    km = costo(ruta)
    v, extra, pct = veredicto(km)
    print(f"\nTu ruta: {texto(ruta)}")
    print(f"Mide {km:.1f} km -> {v}.")
    if extra < 0.01:
        print("Encontraste la ruta mas corta.")
    else:
        print(f"Es {extra:.0f} km ({pct:.1f}%) mas larga que la mejor "
              f"({KM_OPTIMA:.1f} km).")
        print("La mejor es: " + texto(OPTIMA))
    return ruta


def guardar_mapa(ruta, archivo="mapa_ruta.png"):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Para guardar el mapa instala matplotlib: pip install matplotlib")
        return
    v, _, _ = veredicto(costo(ruta))
    color = {"LA MAS CORTA": "tab:green", "CONVIENE": "tab:orange"}.get(v, "tab:red")
    orden = ruta + [ruta[0]]
    xs = [CIUDADES[i][2] for i in orden]
    ys = [CIUDADES[i][1] for i in orden]
    plt.figure(figsize=(7, 6))
    plt.plot(xs, ys, "-o", color=color)
    for pos, i in enumerate(ruta):
        etiqueta = CIUDADES[i][0] if pos == 0 else f"{pos}. {CIUDADES[i][0]}"
        plt.annotate(etiqueta, (CIUDADES[i][2], CIUDADES[i][1]), fontsize=8,
                     xytext=(4, 4), textcoords="offset points")
    plt.title(f"{costo(ruta):.0f} km - {v}")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.tight_layout()
    plt.savefig(archivo, dpi=150)
    print(f"Mapa guardado en {archivo}")


def menu():
    semilla = 42
    rutas = generar_rutas(semilla)
    ultima = OPTIMA
    mostrar_rutas(rutas)
    while True:
        print("\n1) Ver rutas revisadas   2) Verificar mi ruta")
        print("3) Revisar otras rutas   4) Guardar mapa de la ultima ruta   0) Salir")
        try:
            op = input("Elige una opcion: ").strip()
        except EOFError:
            break
        if op == "1":
            mostrar_rutas(rutas)
        elif op == "2":
            r = verificar_mi_ruta()
            ultima = r if r else ultima
        elif op == "3":
            semilla += 1
            rutas = generar_rutas(semilla)
            mostrar_rutas(rutas)
        elif op == "4":
            guardar_mapa(ultima)
        elif op == "0":
            break
        else:
            print("Opcion no valida.")
    print("Fin del programa.")


if __name__ == "__main__":
    print("Un vendedor sale de Puebla, visita 9 ciudades y regresa a Puebla.")
    print("Hay 362,880 ordenes posibles. Calculando...")
    menu()
