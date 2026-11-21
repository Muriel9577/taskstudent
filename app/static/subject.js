const $ = (id) => document.getElementById(id);
const subjectId = location.pathname.split("/").pop();

async function api(path, body, method) {
  const res = await fetch(path, {
    method: method || (body === undefined ? "GET" : "POST"),
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

function text(tag, value, className) {
  const el = document.createElement(tag);
  el.textContent = value; // textContent, щоб не вставляти HTML з даних користувача
  if (className) el.className = className;
  return el;
}

function button(label, className, onClick) {
  const b = text("button", label, className);
  b.type = "button";
  b.onclick = onClick;
  return b;
}

function showError(data) {
  $("message").textContent = (data && data.error) || "Помилка";
}

async function load() {
  const subject = await api(`/api/subjects/${subjectId}`);
  if (subject.status === 401) { location.href = "/"; return; }
  if (!subject.ok) { $("subject-title").textContent = "Предмет не знайдено"; return; }
  $("subject-title").textContent = subject.data.title;
  $("subject-pass").textContent = `Прохідний бал: ${subject.data.pass_score}`;

  const { data } = await api(`/api/subjects/${subjectId}/tasks`);
  const list = $("tasks");
  list.replaceChildren();
  $("tasks-empty").hidden = data.length > 0;
  data.forEach((t) => list.appendChild(taskItem(t)));

  const progress = await api(`/api/subjects/${subjectId}/progress`);
  if (progress.ok) renderProgress(progress.data);
}

const RING_LENGTH = 276.46; // довжина кола з радіусом 44

function renderProgress(p) {
  $("ring-fg").style.strokeDashoffset = RING_LENGTH * (1 - p.percent / 100);
  $("ring-text").textContent = `${p.percent}%`;
  $("ring-caption").textContent = p.total_tasks === 0
    ? "Завдань ще немає"
    : `Виконано ${p.done_tasks} з ${p.total_tasks} завдань`;

  const fill = $("bar-fill");
  const bar = fill.parentElement;
  const warn = $("score-warn");
  warn.hidden = true;

  if (p.pass_score === 0) {
    fill.style.width = "0%";
    fill.classList.remove("passed");
    bar.setAttribute("aria-valuenow", "0");
    $("score-text").textContent = `Прохідний бал не вказано. Набрано: ${p.earned_score}`;
    return;
  }

  const share = Math.min(100, Math.round((p.earned_score / p.pass_score) * 100));
  fill.style.width = `${share}%`;
  fill.classList.toggle("passed", p.passed);
  bar.setAttribute("aria-valuenow", String(share));
  $("score-text").textContent = p.passed
    ? `Прохідний бал досягнуто: ${p.earned_score} з ${p.pass_score}`
    : `Набрано ${p.earned_score} з ${p.pass_score} потрібних, ще ${p.remaining_to_pass}`;

  if (!p.reachable && p.total_tasks > 0) {
    warn.textContent = `Навіть за максимальні бали за решту завдань прохідний бал недосяжний (максимум ${p.max_possible_score}).`;
    warn.hidden = false;
  }
}

async function save(task, changes) {
  const { ok, data } = await api(`/api/tasks/${task.id}`, changes, "PUT");
  if (ok) { $("message").textContent = ""; }
  else showError(data);
  load();
}

function taskItem(t) {
  const li = document.createElement("li");
  li.className = "task" + (t.status === "done" ? " done" : "");

  const check = document.createElement("input");
  check.type = "checkbox";
  check.checked = t.status === "done";
  check.title = "Виконано";
  check.onchange = () => save(t, { status: check.checked ? "done" : "new" });

  const score = document.createElement("input");
  score.type = "number";
  score.min = "0";
  score.step = "any";
  score.className = "score";
  score.placeholder = "бал";
  score.value = t.score === null ? "" : t.score;
  score.title = "Набраний бал";
  score.onchange = () => save(t, { score: score.value === "" ? null : Number(score.value) });

  li.append(
    check,
    text("span", t.title, "title"),
    text("span", t.deadline ? `до ${t.deadline}` : "без дедлайну", "meta"),
    score,
    text("span", `/ ${t.max_score}`, "meta"),
    button("Змінити", "secondary", () => li.replaceWith(taskEditor(t))),
    button("Видалити", "danger", async () => {
      if (!confirm(`Видалити завдання «${t.title}»?`)) return;
      await api(`/api/tasks/${t.id}`, undefined, "DELETE");
      load();
    }),
  );
  return li;
}

function taskEditor(t) {
  const li = document.createElement("li");
  li.className = "task";
  const title = document.createElement("input");
  title.value = t.title;
  title.className = "title";
  const deadline = document.createElement("input");
  deadline.type = "date";
  deadline.value = t.deadline || "";
  const max = document.createElement("input");
  max.type = "number";
  max.min = "0";
  max.step = "any";
  max.value = t.max_score;
  max.className = "score";
  li.append(
    title, deadline, max,
    button("Зберегти", "", () => save(t, {
      title: title.value,
      deadline: deadline.value,
      max_score: max.value === "" ? null : Number(max.value),
    })),
    button("Скасувати", "secondary", load),
  );
  return li;
}

$("task-form").onsubmit = async (e) => {
  e.preventDefault();
  const { ok, data } = await api(`/api/subjects/${subjectId}/tasks`, {
    title: $("task-title").value,
    deadline: $("task-deadline").value,
    max_score: $("task-max").value === "" ? null : Number($("task-max").value),
  });
  if (ok) {
    $("message").textContent = "";
    $("task-form").reset();
    load();
  } else {
    showError(data);
  }
};

load();
