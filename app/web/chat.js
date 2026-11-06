// Chat web del coach: habla con la misma API (POST /usuarios, POST /chat y
// GET /usuarios/{id}/rutinas/actual). Sin dependencias ni paso de compilacion.
"use strict";

const CLAVE_USUARIO = "coach.usuario_id";
const CLAVE_HISTORIAL = "coach.historial";
// Encabezado fijo con el que el coach lista la rutina (app/agentes/nodos.py, _formatear_rutina)
const ENCABEZADO_RUTINA = /^Tu rutina \(versión (\d+)\):$/;

const $ = (id) => document.getElementById(id);
const lista = $("mensajes");
const bienvenida = $("bienvenida");
const entrada = $("entrada");
const enviar = $("enviar");

let usuarioId = leer(CLAVE_USUARIO);
let historial = JSON.parse(leer(CLAVE_HISTORIAL) || "[]");
let ocupado = false;

// --- almacenamiento local (puede no estar disponible: modo privado, etc.) ---
function leer(clave) {
  try { return localStorage.getItem(clave); } catch { return null; }
}
function guardar(clave, valor) {
  try { localStorage.setItem(clave, valor); } catch { /* sin persistencia local */ }
}
function borrar(clave) {
  try { localStorage.removeItem(clave); } catch { /* sin persistencia local */ }
}

// --- API ---
class ErrorApi extends Error {
  constructor(estado, detalle) { super(detalle); this.estado = estado; }
}

async function api(metodo, ruta, cuerpo) {
  let resp;
  try {
    resp = await fetch(ruta, {
      method: metodo,
      headers: cuerpo ? { "Content-Type": "application/json" } : {},
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    throw new ErrorApi(0, "No pude conectar con la API. Revisá que el sistema esté levantado (docker compose up -d).");
  }
  const datos = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detalle = typeof datos.detail === "string" ? datos.detail : `La API respondió ${resp.status}.`;
    throw new ErrorApi(resp.status, detalle);
  }
  return datos;
}

async function asegurarUsuario() {
  if (usuarioId) return usuarioId;
  const { id } = await api("POST", "/usuarios", {});
  usuarioId = id;
  guardar(CLAVE_USUARIO, id);
  return id;
}

// --- render ---
function el(etiqueta, clase, texto) {
  const nodo = document.createElement(etiqueta);
  if (clase) nodo.className = clase;
  if (texto !== undefined) nodo.textContent = texto;
  return nodo;
}

// Convierte texto plano en parrafos y listas ("- item"), sin interpretar HTML.
function bloquesDeTexto(lineas, destino) {
  let ul = null;
  let parrafo = [];
  const cerrarParrafo = () => {
    if (parrafo.length) destino.append(el("p", null, parrafo.join("\n")));
    parrafo = [];
  };
  for (const linea of lineas) {
    if (linea.startsWith("- ")) {
      cerrarParrafo();
      if (!ul) { ul = el("ul"); destino.append(ul); }
      ul.append(el("li", null, linea.slice(2)));
    } else if (!linea.trim()) {
      cerrarParrafo();
      ul = null;
    } else {
      ul = null;
      parrafo.push(linea);
    }
  }
  cerrarParrafo();
}

// Separa la lista de la rutina (encabezado, dias y "- ejercicio") del resto del texto.
function partirRutina(texto) {
  const lineas = texto.split("\n");
  const inicio = lineas.findIndex((l) => ENCABEZADO_RUTINA.test(l.trim()));
  if (inicio < 0) return null;
  let fin = inicio + 1;
  while (fin < lineas.length) {
    const l = lineas[fin];
    const siguiente = lineas.slice(fin + 1).find((x) => x.trim());
    const esDia = l.trim() && !l.startsWith("- ") && siguiente !== undefined && siguiente.startsWith("- ");
    if (!l.trim() || l.startsWith("- ") || esDia) fin++;
    else break;
  }
  return {
    version: Number(lineas[inicio].trim().match(ENCABEZADO_RUTINA)[1]),
    antes: lineas.slice(0, inicio),
    despues: lineas.slice(fin),
  };
}

function tablaRutina(rutina) {
  const caja = el("div", "rutina");
  const titulo = el("h3", "rutina__titulo", "Tu rutina ");
  titulo.append(el("span", null, `versión ${rutina.version}`));
  caja.append(titulo);
  const nombres = rutina.nombres || {};
  rutina.dias.forEach((dia, i) => {
    const bloque = el("section", "dia");
    bloque.append(el("h4", null, dia.nombre || `Día ${i + 1}`));
    const envoltorio = el("div", "tabla-envoltorio");
    const tabla = el("table");
    const cabeza = el("tr");
    [["Ejercicio", ""], ["Series", "num"], ["Reps", "num"], ["Descanso", "num"]]
      .forEach(([t, c]) => { const th = el("th", c, t); th.scope = "col"; cabeza.append(th); });
    const thead = el("thead");
    thead.append(cabeza);
    tabla.append(thead);
    const cuerpo = el("tbody");
    for (const ej of dia.ejercicios) {
      const fila = el("tr");
      fila.append(
        el("td", null, nombres[ej.ejercicio_id] || ej.ejercicio_id),
        el("td", "num", String(ej.series)),
        el("td", "num", ej.repeticiones),
        el("td", "num", `${ej.descanso_seg} s`),
      );
      cuerpo.append(fila);
    }
    tabla.append(cuerpo);
    envoltorio.append(tabla);
    bloque.append(envoltorio);
    caja.append(bloque);
  });
  return caja;
}

function pintar(item) {
  bienvenida.hidden = true;
  const li = el("li", `mensaje mensaje--${item.tipo}`);
  if (item.tipo === "usuario") {
    li.textContent = item.texto;
  } else if (item.tipo === "pausa" || item.tipo === "error") {
    li.setAttribute("role", item.tipo === "error" ? "alert" : "status");
    li.append(el("strong", null, item.titulo));
    bloquesDeTexto(item.texto.split("\n"), li);
  } else {
    const partes = item.rutina ? partirRutina(item.texto) : null;
    if (partes && partes.version === item.rutina.version) {
      bloquesDeTexto(partes.antes, li);
      li.append(tablaRutina(item.rutina));
      bloquesDeTexto(partes.despues, li);
    } else {
      bloquesDeTexto(item.texto.split("\n"), li);
    }
  }
  lista.append(li);
  li.scrollIntoView({ block: "end" });
  return li;
}

function agregar(item) {
  historial.push(item);
  guardar(CLAVE_HISTORIAL, JSON.stringify(historial));
  pintar(item);
}

function indicadorEspera() {
  const li = el("li", "mensaje mensaje--coach");
  li.setAttribute("aria-label", "El coach está escribiendo");
  const puntos = el("span", "escribiendo");
  puntos.append(el("span"), el("span"), el("span"));
  li.append(puntos);
  lista.append(li);
  li.scrollIntoView({ block: "end" });
  return li;
}

// --- flujo ---
async function rutinaSiCorresponde(texto) {
  const partes = partirRutina(texto);
  if (!partes) return null;
  try {
    const rutina = await api("GET", `/usuarios/${usuarioId}/rutinas/actual`);
    return rutina.version === partes.version ? rutina : null;
  } catch {
    return null; // sin tabla: se muestra el texto tal cual
  }
}

async function mandar(texto) {
  if (ocupado || !texto.trim()) return;
  ocupado = true;
  enviar.disabled = true;
  agregar({ tipo: "usuario", texto });
  const espera = indicadorEspera();
  try {
    await asegurarUsuario();
    const r = await api("POST", "/chat", { usuario_id: usuarioId, mensaje: texto });
    espera.remove();
    if (r.requiere_humano) {
      agregar({ tipo: "pausa", titulo: "Conversación en pausa", texto: r.respuesta });
    } else {
      agregar({ tipo: "coach", texto: r.respuesta, rutina: await rutinaSiCorresponde(r.respuesta) });
    }
  } catch (e) {
    espera.remove();
    const pausa = e.estado === 409;
    agregar({
      tipo: pausa ? "pausa" : "error",
      titulo: pausa ? "Conversación en pausa" : "No se pudo enviar el mensaje",
      texto: e.message,
    });
  } finally {
    ocupado = false;
    enviar.disabled = false;
    entrada.focus();
  }
}

function ajustarAltura() {
  entrada.style.height = "auto";
  const borde = entrada.offsetHeight - entrada.clientHeight;
  entrada.style.height = `${entrada.scrollHeight + borde}px`;
  // con scroll solo cuando el texto supera la altura maxima (10rem)
  entrada.style.overflowY = entrada.scrollHeight + borde > entrada.offsetHeight ? "auto" : "hidden";
}

$("formulario").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const texto = entrada.value;
  entrada.value = "";
  ajustarAltura();
  mandar(texto);
});

entrada.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey && !ev.isComposing) {
    ev.preventDefault();
    $("formulario").requestSubmit();
  }
});
entrada.addEventListener("input", ajustarAltura);

document.querySelectorAll(".sugerencia").forEach((b) =>
  b.addEventListener("click", () => mandar(b.textContent)));

$("nueva").addEventListener("click", () => {
  if (ocupado) return;
  usuarioId = null;
  historial = [];
  borrar(CLAVE_USUARIO);
  borrar(CLAVE_HISTORIAL);
  lista.replaceChildren();
  bienvenida.hidden = false;
  entrada.focus();
});

historial.forEach(pintar);
entrada.focus();
