const $ = (id) => document.getElementById(id);
let mode = "login";

function setMode(next) {
  mode = next;
  $("tab-login").classList.toggle("active", mode === "login");
  $("tab-register").classList.toggle("active", mode === "register");
  $("name-row").hidden = mode !== "register";
  $("submit").textContent = mode === "login" ? "Увійти" : "Зареєструватися";
  $("message").textContent = "";
}

function showUser(user) {
  $("guest").hidden = !!user;
  $("user").hidden = !user;
  if (user) {
    $("user-name").textContent = user.name;
    loadSubjects();
  }
}

async function api(path, body, method) {
  const res = await fetch(path, {
    method: method || (body === undefined ? "GET" : "POST"),
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, data };
}

$("tab-login").onclick = () => setMode("login");
$("tab-register").onclick = () => setMode("register");

$("form").onsubmit = async (e) => {
  e.preventDefault();
  const body = { email: $("email").value, password: $("password").value };
  if (mode === "register") body.name = $("name").value;
  const { ok, data } = await api(mode === "login" ? "/api/login" : "/api/register", body);
  if (ok) {
    $("message").textContent = "";
    showUser(data);
  } else {
    $("message").textContent = data.error || "Помилка";
  }
};

$("logout").onclick = async () => {
  await api("/api/logout", {});
  showUser(null);
};

api("/api/me").then(({ ok, data }) => showUser(ok ? data : null));

// ---------- Предмети ----------
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

async function loadSubjects() {
  const { ok, data } = await api("/api/subjects");
  if (!ok) return;
  const list = $("subjects");
  list.replaceChildren();
  $("subjects-empty").hidden = data.length > 0;
  data.forEach((s) => list.appendChild(subjectItem(s)));
}

function subjectItem(s) {
  const li = document.createElement("li");
  li.append(
    text("span", s.title, "grow"),
    text("span", `прохідний бал: ${s.pass_score}`, "pass"),
    button("Змінити", "secondary", () => li.replaceWith(subjectEditor(s))),
    button("Видалити", "danger", async () => {
      if (!confirm(`Видалити предмет «${s.title}» разом із завданнями?`)) return;
      await api(`/api/subjects/${s.id}`, undefined, "DELETE");
      loadSubjects();
    }),
  );
  return li;
}

function subjectEditor(s) {
  const li = document.createElement("li");
  const title = document.createElement("input");
  title.value = s.title;
  title.className = "grow";
  const pass = document.createElement("input");
  pass.type = "number";
  pass.min = "0";
  pass.step = "any";
  pass.value = s.pass_score;
  li.append(
    title,
    pass,
    button("Зберегти", "", async () => {
      const { ok, data } = await api(
        `/api/subjects/${s.id}`,
        { title: title.value, pass_score: pass.value === "" ? null : Number(pass.value) },
        "PUT",
      );
      if (ok) loadSubjects();
      else $("message").textContent = data.error || "Помилка";
    }),
    button("Скасувати", "secondary", loadSubjects),
  );
  return li;
}

$("subject-form").onsubmit = async (e) => {
  e.preventDefault();
  const { ok, data } = await api("/api/subjects", {
    title: $("subject-title").value,
    pass_score: Number($("subject-pass").value),
  });
  if (ok) {
    $("message").textContent = "";
    $("subject-form").reset();
    loadSubjects();
  } else {
    $("message").textContent = data.error || "Помилка";
  }
};
