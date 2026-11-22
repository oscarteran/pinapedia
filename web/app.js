// Chat de PiñaPedia: crea una sesión ADK y consume /run_sse.
(() => {
  const APP = "app";

  const I18N = {
    es: {
      tagline: "Asistente multi-agente para producción de piña",
      reset: "Nueva conversación",
      welcomeTitle: "¿Qué quieres saber de tu cultivo?",
      welcomeText: "Un coordinador dirige tu pregunta al especialista: agrónomo, planificador o clima y mercado.",
      placeholder: "Escribe tu pregunta…",
      send: "Enviar",
      foot: "Demo de portafolio · Google ADK + Gemini en Cloud Run · las respuestas pueden contener errores.",
      tool: "herramienta",
      transfer: "pasa a",
      error: "No pude responder. Intenta de nuevo en un momento.",
      chips: [
        "¿Cuándo conviene hacer la inducción floral en MD2?",
        "Sembré el 15 de marzo de 2026, ¿cuándo cosecho?",
        "¿Cuánto cuesta sembrar 3 hectáreas?",
        "¿Va a llover esta semana en Loma Bonita?",
      ],
    },
    en: {
      tagline: "Multi-agent assistant for pineapple production",
      reset: "New chat",
      welcomeTitle: "What do you want to know about your crop?",
      welcomeText: "A coordinator routes your question to a specialist: agronomist, planner, or weather and market.",
      placeholder: "Type your question…",
      send: "Send",
      foot: "Portfolio demo · Google ADK + Gemini on Cloud Run · answers may contain mistakes.",
      tool: "tool",
      transfer: "hands off to",
      error: "I couldn't answer. Please try again in a moment.",
      chips: [
        "When should flower induction be done in MD2?",
        "I planted on March 15, 2026. When do I harvest?",
        "How much does it cost to plant 3 hectares?",
        "Will it rain this week in Loma Bonita?",
      ],
    },
  };

  const AGENT_LABEL = {
    coordinador: "coordinador",
    agronomo: "agrónomo",
    planificador: "planificador",
    mercado_clima: "clima y mercado",
  };

  const $ = (s) => document.querySelector(s);
  const chat = $("#chat");
  const form = $("#form");
  const input = $("#input");
  const send = $("#send");

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* sin almacenamiento */ } },
  };

  let lang = store.get("pp_lang") || ((navigator.language || "es").slice(0, 2) === "en" ? "en" : "es");
  let userId = store.get("pp_user");
  if (!userId) {
    userId = "u-" + (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2));
    store.set("pp_user", userId);
  }
  let sessionId = null;

  // ---------- idioma ----------
  function applyLang() {
    const t = I18N[lang];
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t[el.dataset.i18n]; });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t[el.dataset.i18nPlaceholder]; });
    $("#lang").textContent = lang === "es" ? "EN" : "ES";
    const chips = $("#chips");
    if (chips) {
      chips.innerHTML = "";
      t.chips.forEach((q) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "chip";
        b.textContent = q;
        b.onclick = () => ask(q);
        chips.appendChild(b);
      });
    }
  }

  // ---------- markdown mínimo y seguro ----------
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function inline(s) {
    return esc(s)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
  }

  function md(text) {
    const lines = text.replace(/\r/g, "").split("\n");
    let html = "", list = null, table = [];
    const closeList = () => { if (list) { html += `</${list}>`; list = null; } };
    const flushTable = () => {
      if (!table.length) return;
      const rows = table.filter((r) => !/^\s*\|?\s*:?-{2,}/.test(r));
      html += "<table>" + rows.map((r, i) => {
        const cells = r.trim().replace(/^\||\|$/g, "").split("|").map((c) => inline(c.trim()));
        const tag = i === 0 ? "th" : "td";
        return "<tr>" + cells.map((c) => `<${tag}>${c}</${tag}>`).join("") + "</tr>";
      }).join("") + "</table>";
      table = [];
    };
    for (const raw of lines) {
      const line = raw.trimEnd();
      if (/^\s*\|.*\|\s*$/.test(line)) { closeList(); table.push(line); continue; }
      flushTable();
      let m;
      if ((m = line.match(/^\s*[-*]\s+(.*)/))) {
        if (list !== "ul") { closeList(); html += "<ul>"; list = "ul"; }
        html += `<li>${inline(m[1])}</li>`;
      } else if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) {
        if (list !== "ol") { closeList(); html += "<ol>"; list = "ol"; }
        html += `<li>${inline(m[1])}</li>`;
      } else if ((m = line.match(/^#{1,4}\s+(.*)/))) {
        closeList(); html += `<p><strong>${inline(m[1])}</strong></p>`;
      } else if (line.trim() === "") {
        closeList();
      } else {
        closeList(); html += `<p>${inline(line)}</p>`;
      }
    }
    closeList(); flushTable();
    return html;
  }

  // ---------- UI ----------
  function addMsg(role, html, agent) {
    $("#welcome")?.remove();
    const wrap = document.createElement("div");
    wrap.className = `msg ${role}`;
    if (agent) {
      const tag = document.createElement("span");
      tag.className = "agent";
      tag.textContent = AGENT_LABEL[agent] || agent;
      wrap.appendChild(tag);
    }
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.innerHTML = html;
    wrap.appendChild(bubble);
    chat.appendChild(wrap);
    wrap.scrollIntoView({ behavior: "smooth", block: "end" });
    return wrap;
  }

  function addTrace(container, text) {
    let trace = container.querySelector(".trace");
    if (!trace) {
      trace = document.createElement("div");
      trace.className = "trace";
      container.prepend(trace);
    }
    const s = document.createElement("span");
    s.textContent = text;
    trace.appendChild(s);
  }

  function typing() {
    const wrap = document.createElement("div");
    wrap.className = "msg bot";
    wrap.innerHTML = '<div class="bubble typing"><i></i><i></i><i></i></div>';
    chat.appendChild(wrap);
    wrap.scrollIntoView({ behavior: "smooth", block: "end" });
    return wrap;
  }

  // ---------- API ----------
  async function ensureSession() {
    if (sessionId) return sessionId;
    const r = await fetch(`/apps/${APP}/users/${encodeURIComponent(userId)}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    if (!r.ok) throw new Error(`session ${r.status}`);
    sessionId = (await r.json()).id;
    return sessionId;
  }

  async function ask(text) {
    text = text.trim();
    if (!text || send.disabled) return;
    const t = I18N[lang];
    addMsg("user", esc(text));
    input.value = "";
    autosize();
    send.disabled = true;
    const status = typing();
    const traceBox = document.createElement("div");
    traceBox.className = "msg bot";

    try {
      await ensureSession();
      const r = await fetch("/run_sse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          app_name: APP,
          user_id: userId,
          session_id: sessionId,
          new_message: { role: "user", parts: [{ text }] },
          streaming: false,
        }),
      });
      if (!r.ok) {
        let detail = t.error;
        try { detail = (await r.json()).detail || detail; } catch { /* sin json */ }
        throw new Error(detail);
      }

      const reader = r.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      let answered = false;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const chunks = buf.split("\n\n");
        buf = chunks.pop();
        for (const chunk of chunks) {
          const line = chunk.split("\n").find((l) => l.startsWith("data:"));
          if (!line) continue;
          let ev;
          try { ev = JSON.parse(line.slice(5)); } catch { continue; }
          if (ev.error) throw new Error(ev.error);
          const parts = ev.content?.parts || [];
          for (const p of parts) {
            const call = p.functionCall || p.function_call;
            if (call) {
              if (!traceBox.isConnected) chat.insertBefore(traceBox, status);
              addTrace(traceBox, call.name === "transfer_to_agent"
                ? `${t.transfer} ${AGENT_LABEL[call.args?.agent_name] || call.args?.agent_name}`
                : `${t.tool}: ${call.name}`);
            }
          }
          const textOut = parts.filter((p) => p.text && !p.thought).map((p) => p.text).join("");
          if (textOut && !ev.partial) {
            addMsg("bot", md(textOut), ev.author);
            answered = true;
          }
        }
      }
      if (!answered) throw new Error(t.error);
    } catch (err) {
      addMsg("bot error", esc(err.message || I18N[lang].error));
    } finally {
      status.remove();
      send.disabled = false;
      input.focus();
    }
  }

  function autosize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
  }

  // ---------- eventos ----------
  form.addEventListener("submit", (e) => { e.preventDefault(); ask(input.value); });
  input.addEventListener("input", autosize);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
  });
  $("#lang").addEventListener("click", () => {
    lang = lang === "es" ? "en" : "es";
    store.set("pp_lang", lang);
    applyLang();
  });
  $("#reset").addEventListener("click", () => location.reload());

  applyLang();
})();