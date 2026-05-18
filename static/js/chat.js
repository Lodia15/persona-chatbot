import { API_CHAT_URL, SESSION_KEY } from "./config.js";
import { bindAutoResize, bindEnterSubmit } from "./ui.js";

const logEl = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("msg");
const sendBtn = document.getElementById("send");
const errEl = document.getElementById("err");
const statusEl = document.getElementById("composer-status");
const newChatBtn = document.getElementById("newChat");

function sessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

function resetSession() {
  localStorage.removeItem(SESSION_KEY);
  logEl.innerHTML = "";
  appendSystem("New conversation.");
}

function appendSystem(text) {
  const d = document.createElement("p");
  d.className = "chat-log__system";
  d.textContent = text;
  logEl.appendChild(d);
  logEl.scrollTop = logEl.scrollHeight;
}

function appendBubble(role, text) {
  const row = document.createElement("article");
  row.className = `chat-row chat-row--${role === "user" ? "user" : "bot"}`;

  const bubble = document.createElement("div");
  bubble.className = "chat-row__bubble";
  bubble.textContent = text;
  row.appendChild(bubble);

  const meta = document.createElement("div");
  meta.className = "chat-row__meta";
  meta.textContent = role === "user" ? "You" : "Persona";
  row.appendChild(meta);

  logEl.appendChild(row);
  logEl.scrollTop = logEl.scrollHeight;
}

function setError(msg) {
  if (!msg) {
    errEl.hidden = true;
    errEl.textContent = "";
    return;
  }
  errEl.hidden = false;
  errEl.textContent = msg;
}

function setSending(sending) {
  if (!statusEl) return;
  if (sending) {
    statusEl.hidden = false;
    statusEl.textContent = "Sending…";
  } else {
    statusEl.hidden = true;
    statusEl.textContent = "";
  }
}

async function sendMessage(text) {
  setError("");
  setSending(true);
  sendBtn.disabled = true;
  const sid = sessionId();

  let res;
  try {
    res = await fetch(API_CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sid }),
    });
  } catch (e) {
    const m = e && e.message ? e.message : String(e);
    if (/failed to fetch|load failed|networkerror/i.test(m)) {
      throw new Error(
        "Cannot reach the API. Start the server from the project folder: uvicorn app:app --reload --host 127.0.0.1 --port 8000"
      );
    }
    throw new Error(m);
  }

  const raw = await res.text();
  let data = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    throw new Error(`HTTP ${res.status}: response was not JSON. ${raw.slice(0, 240)}`);
  }

  if (!res.ok) {
    const detail = data.detail;
    let msg;
    if (Array.isArray(detail)) {
      msg = detail.map((d) => (d && (d.msg || d.message)) || String(d)).join(" ");
    } else if (typeof detail === "string") {
      msg = detail;
    } else if (detail && typeof detail === "object") {
      msg = JSON.stringify(detail);
    } else {
      msg = `HTTP ${res.status}`;
    }
    throw new Error(msg);
  }

  if (typeof data.reply !== "string") {
    throw new Error("Bad response: missing reply.");
  }

  if (data.session_id) {
    localStorage.setItem(SESSION_KEY, data.session_id);
  }

  return data.reply;
}

function init() {
  const runResizeOnce = bindAutoResize(input);
  bindEnterSubmit(input, form);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    if (text.toLowerCase() === "exit") {
      input.value = "";
      input.style.height = "auto";
      runResizeOnce();
      localStorage.removeItem(SESSION_KEY);
      logEl.innerHTML = "";
      appendSystem(
        "Session ended — new thread. (Same as typing exit in the terminal.)"
      );
      appendSystem(
        "Ask something. Answers stay in character using your ingested documents."
      );
      setError("");
      input.focus();
      return;
    }

    appendBubble("user", text);
    input.value = "";
    input.style.height = "auto";
    runResizeOnce();

    try {
      const reply = await sendMessage(text);
      appendBubble("bot", reply);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setSending(false);
      sendBtn.disabled = false;
      input.focus();
    }
  });

  newChatBtn.addEventListener("click", () => {
    resetSession();
    input.focus();
  });

  appendSystem(
    "Ask something. Type exit to clear the session (same as the terminal). Answers stay in character using your ingested documents."
  );
  input.focus();
}

init();
