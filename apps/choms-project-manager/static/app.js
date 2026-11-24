"use strict";

const view = document.querySelector("#view");
const notice = document.querySelector("#notice");
const editor = document.querySelector("#editor");
const today = new Intl.DateTimeFormat("sv-SE", {timeZone: "Europe/Madrid"}).format(new Date());
const formatDate = new Intl.DateTimeFormat("es-ES", {dateStyle: "medium", timeZone: "UTC"});
const formatLongDate = new Intl.DateTimeFormat("es-ES", {dateStyle: "full", timeZone: "UTC"});
const money = new Intl.NumberFormat("es-ES", {style: "currency", currency: "EUR"});
let statusLabels = {};
let priorities = {};
let taskKinds = {};
let activityKinds = {};
let activityConfig = {};
let transportOptions = {};
const projectSelect = document.querySelector("#project-select");
const exportLink = document.querySelector("#project-export");
const calendarModes = {day: "Día", week: "Semana", month: "Mes"};
const modeNav = {dashboard: "Resumen", calendar: "Calendario", tasks: "Tareas", kanban: "Kanban", gantt: "Gantt", logs: "Registros", reports: "Informes", projects: "Proyectos", settings: "Configuración"};
const state = {date: today, mode: "day", transport: "", taskKind: "", activityKind: ""};

let project;
let projects = [];
let templates = [];
let globalSummary = {};
let tasks = [];
let activities = [];
let events = [];
let currentRender = 0;
let currentReload = 0;

function html(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[character]));
}
function fromDate(value) {
  return new Date(value + "T00:00:00Z");
}
function offset(value, days) {
  const next = fromDate(value);
  next.setUTCDate(next.getUTCDate() + days);
  return next.toISOString().slice(0, 10);
}
function displayDate(value) {
  return value ? formatDate.format(fromDate(value)) : "Sin fecha";
}
function monday(value) {
  return offset(value, -((fromDate(value).getUTCDay() + 6) % 7));
}
function minutes(value) {
  return value ? `${Math.floor(value / 60)} h ${value % 60} min` : "0 h";
}
function euros(value) {
  return money.format((value ?? 0) / 100);
}
function route() {
  const page = location.hash.slice(1);
  return Object.hasOwn(modeNav, page) ? page : "projects";
}
function scoped(path) {
  return projectPath(project.id, path);
}
function projectPath(id, path) {
  return "/api/projects/" + encodeURIComponent(id) + path;
}
async function request(path, method = "GET", body) {
  const options = {method};
  if (body !== undefined) {
    options.body = JSON.stringify(body);
    options.headers = {"Content-Type": "application/json"};
  }
  const response = await fetch(path, options);
  if (response.redirected) throw new Error("La sesión ha caducado. Recarga para volver a iniciar sesión.");
  if (response.status === 401 || response.status === 403) throw new Error("Tu sesión carece de acceso. Recarga para autenticarte.");
  if (!response.headers.get("Content-Type")?.includes("application/json")) throw new Error("No se pudo leer la respuesta del servidor.");
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo completar la operación.");
  return data;
}
function plan(start, end) {
  return request(scoped("/plan?") + new URLSearchParams({start, end, ...(state.transport && {transport: state.transport})}));
}
function report(date) {
  return request(scoped("/reports/weekly?") + new URLSearchParams({date, ...(state.transport && {transport: state.transport})}));
}
function flash(message, error = false) {
  notice.textContent = message;
  notice.classList.toggle("error", error);
  notice.hidden = false;
}
function button(text, action, value = "", primary = false) {
  return `<button type="button" class="button ${primary ? "primary" : ""}" data-action="${action}" data-value="${html(value)}">${html(text)}</button>`;
}
function navButton(text, href) {
  return `<a class="button" href="#${href}">${html(text)}</a>`;
}
function header(title, description = "", action = "") {
  return `<header class="page-header"><div><h1>${html(title)}</h1>${description ? `<p class="description">${html(description)}</p>` : ""}</div>${action}</header>`;
}
function panel(title, content, action = "") {
  return `<section class="panel"><div class="panel-header"><h2>${html(title)}</h2>${action}</div>${content}</section>`;
}
function empty(message) {
  return `<p class="muted">${html(message)}</p>`;
}
function badges(task) {
  return `<span class="chip">${html(taskKinds[task.kind])}</span>${task.provisional ? ' <span class="chip provisional">Provisional</span>' : ""}`;
}
function options(entries, selected) {
  const matches = Array.isArray(selected) ? selected : [selected];
  return Object.entries(entries).map(([value, label]) =>
    `<option value="${html(value)}"${matches.includes(value) ? " selected" : ""}>${html(label)}</option>`).join("");
}
function list(rows, renderer, fallback) {
  return rows.length ? `<ul class="entries">${rows.map(renderer).join("")}</ul>` : empty(fallback);
}
function taskRow(task) {
  const info = [displayDate(task.end_date || task.start_date), priorities[task.priority], statusLabels[task.status]];
  if (task.application_stage) info.push(project.config.application_stages[task.application_stage] || task.application_stage);
  if (task.recurrence) info.push(`Repite ${task.recurrence.frequency === "daily" ? "a diario" : "cada semana"} hasta ${displayDate(task.recurrence.until)}`);
  if (task.depends_on?.length) info.push(`Depende de: ${task.depends_on.map((id) => tasks.find((item) => item.id === id)?.title || id).join(", ")}`);
  if (task.planned_minutes || task.actual_minutes) info.push(`${minutes(task.actual_minutes)} reales / ${minutes(task.planned_minutes)} planificadas`);
  return `<li class="entry"><div><strong>${html(task.title)}</strong> ${badges(task)}<span class="muted">${html(info.join(" · "))}</span></div>
    <div class="actions">${button("Editar", "edit-task", task.id)}${isComplete(task.status) ? "" : button("Completar", "complete-task", task.id)}</div></li>`;
}
function eventRow(event) {
  const time = event.start ? `${event.start}–${event.end}` : "Sin hora";
  const edit = event.task_id ? button("Editar", "edit-task", event.task_id) : button("Editar", "edit-event", event.id);
  const provisional = event.provisional ? ' <span class="chip provisional">Provisional</span>' : "";
  return `<li class="entry"><div><strong>${html(event.title)}</strong>${provisional}<span class="muted">${html(time)}${event.notes ? " · " + html(event.notes) : ""}</span></div>${edit}</li>`;
}
function metric(label, value) {
  return `<div class="metric"><span>${html(label)}</span><strong>${html(value)}</strong></div>`;
}
function isComplete(status) {
  return status === completionStatus();
}
function completionStatus() {
  return project?.config?.complete_status || "done";
}
function upcoming() {
  return tasks.filter((task) => task.end_date >= today && !isComplete(task.status) )
    .sort((left, right) => left.end_date.localeCompare(right.end_date)).slice(0, 5);
}
async function dashboard() {
  const [daily, weekly] = await Promise.all([plan(today, today), report(today)]);
  const due = upcoming();
  return {
    events: daily,
    markup: header(project.title, `${displayDate(project.start)} – ${displayDate(project.end)}`, button("+ Nueva tarea", "new-task", "", true)) +
      `<div class="stack">
        <section class="metrics" aria-label="Indicadores">
          ${metric("Tareas abiertas", tasks.filter((task) => !isComplete(task.status)).length)}
          ${weeklyMetrics(weekly)}
          ${project.monthly_revenue_target_cents ? metric("Meta mensual", euros(project.monthly_revenue_target_cents)) : ""}
        </section>
        <div class="split">
          ${panel("Plan de hoy", list(daily, eventRow, "No hay bloques para hoy."), navButton("Calendario", "calendar"))}
          ${panel("Próximos hitos", list(due, taskRow, "No hay hitos pendientes."), navButton("Gantt", "gantt"))}
        </div>
        ${panel("Objetivos", `<ul>${(project.goals || []).map((goal) => `<li>${html(goal)}</li>`).join("")}</ul>`)}
      </div>`
  };
}
function calendarBounds() {
  if (state.mode === "day") return [state.date, state.date];
  if (state.mode === "week") {
    const start = monday(state.date);
    return [start, offset(start, 6)];
  }
  const month = state.date.slice(0, 8) + "01";
  const next = fromDate(month);
  next.setUTCMonth(next.getUTCMonth() + 1);
  const last = offset(next.toISOString().slice(0, 10), -1);
  return [monday(month), offset(monday(last), 6)];
}
function range(start, end) {
  const days = [];
  for (let day = start; day <= end; day = offset(day, 1)) days.push(day);
  return days;
}
function byDay(records) {
  const groups = new Map();
  for (const event of records) {
    if (!groups.has(event.date)) groups.set(event.date, []);
    groups.get(event.date).push(event);
  }
  return groups;
}
function monthGrid(days, groups, date) {
  const headings = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"].map((day) => `<span class="day-label">${day}</span>`).join("");
  return `<div class="calendar" aria-label="Calendario mensual">${headings}${days.map((day) => {
    const items = groups.get(day) || [];
    const classes = ["day", day === today ? "today" : "", day.slice(0, 7) === date.slice(0, 7) ? "" : "out"].join(" ");
    const previews = items.slice(0, 2).map((event) => `<span class="day-title">${html(event.title)}</span>`).join("");
    return `<div class="${classes}"><button type="button" data-action="choose-day" data-value="${day}" aria-label="${html(displayDate(day))}, ${items.length} bloques"><strong>${Number(day.slice(-2))}</strong><span class="muted">${items.length || ""}</span></button>${previews}</div>`;
  }).join("")}</div>`;
}
function dayPanel(date, items) {
  return panel(formatLongDate.format(fromDate(date)), list(items || [], eventRow, "Sin bloques."), button("+ Tarea", "new-task", date));
}
async function calendarPage() {
  const {date, mode, transport} = state;
  const [start, end] = calendarBounds();
  const records = await plan(start, end);
  const groups = byDay(records);
  const days = range(start, end);
  const selector = Object.entries(calendarModes).map(([value, label]) =>
    `<button type="button" class="button" data-action="calendar-mode" data-value="${value}" aria-pressed="${value === mode}">${label}</button>`).join("");
  const controls = `<div class="toolbar">
    <div class="actions" aria-label="Vista del calendario">${selector}</div>
    <div class="actions">
      ${button("Anterior", "shift", -1)} ${button("Hoy", "choose-today")} ${button("Siguiente", "shift", 1)}
      <label>Fecha <input type="date" id="calendar-date" value="${html(date)}"></label>
      ${Object.keys(transportOptions).length ? `<label>Variante <select id="transport">${options(transportOptions, transport)}</select></label>` : ""}
    </div>
  </div>`;
  let calendar;
  if (mode === "month") calendar = monthGrid(days, groups, date);
  if (mode === "week") calendar = `<div class="week">${days.map((day) => dayPanel(day, groups.get(day))).join("")}</div>`;
  if (mode === "day") calendar = dayPanel(date, groups.get(date));
  return {events: records, markup: header("Calendario", "Horario de Madrid · selecciona una fecha para consultar y editar el plan.") + controls + calendar};
}
function tasksPage() {
  const rows = state.taskKind ? tasks.filter((task) => task.kind === state.taskKind) : tasks;
  const filter = `<label>Tipo <select id="task-kind">${options({"": "Todos", ...taskKinds}, state.taskKind)}</select></label>`;
  return header("Tareas", "Organiza el trabajo por categoría, estado y prioridad.", button("+ Nueva tarea", "new-task", "", true)) +
    panel("Seguimiento", list(rows, taskRow, "No hay tareas en esta categoría."), filter);
}
function boardPage() {
  const columns = Object.entries(statusLabels).map(([status, label]) => {
    const rows = tasks.filter((task) => task.status === status);
    const cards = rows.map((task) => `<div class="card"><strong>${html(task.title)}</strong> ${badges(task)}
      <p class="muted">${html(displayDate(task.end_date || task.start_date))} · ${html(priorities[task.priority])}</p>
      <label>Estado<select data-task-status="${html(task.id)}" aria-label="Estado de ${html(task.title)}">${options(statusLabels, task.status)}</select></label></div>`).join("");
    return panel(`${label} (${rows.length})`, cards || empty("Sin tareas."));
  });
  return header("Kanban", "Cambia el estado desde cada tarjeta.", button("+ Nueva tarea", "new-task", "", true)) +
    `<div class="board">${columns.join("")}</div>`;
}
function ganttPage() {
  const rows = tasks.filter((task) => task.start_date || task.end_date).sort((left, right) =>
    (left.start_date || left.end_date).localeCompare(right.start_date || right.end_date));
  const dateValues = rows.flatMap((task) => [task.start_date, task.end_date]).filter(Boolean).sort();
  const first = [project.start, dateValues[0]].filter(Boolean).sort()[0] || today;
  const last = [project.end, dateValues.at(-1)].filter(Boolean).sort().at(-1) || today;
  const duration = fromDate(last) - fromDate(first) + 86400000;
  const bars = rows.map((task) => {
    const start = task.start_date || task.end_date;
    const end = task.end_date || task.start_date;
    const position = 100 * (fromDate(start) - fromDate(first)) / duration;
    const width = 100 * (fromDate(end) - fromDate(start) + 86400000) / duration;
    return `<div class="card">
      <div class="toolbar"><div><strong>${html(task.title)}</strong> ${badges(task)}<p class="muted">${html(displayDate(start))} – ${html(displayDate(end))}</p></div>${button("Editar", "edit-task", task.id)}</div>
      <canvas class="timeline-track" role="img" aria-label="${html(task.title)}: ${html(displayDate(start))} – ${html(displayDate(end))}" data-start="${position}" data-width="${width}"></canvas>
    </div>`;
  });
  return header("Gantt", `${displayDate(first)} – ${displayDate(last)}`) + panel("Cronograma", `<div class="timeline">${bars.join("") || empty("Añade fechas a tus tareas para verlas aquí.")}</div>`);
}
function activityRow(item) {
  let details = `${displayDate(item.date)} · ${activityKinds[item.kind]} · ${minutes(item.actual_minutes)} reales / ${minutes(item.planned_minutes)} planificadas`;
  if (activityConfig[item.kind]?.financial) details += ` · ${euros(item.revenue_cents)} ingresos · ${euros(item.cost_cents)} costes · ${euros(item.revenue_cents - item.cost_cents)} beneficio`;
  return `<li class="entry"><div><strong>${html(item.title)}</strong><span class="muted">${html(details)}</span></div>${button("Editar", "edit-activity", item.id)}</li>`;
}
function logsPage() {
  const rows = (state.activityKind ? activities.filter((item) => item.kind === state.activityKind) : activities)
    .slice().sort((left, right) => right.date.localeCompare(left.date));
  const filter = `<label>Tipo <select id="activity-kind">${options({"": "Todos", ...activityKinds}, state.activityKind)}</select></label>`;
  return header("Registros", "Registra actividades, tiempo e importes del proyecto.", button("+ Nuevo registro", "new-activity", "", true)) +
    panel("Actividades", list(rows, activityRow, "Todavía no hay registros en esta categoría."), filter);
}
function weeklyMetrics(weekly) {
  const base = {
    planned_minutes: "Tiempo planificado", actual_minutes: "Tiempo real", calendar_minutes: "Tiempo en calendario",
    completed_tasks: "Tareas completadas", revenue_cents: "Ingresos", cost_cents: "Costes",
    profit_cents: "Beneficio", monthly_revenue_cents: "Ingresos del mes"
  };
  const configured = project.config.indicators;
  const labels = Object.keys(configured).length ? configured : base;
  return Object.entries(labels).map(([key, label]) => {
    let value = weekly[key];
    if (value === undefined && key.endsWith("_minutes")) value = weekly.activity_minutes_by_kind?.[key.slice(0, -8)];
    if (value === undefined && key.endsWith("_count")) value = weekly.task_count_by_kind?.[key.slice(0, -6)];
    if (key.endsWith("_cents")) return metric(label, euros(value));
    if (key.endsWith("_minutes")) return metric(label, minutes(value));
    return metric(label, value ?? 0);
  }).join("");
}
async function reportsPage() {
  const date = state.date;
  const weekly = await report(date);
  return header("Informes", `Semana del ${displayDate(weekly.start)} al ${displayDate(weekly.end)}`) +
    `<div class="toolbar"><label>Fecha de la semana <input type="date" id="report-date" value="${html(date)}"></label></div>
    <section class="metrics" aria-label="Indicadores de la semana">${weeklyMetrics(weekly)}</section>`;
}
function drawTimeline() {
  for (const item of view.querySelectorAll("canvas.timeline-track")) {
    const ratio = devicePixelRatio || 1;
    item.width = Math.round(item.clientWidth * ratio);
    item.height = Math.round(item.clientHeight * ratio);
    const context = item.getContext("2d");
    context.fillStyle = "#116650";
    context.fillRect(item.width * Number(item.dataset.start) / 100, 0, Math.max(4 * ratio, item.width * Number(item.dataset.width) / 100), item.height);
  }
}
function globalPage() {
  const cards = projects.map((item) => `<li class="entry"><div><strong>${html(item.title)}</strong><span class="muted">${html([item.start && displayDate(item.start), item.end && displayDate(item.end), item.description].filter(Boolean).join(" · "))}</span></div>${button("Abrir", "open-project", item.id)}</li>`);
  return header("Proyectos", "", `<div class="actions">${button("Importar JSON", "import-project")}${button("+ Nuevo proyecto", "new-project", "", true)}</div>`) +
    `<div class="stack"><section class="metrics" aria-label="Indicadores globales">
      ${metric("Proyectos", projects.length)}${metric("Tareas", globalSummary.tasks || 0)}
      ${metric("Completadas", globalSummary.completed_tasks || 0)}${metric("Actividades", globalSummary.activities || 0)}
      ${metric("Ingresos", euros(globalSummary.revenue_cents))}${metric("Beneficio", euros(globalSummary.profit_cents))}
    </section>${panel("Cartera de proyectos", cards.length ? `<ul class="entries">${cards.join("")}</ul>` : empty("Crea o importa un proyecto para empezar."))}</div>`;
}
function settingsPage() {
  return header("Configuración", project.title) +
    panel("Proyecto", `<p>${html(project.description || "")}</p><div class="actions">${button("Editar configuración", "edit-project", "", true)}${button("Guardar como plantilla", "save-template")}</div>`);
}
async function render() {
  const token = ++currentRender;
  const page = project && route() !== "projects" ? route() : "projects";
  view.setAttribute("aria-busy", "true");
  for (const link of document.querySelectorAll("nav a")) {
    link.hidden = !project && link.hash !== "#projects";
    if (link.hash === "#" + page) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  try {
    const result = await ({projects: globalPage, settings: settingsPage, dashboard, calendar: calendarPage, tasks: tasksPage, kanban: boardPage, gantt: ganttPage, logs: logsPage, reports: reportsPage}[page])();
    if (token !== currentRender) return;
    view.innerHTML = typeof result === "string" ? result : result.markup;
    events = result.events || [];
    drawTimeline();
  } catch (error) {
    if (token !== currentRender) return;
    view.innerHTML = `${header(modeNav[page])}<p>${html(error.message)}</p>${button("Reintentar", "reload")}`;
  } finally {
    if (token === currentRender) view.setAttribute("aria-busy", "false");
  }
}
async function reload(selected = project?.id || "") {
  const token = ++currentReload;
  view.setAttribute("aria-busy", "true");
  projectSelect.disabled = true;
  try {
    const [listedProjects, listedTemplates, summary] = await Promise.all([request("/api/projects"), request("/api/templates"), request("/api/dashboard")]);
    if (token !== currentReload) return;
    const nextProjects = listedProjects.projects || listedProjects;
    const nextId = nextProjects.some((item) => item.id === selected) ? selected : "";
    const [nextProject, nextTasks, nextActivities] = nextId
      ? await Promise.all([request(projectPath(nextId, "")), request(projectPath(nextId, "/tasks")), request(projectPath(nextId, "/activities"))])
      : [undefined, [], []];
    if (token !== currentReload) return;
    projects = nextProjects;
    templates = listedTemplates.templates || listedTemplates;
    globalSummary = summary;
    project = nextProject;
    tasks = nextTasks;
    activities = nextActivities;
    projectSelect.innerHTML = options({"": "Todos los proyectos", ...Object.fromEntries(projects.map((item) => [item.id, item.title]))}, nextId);
    if (project) {
      const config = project.config;
      statusLabels = config.statuses;
      priorities = config.priorities;
      taskKinds = config.task_kinds;
      activityKinds = config.activity_kinds;
      activityConfig = Object.fromEntries(config.financial_activity_kinds.map((kind) => [kind, {financial: true}]));
      transportOptions = config.transport_modes;
      if (!Object.hasOwn(transportOptions, state.transport)) state.transport = Object.keys(transportOptions)[0] || "";
      if (!Object.hasOwn(taskKinds, state.taskKind)) state.taskKind = "";
      if (!Object.hasOwn(activityKinds, state.activityKind)) state.activityKind = "";
    }
    exportLink.hidden = !project;
    if (project) exportLink.href = scoped("/export");
    await render();
  } catch (error) {
    if (token !== currentReload) return;
    projectSelect.value = project?.id || "";
    view.setAttribute("aria-busy", "false");
    view.innerHTML = `${header("Project Manager")}<p>${html(error.message)}</p>${button("Reintentar", "reload")}`;
  } finally {
    if (token === currentReload) projectSelect.disabled = false;
  }
}
async function openProject(id) {
  await reload(id);
  location.hash = id ? "#dashboard" : "#projects";
}

function input(label, name, value, attributes = "") {
  return `<label>${html(label)}<input name="${html(name)}" value="${html(value)}" ${attributes}></label>`;
}
function select(label, name, entries, selected) {
  return `<label>${html(label)}<select aria-label="${html(label)}" name="${name}">${options(entries, selected)}</select></label>`;
}
function notes(value) {
  return `<label>Notas<textarea name="notes" aria-label="Notas" maxlength="4000">${html(value)}</textarea></label>`;
}
function grid(fields) {
  return `<div class="form-grid">${fields.join("")}</div>`;
}
function timeFields(row) {
  return grid([
    input("Minutos planificados", "planned_minutes", row.planned_minutes ?? 0, 'type="number" min="0" max="525600" step="1" required'),
    input("Minutos reales", "actual_minutes", row.actual_minutes ?? 0, 'type="number" min="0" max="525600" step="1" required')
  ]);
}
function openEditor(title, contents, save, focusTarget) {
  editor.innerHTML = `<h2 id="editor-title">${html(title)}</h2>
    <form id="edit-form">
      ${contents}
      <p class="form-error" role="alert" hidden></p>
      <div class="actions"><button type="submit" class="button primary">Guardar</button>
      <button class="button" type="button" data-close>Cancelar</button></div>
    </form>`;
  const form = editor.querySelector("form");
  const errorBox = form.querySelector(".form-error");
  const submit = form.querySelector("[type=submit]");
  const cancel = form.querySelector("[data-close]");
  cancel.onclick = () => editor.close();
  editor.oncancel = (event) => {
    if (submit.disabled) event.preventDefault();
  };
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    cancel.disabled = true;
    errorBox.hidden = true;
    try {
      await save(Object.fromEntries(new FormData(form)), form);
      await reload();
      editor.close();
      flash("Cambios guardados.");
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
      submit.disabled = false;
      cancel.disabled = false;
    }
  });
  editor.showModal();
  editor.querySelector(`[name="${focusTarget}"]`)?.focus();
}
function textarea(label, name, value, attributes = "") {
  return `<label>${html(label)}<textarea aria-label="${html(label)}" name="${name}" ${attributes}>${html(value)}</textarea></label>`;
}
const configurationLabels = {
  task_kinds: "Categorías de tareas", statuses: "Estados", priorities: "Prioridades",
  activity_kinds: "Tipos de actividad", custom_fields: "Campos personalizados",
  indicators: "Indicadores", transport_modes: "Variantes de calendario", application_stages: "Etapas de seguimiento"
};
function stringifyOptions(entries = {}) {
  return Object.entries(entries).map(([key, label]) => `${key}=${label}`).join("\n");
}
function parseOptions(value) {
  return Object.fromEntries(value.split("\n").map((line) => line.trim()).filter(Boolean).map((line) => {
    const separator = line.indexOf("=");
    if (separator < 1) throw new Error("Usa clave=etiqueta para cada opción.");
    return [line.slice(0, separator).trim(), line.slice(separator + 1).trim()];
  }));
}
function projectEditor(item = {}) {
  const existing = Boolean(item.id);
  const fields = input("Nombre", "title", item.title, 'maxlength="160" required') +
    grid([input("Inicio", "start", item.start, 'type="date"'), input("Fin", "end", item.end, 'type="date"')]) +
    textarea("Descripción", "description", item.description, 'maxlength="4000"') +
    (existing
      ? textarea("Objetivos (uno por línea)", "goals", (item.goals || []).join("\n")) +
        input("Meta mensual de ingresos (€)", "target", (item.monthly_revenue_target_cents || 0) / 100, 'type="number" min="0" step="0.01"') +
        '<p class="muted">Introduce una opción por línea con el formato clave=etiqueta.</p>' +
        grid(Object.entries(configurationLabels).map(([key, label]) => textarea(label, key, stringifyOptions(item.config[key]), 'rows="3"'))) +
        input("Claves de actividades financieras (separadas por comas)", "financial", item.config.financial_activity_kinds.join(", "))
      : select("Plantilla", "template_id", {"": "Proyecto en blanco", ...Object.fromEntries(templates.map((template) => [template.id, template.title]))}, ""));
  openEditor(existing ? "Editar proyecto" : "Nuevo proyecto", fields, async (form) => {
    const body = {title: form.title, description: form.description, start: form.start || null, end: form.end || null};
    if (existing) {
      body.goals = form.goals.split("\n").map((value) => value.trim()).filter(Boolean);
      body.monthly_revenue_target_cents = Math.round(Number(form.target) * 100);
      body.config = {...item.config, ...Object.fromEntries(Object.keys(configurationLabels).map((key) => [key, parseOptions(form[key])])), financial_activity_kinds: form.financial.split(",").map((key) => key.trim()).filter(Boolean)};
    } else if (form.template_id) body.template_id = form.template_id;
    const saved = await request(existing ? scoped("") : "/api/projects", existing ? "PATCH" : "POST", body);
    if (!existing) await openProject(saved.id);
  }, "title");
}
function importProject() {
  openEditor("Importar proyecto", '<label>Archivo de exportación JSON<input type="file" name="file" accept=".json,application/json" required></label>', async ({file}) => {
    let payload;
    try { payload = JSON.parse(await file.text()); }
    catch { throw new Error("El archivo debe contener una exportación JSON válida."); }
    const result = await request("/api/projects/import", "POST", payload);
    await openProject(result.id);
  }, "file");
}
function saveTemplate() {
  openEditor("Guardar plantilla", input("Nombre", "title", project.title, 'maxlength="160" required'), async ({title}) => {
    await request("/api/templates", "POST", {title, project_id: project.id});
  }, "title");
}
function customFieldInputs(record) {
  return grid(Object.entries(project.config.custom_fields).map(([key, label]) =>
    input(label, "custom_" + key, record.custom_fields?.[key], 'maxlength="500"')));
}
function readCustomFields(form, body) {
  body.custom_fields = {};
  for (const key of Object.keys(project.config.custom_fields)) {
    if (form["custom_" + key]) body.custom_fields[key] = form["custom_" + key];
    delete body["custom_" + key];
  }
}
function taskEditor(task = {}) {
  const contents = input("Título", "title", task.title, 'maxlength="160" required') +
    grid([select("Tipo", "kind", taskKinds, task.kind || Object.keys(taskKinds)[0]), select("Prioridad", "priority", priorities, task.priority || Object.keys(priorities)[0])]) +
    grid([input("Inicio", "start_date", task.start_date, 'type="date"'), input("Fin", "end_date", task.end_date, 'type="date"')]) +
    select("Estado", "status", statusLabels, task.status || Object.keys(statusLabels)[0]) +
    (Object.keys(project.config.application_stages).length ? select("Etapa de seguimiento", "application_stage", {"": "Sin etapa", ...project.config.application_stages}, task.application_stage || "") : "") +
    `<label class="checkbox"><input type="checkbox" name="provisional"${task.provisional ? " checked" : ""}>Fecha provisional</label>` +
    timeFields(task) + grid([
      select("Repetición", "frequency", {"": "Sin repetición", daily: "Diaria", weekly: "Semanal"}, task.recurrence?.frequency || ""),
      input("Repetir hasta", "until", task.recurrence?.until, 'type="date"')
    ]) + `<label>Depende de<select multiple name="depends_on" aria-label="Depende de">${options(Object.fromEntries(tasks.filter((row) => row.id !== task.id).map((row) => [row.id, row.title])), task.depends_on || [])}</select></label>` +
    customFieldInputs(task) + notes(task.notes);
  openEditor(task.id ? "Editar tarea" : "Nueva tarea", contents, async (body, form) => {
    body.start_date ||= null;
    body.end_date ||= null;
    if (body.end_date && body.start_date && body.end_date < body.start_date) throw new Error("La fecha de fin debe ser igual o posterior al inicio.");
    body.provisional = body.provisional === "on";
    body.application_stage ||= null;
    if (body.frequency && (!body.start_date || !body.until)) throw new Error("Una tarea recurrente necesita fecha de inicio y fecha de fin de repetición.");
    body.recurrence = body.frequency ? {frequency: body.frequency, until: body.until} : null;
    body.depends_on = new FormData(form).getAll("depends_on");
    delete body.frequency;
    delete body.until;
    readCustomFields(body, body);
    body.planned_minutes = Number(body.planned_minutes);
    body.actual_minutes = Number(body.actual_minutes);
    await request(scoped(task.id ? "/tasks/" + encodeURIComponent(task.id) : "/tasks"), task.id ? "PATCH" : "POST", body);
  }, "title");
}
function activityEditor(activity = {}) {
  const kind = activity.kind || state.activityKind || Object.keys(activityKinds)[0];
  const step = 'type="number" min="0" max="10000000" step="0.01" required';
  const contents = grid([
    select("Tipo", "kind", activityKinds, kind),
    input("Fecha", "date", activity.date ?? state.date, 'type="date" required')
  ]) + input("Título", "title", activity.title, 'maxlength="160" required') + timeFields(activity) +
    `<div id="finance-fields"${activityConfig[kind]?.financial ? "" : " hidden"}>${grid([
      input("Ingresos (€)", "revenue_cents", (activity.revenue_cents ?? 0) / 100, step),
      input("Costes (€)", "cost_cents", (activity.cost_cents ?? 0) / 100, step)
    ])}</div>` + customFieldInputs(activity) + notes(activity.notes);
  openEditor(activity.id ? "Editar registro" : "Nuevo registro", contents, async (body) => {
    body.planned_minutes = Number(body.planned_minutes);
    body.actual_minutes = Number(body.actual_minutes);
    body.revenue_cents = activityConfig[body.kind]?.financial ? Math.round(Number(body.revenue_cents) * 100) : 0;
    body.cost_cents = activityConfig[body.kind]?.financial ? Math.round(Number(body.cost_cents) * 100) : 0;
    readCustomFields(body, body);
    await request(scoped(activity.id ? "/activities/" + encodeURIComponent(activity.id) : "/activities"), activity.id ? "PATCH" : "POST", body);
  }, "title");
  const kindControl = editor.querySelector('[name="kind"]');
  const financeFields = editor.querySelector("#finance-fields");
  const updateKind = () => {
    financeFields.hidden = !activityConfig[kindControl.value]?.financial;
    for (const item of financeFields.querySelectorAll("input")) item.disabled = financeFields.hidden;
  };
  kindControl.addEventListener("change", updateKind);
  updateKind();
}
function eventEditor(event) {
  const time = 'placeholder="HH:MM" pattern="[0-9]{2}:[0-9]{2}"';
  const contents = `<p class="muted">${html(displayDate(event.date))} · Edición de este bloque.</p>` +
    input("Título", "title", event.title, 'maxlength="160" required') +
    grid([input("Inicio", "start", event.start, time), input("Fin", "end", event.end, time)]) + notes(event.notes) +
    '<label class="checkbox"><input type="checkbox" name="hidden">Omitir este bloque</label>';
  openEditor("Editar bloque", contents, async (body) => {
    body.hidden = body.hidden === "on";
    body.start ||= null;
    body.end ||= null;
    await request(scoped("/plan/" + encodeURIComponent(event.id)) + "?" + new URLSearchParams(state.transport ? {transport: state.transport} : {}), "PATCH", body);
  }, "title");
}
async function updateStatus(id, status) {
  try {
    await request(scoped("/tasks/" + encodeURIComponent(id)), "PATCH", {status});
    flash("Estado actualizado.");
  } catch (error) {
    flash(error.message, true);
  }
  await reload();
}
function shift(direction) {
  if (state.mode === "month") {
    const next = fromDate(state.date.slice(0, 8) + "01");
    next.setUTCMonth(next.getUTCMonth() + direction);
    state.date = next.toISOString().slice(0, 10);
  } else {
    state.date = offset(state.date, direction * (state.mode === "week" ? 7 : 1));
  }
  render();
}
const actions = {
  "open-project": openProject,
  "new-project": () => projectEditor(),
  "edit-project": () => projectEditor(project),
  "import-project": importProject,
  "save-template": saveTemplate,
  "new-task": (value) => taskEditor(value ? {start_date: value, end_date: value} : {}),
  "edit-task": (id) => taskEditor(tasks.find((item) => String(item.id) === id)),
  "complete-task": (id) => updateStatus(id, completionStatus()),
  "new-activity": () => activityEditor(),
  "edit-activity": (id) => activityEditor(activities.find((item) => String(item.id) === id)),
  "edit-event": (id) => {
    const match = events.find((item) => String(item.id) === id);
    if (match) eventEditor(match);
  },
  "choose-today": () => {state.date = today; render();},
  "choose-day": (day) => {state.date = day; state.mode = "day"; render();},
  "calendar-mode": (mode) => {state.mode = mode; render();},
  shift: (value) => shift(Number(value)),
  reload: () => reload()
};
view.addEventListener("click", (event) => {
  const target = event.target.closest("[data-action]");
  if (target && Object.hasOwn(actions, target.dataset.action)) {
    if (target.dataset.action === "complete-task") target.disabled = true;
    actions[target.dataset.action](target.dataset.value);
  }
});
view.addEventListener("change", (event) => {
  const control = event.target;
  if (control.dataset.taskStatus) {
    control.disabled = true;
    updateStatus(control.dataset.taskStatus, control.value);
    return;
  }
  if (control.id === "calendar-date" || control.id === "report-date") {
    if (!control.value || !control.validity.valid) {
      control.value = state.date;
      return;
    }
    state.date = control.value;
  }
  if (control.id === "transport") state.transport = control.value;
  if (control.id === "task-kind") state.taskKind = control.value;
  if (control.id === "activity-kind") state.activityKind = control.value;
  render();
});
projectSelect.addEventListener("change", () => openProject(projectSelect.value));
window.addEventListener("hashchange", () => {
  if (location.hash === "#main") return;
  notice.hidden = true;
  render();
  document.querySelector("#main").focus();
});
window.addEventListener("resize", drawTimeline);
reload();
