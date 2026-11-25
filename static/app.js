const $ = (sel) => document.querySelector(sel);
const results = $("#results");
const savedBox = $("#saved");
const savedEmpty = $("#saved-empty");
const goBtn = $("#go");

// ---------- Saved jokes (browser ke localStorage mein) ----------
function loadSaved() {
  try { return JSON.parse(localStorage.getItem("saved-jokes") || "[]"); }
  catch { return []; }
}
function storeSaved(list) {
  try { localStorage.setItem("saved-jokes", JSON.stringify(list)); } catch { /* private mode */ }
}

function jokeCard(text) {
  const card = document.createElement("article");
  card.className = "joke";

  const p = document.createElement("p");
  p.textContent = text; // textContent = safe, HTML inject nahi hoga
  card.append(p);

  const acts = document.createElement("div");
  acts.className = "acts";

  const copy = document.createElement("button");
  copy.className = "act";
  copy.type = "button";
  copy.textContent = "Copy";
  copy.onclick = async () => {
    try { await navigator.clipboard.writeText(text); copy.textContent = "Copy ho gaya"; }
    catch { copy.textContent = "Copy nahi hua"; }
    setTimeout(() => (copy.textContent = "Copy"), 1500);
  };

  const wa = document.createElement("a");
  wa.className = "act";
  wa.target = "_blank";
  wa.rel = "noopener";
  wa.href = "https://wa.me/?text=" + encodeURIComponent(text);
  wa.textContent = "WhatsApp";

  const save = document.createElement("button");
  save.className = "act";
  save.type = "button";
  const refresh = () => {
    const isSaved = loadSaved().includes(text);
    save.textContent = isSaved ? "Saved" : "Save";
    save.classList.toggle("on", isSaved);
  };
  save.onclick = () => {
    let list = loadSaved();
    list = list.includes(text) ? list.filter((j) => j !== text) : [text, ...list];
    storeSaved(list);
    renderSaved();
    refresh();
  };
  refresh();

  acts.append(copy, wa, save);
  card.append(acts);
  return card;
}

function renderSaved() {
  const list = loadSaved();
  savedBox.replaceChildren(...list.map((t) => jokeCard(t)));
  savedEmpty.hidden = list.length > 0;
}

// ---------- Joke banana ----------
function message(cls, text) {
  const div = document.createElement("div");
  div.className = cls;
  div.textContent = text;
  return div;
}

async function makeJokes() {
  const body = {
    topic: $("#topic").value,
    language: document.querySelector("input[name=language]:checked").value,
    style: document.querySelector("input[name=style]:checked").value,
    count: 3,
  };

  goBtn.disabled = true;
  results.replaceChildren(message("loading", "Joke soch raha hoon"));

  try {
    const res = await fetch("/api/jokes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Kuch gadbad ho gayi.");

    const nodes = [];
    if (data.notice) nodes.push(message("notice", data.notice));
    data.jokes.forEach((j) => nodes.push(jokeCard(j)));
    results.replaceChildren(...nodes);
  } catch (err) {
    results.replaceChildren(message("error", err.message + " Internet check karke dobara Joke banao dabao."));
  } finally {
    goBtn.disabled = false;
  }
}

goBtn.addEventListener("click", makeJokes);
$("#topic").addEventListener("keydown", (e) => { if (e.key === "Enter") makeJokes(); });
renderSaved();
