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
  if (user) $("user-name").textContent = user.name;
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
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
