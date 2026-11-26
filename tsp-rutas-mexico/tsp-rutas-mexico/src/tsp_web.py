"""
Version web del TSP hecha 100% en Python (solo biblioteca estandar).

Uso (con tsp_rutas.py en la misma carpeta):
    python tsp_web.py
Se abre solo el navegador en http://localhost:8000
Para cerrar el programa presiona Ctrl+C en la ventana de CMD.
"""
import html
import json
import math
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from tsp_rutas import (CIUDADES, DIST, KM_OPTIMA, LIMITE_CONVIENE, N, OPTIMA, costo,
                       generar_rutas, texto, veredicto)

PUERTO = 8000
COLORES = {"LA MAS CORTA": "#0b6e69", "CONVIENE": "#a16207", "NO CONVIENE": "#b91c1c"}
CACHE = {}


def rutas_de(semilla):
    if semilla not in CACHE:
        CACHE[semilla] = generar_rutas(semilla)
    return CACHE[semilla]


def svg_mapa(ruta, color):
    """Dibuja las ciudades y la ruta como SVG (generado en Python)."""
    W, H, pad = 560, 440, 50
    k = math.cos(math.radians(19))
    lat = [c[1] for c in CIUDADES]
    lon = [c[2] for c in CIUDADES]
    esc = min((W - 2 * pad) / ((max(lon) - min(lon)) * k),
              (H - 2 * pad) / (max(lat) - min(lat)))
    ox = (W - (max(lon) - min(lon)) * k * esc) / 2
    oy = (H - (max(lat) - min(lat)) * esc) / 2
    pts = [(ox + (c[2] - min(lon)) * k * esc, oy + (max(lat) - c[1]) * esc)
           for c in CIUDADES]
    orden = ruta + [ruta[0]]
    linea = " ".join(f"{pts[i][0]:.1f},{pts[i][1]:.1f}" for i in orden)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
         f'aria-label="Mapa de la ruta" style="background:#e6ece8;border-radius:8px">',
         f'<polyline points="{linea}" fill="none" stroke="{color}" '
         f'stroke-width="3" stroke-opacity=".3" stroke-linejoin="round"/>',
         f'<polyline id="rastro" points="" fill="none" stroke="{color}" '
         f'stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>']
    for pos, i in enumerate(ruta):
        x, y = pts[i]
        r = 7 if i == 0 else 5
        fill = "#c2410c" if i == 0 else "#1d2a2f"
        nombre = CIUDADES[i][0] if pos == 0 else f"{pos}. {CIUDADES[i][0]}"
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')
        s.append(f'<text x="{x + 9:.1f}" y="{y - 7:.1f}" font-size="13" '
                 f'font-family="sans-serif" fill="#1d2a2f">{html.escape(nombre)}</text>')
    s.append('<text id="coche" x="0" y="0" font-size="26" text-anchor="middle" '
             'dominant-baseline="central">🚗</text>')
    s.append("</svg>")
    return "".join(s), pts


SCRIPT_COCHE = """
<script>
(function(){
var D=__DATOS__,P=D.p,NM=D.n,KM=D.km,TOT=D.tot;
var car=document.getElementById('coche'),tr=document.getElementById('rastro');
var btn=document.getElementById('simBtn'),rst=document.getElementById('simRst'),sp=document.getElementById('simVel');
var odo=document.getElementById('simKm'),est=document.getElementById('simEst');
var L=[],i;
for(i=0;i<P.length-1;i++)L.push(Math.hypot(P[i+1][0]-P[i][0],P[i+1][1]-P[i][1]));
var leg=0,f=0,kmDone=0,play=false,last=0,pausa=0,fin=false;
function draw(){
  var a=P[leg],b=P[leg+1],x=a[0]+(b[0]-a[0])*f,y=a[1]+(b[1]-a[1])*f;
  car.setAttribute('transform','translate('+x+','+y+') scale('+(b[0]>a[0]?-1:1)+',1)');
  var pts=P.slice(0,leg+1).map(function(p){return p.join(',')});pts.push(x+','+y);
  tr.setAttribute('points',pts.join(' '));
  odo.textContent=(kmDone+KM[leg]*f).toFixed(0)+' km de '+TOT.toFixed(0)+' km';
}
function reset(){leg=0;f=0;kmDone=0;pausa=0;fin=false;play=false;
  btn.textContent='\u25B6 Simular recorrido';est.textContent='Listo para salir de '+NM[0];draw();}
function step(t){
  if(!play)return;
  var dt=Math.min(50,t-last);last=t;
  if(pausa>0){pausa-=dt;}
  else{
    f+=0.1*parseFloat(sp.value)*dt/L[leg];
    if(f>=1){
      if(leg===L.length-1){f=1;fin=true;play=false;draw();
        est.textContent='\u00A1Lleg\u00F3 a '+NM[0]+'! Recorri\u00F3 '+TOT.toFixed(0)+' km';
        btn.textContent='\u21BB Repetir';return;}
      kmDone+=KM[leg];leg++;f=0;pausa=500;
      est.textContent='En '+NM[leg]+'. Sigue rumbo a '+NM[leg+1];
    }
    draw();
  }
  requestAnimationFrame(step);
}
btn.addEventListener('click',function(){
  if(fin)reset();
  if(play){play=false;btn.textContent='\u25B6 Continuar';return;}
  play=true;last=performance.now();btn.textContent='\u23F8 Pausar';
  if(est.textContent.indexOf('Listo')===0)est.textContent='Sale de '+NM[0]+' rumbo a '+NM[1];
  requestAnimationFrame(step);
});
rst.addEventListener('click',reset);
reset();
})();
</script>
"""


def simulador(ruta, pts):
    """Controles y animacion del coche recorriendo la ruta."""
    orden = ruta + [ruta[0]]
    datos = {"p": [[round(pts[i][0], 1), round(pts[i][1], 1)] for i in orden],
             "n": [CIUDADES[i][0] for i in orden],
             "km": [round(DIST[orden[k]][orden[k + 1]], 2) for k in range(len(ruta))],
             "tot": round(costo(ruta), 2)}
    return ('<div class="sim"><button id="simBtn" type="button">▶ Simular recorrido</button>'
            '<button id="simRst" type="button" class="alt">Reiniciar</button>'
            '<label>Velocidad <select id="simVel"><option value="1">Normal</option>'
            '<option value="2">Rápida</option><option value="4">Muy rápida</option></select></label>'
            '<span id="simKm" class="km">0 km</span></div>'
            '<p id="simEst" class="h" role="status"></p>'
            + SCRIPT_COCHE.replace("__DATOS__", json.dumps(datos)))


def insignia(km):
    v, extra, pct = veredicto(km)
    return (f'<b style="color:{COLORES[v]}">{v}</b>', v, extra, pct)


def pagina(q):
    try:
        semilla = int(q.get("seed", ["42"])[0])
    except ValueError:
        semilla = 42
    rutas = rutas_de(semilla)
    try:
        elegida = min(max(int(q.get("ruta", ["1"])[0]), 1), len(rutas))
    except ValueError:
        elegida = 1

    # Ruta propia (c1..c9)
    mia, mensaje = None, ""
    previas = [q.get(f"c{i}", [""])[0] for i in range(1, N)]
    if any(previas):
        try:
            orden = [int(x) for x in previas]
            if sorted(orden) == list(range(1, N)):
                mia = [0] + orden
            else:
                mensaje = "Usa cada ciudad una sola vez."
        except ValueError:
            mensaje = "Elige una ciudad en cada lugar de la lista."

    if mia:
        ruta_mapa, km_mapa = mia, costo(mia)
        titulo_mapa = "Tu ruta"
    else:
        ruta_mapa = rutas[elegida - 1]
        km_mapa = costo(ruta_mapa)
        titulo_mapa = f"Ruta {elegida}"
    tag, v, extra, pct = insignia(km_mapa)
    mapa, pts = svg_mapa(ruta_mapa, COLORES[v])
    sim = simulador(ruta_mapa, pts)

    filas = []
    for i, r in enumerate(rutas, 1):
        km = costo(r)
        t, v2, e2, p2 = insignia(km)
        mas = "mejor opción" if e2 < 0.01 else f"+{e2:.0f} km ({p2:.1f}%)"
        marca = " sel" if (not mia and i == elegida) else ""
        filas.append(
            f'<a class="it{marca}" href="/?seed={semilla}&ruta={i}">'
            f'<span><b>Ruta {i}</b> {t}</span><span>{km:.0f} km · {mas}</span></a>')

    opciones = "".join(f'<option value="{i}">{html.escape(CIUDADES[i][0])}</option>'
                       for i in range(1, N))
    selects = []
    for i in range(1, N):
        o = opciones.replace(f'value="{previas[i-1]}"',
                             f'value="{previas[i-1]}" selected') if previas[i-1] else opciones
        selects.append(f'<label>{i}.<select name="c{i}" required>'
                       f'<option value="">—</option>{o}</select></label>')

    if mia:
        if extra < 0.01:
            res = "¡Encontraste la ruta más corta!"
        else:
            res = (f"Es {extra:.0f} km ({pct:.1f}%) más larga que la mejor "
                   f"({KM_OPTIMA:.0f} km). La mejor es: {html.escape(texto(OPTIMA))}")
        bloque_mia = f'<p>Tu ruta mide <b>{km_mapa:.0f} km</b>: {tag}. {res}</p>'
    else:
        bloque_mia = f'<p class="err">{mensaje}</p>' if mensaje else ""

    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>¿Qué ruta conviene?</title>
<style>
body{{font:16px/1.5 Georgia,serif;background:#f3f1ea;color:#1d2a2f;margin:0}}
main{{max-width:980px;margin:auto;padding:20px 16px 40px}}
h1{{font-size:1.6rem;line-height:1.2;margin:0 0 6px}} h2{{font-size:1.05rem;margin:0 0 8px}}
.grid{{display:grid;grid-template-columns:1.1fr 1fr;gap:16px}}
@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}
.box{{background:#fff;border:1px solid #d6d2c4;border-radius:10px;padding:12px;margin-bottom:16px;font-family:system-ui,sans-serif}}
.it{{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:10px;border:1px solid #d6d2c4;border-radius:8px;margin-bottom:8px;color:inherit;text-decoration:none;font-size:.9rem}}
.it.sel{{border-color:#0b6e69;box-shadow:0 0 0 2px #0b6e69 inset}}
.btn,button{{display:inline-block;font:600 .9rem system-ui;background:#0b6e69;color:#fff;border:0;border-radius:8px;padding:9px 14px;cursor:pointer;text-decoration:none}}
select{{padding:6px;margin:0 8px 8px 4px;border:1px solid #d6d2c4;border-radius:6px}}
.err{{color:#b91c1c}} .h{{color:#5d6b70;font-size:.85rem;margin:0 0 8px}}
.sim{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}}
.sim button.alt{{background:transparent;color:#1d2a2f;border:1px solid #d6d2c4}}
.sim select{{margin:0 0 0 4px}} .sim .km{{margin-left:auto;font:700 .95rem system-ui}}
</style></head><body><main>
<h1>Un vendedor sale de Puebla y debe visitar 9 ciudades</h1>
<p class="h" style="font-size:1rem">Pasa por cada ciudad una sola vez y regresa a Puebla. Hay 362,880 órdenes posibles.
El programa revisa varias rutas y dice cuál es la más corta y cuáles conviene o no conviene tomar.</p>
<div class="grid"><div>
<div class="box"><h2>{titulo_mapa}: {km_mapa:.0f} km · {tag}</h2>
{mapa}{sim}
<p class="h">{html.escape(texto(ruta_mapa))}</p></div>
<div class="box"><h2>Arma tu propia ruta</h2>
<p class="h">Elige las ciudades en el orden en que las visitarías (sales de Puebla y regresas al final).</p>
<form method="get"><input type="hidden" name="seed" value="{semilla}">
{"".join(selects)}<br><button type="submit">Verificar mi ruta</button></form>
{bloque_mia}</div></div>
<div class="box"><h2>Rutas revisadas, de la más corta a la más larga</h2>
<p class="h">Conviene si es hasta {LIMITE_CONVIENE:.0f}% más larga que la mejor.</p>
{"".join(filas)}
<a class="btn" href="/?seed={semilla + 1}">Revisar otras rutas</a></div>
</div></main></body></html>"""


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/":
            self.send_error(404)
            return
        cuerpo = pagina(parse_qs(url.query)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass  # sin mensajes en la consola


if __name__ == "__main__":
    servidor = HTTPServer(("127.0.0.1", PUERTO), Manejador)
    url = f"http://localhost:{PUERTO}"
    print(f"Programa listo en {url}  (Ctrl+C para cerrar)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nPrograma cerrado.")
