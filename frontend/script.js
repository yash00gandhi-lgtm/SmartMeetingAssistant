// Frontend script — talks to FastAPI via fetch().
// Same-origin, so relative URLs work.

const API = "";
let currentMeeting = null;  // last processed meeting (for export)

// ---------- Tab switching ----------
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    panels.forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById("tab-" + tab.dataset.tab).classList.add("active");
    if (tab.dataset.tab === "list") loadMeetings();
  });
});

// ---------- DOM refs ----------
const titleInput   = document.getElementById("meetingTitle");
const notesText    = document.getElementById("notesText");
const pdfInput     = document.getElementById("pdfInput");
const processBtn   = document.getElementById("processBtn");
const processStatus= document.getElementById("processStatus");
const resultsCard  = document.getElementById("resultsCard");
const currentIdEl  = document.getElementById("currentMeetingId");
const rSummary     = document.getElementById("rSummary");
const rActions     = document.getElementById("rActions");
const rFollowUps   = document.getElementById("rFollowUps");
const rNextSteps   = document.getElementById("rNextSteps");
const exportBtn    = document.getElementById("exportBtn");
const searchInput  = document.getElementById("searchInput");
const searchBtn    = document.getElementById("searchBtn");
const searchResult = document.getElementById("searchResult");
const refreshBtn   = document.getElementById("refreshBtn");
const meetingsList = document.getElementById("meetingsList");

// Switch text/PDF mode
document.querySelectorAll('input[name="mode"]').forEach((r) => {
  r.addEventListener("change", () => {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    notesText.style.display = mode === "text" ? "block" : "none";
    pdfInput.style.display  = mode === "pdf"  ? "block" : "none";
  });
});

// ---------- Helpers ----------
function setStatus(el, text, isError = false) {
  el.textContent = text;
  const cls = el.classList.contains("status") ? "status" : "result";
  el.className = cls + (isError ? " error" : "");
}

// ---------- 1. Process meeting ----------
processBtn.addEventListener("click", async () => {
  const title = titleInput.value.trim();
  if (!title) return setStatus(processStatus, "Please add a title.", true);

  const mode = document.querySelector('input[name="mode"]:checked').value;

  const fd = new FormData();
  fd.append("title", title);

  if (mode === "text") {
    const text = notesText.value.trim();
    if (!text) return setStatus(processStatus, "Paste meeting notes first.", true);
    fd.append("notes_text", text);
  } else {
    const file = pdfInput.files[0];
    if (!file) return setStatus(processStatus, "Choose a PDF first.", true);
    fd.append("file", file);
  }

  setStatus(processStatus, "Processing... this can take 15-30 seconds.");
  processBtn.disabled = true;
  resultsCard.style.display = "none";

  try {
    const res = await fetch(API + "/process-meeting", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed");

    currentMeeting = data;
    currentIdEl.textContent = data.meeting_id;
    rSummary.textContent    = data.summary;
    rActions.textContent    = data.action_items;
    rFollowUps.textContent  = data.follow_ups;
    rNextSteps.textContent  = data.next_steps;
    resultsCard.style.display = "block";
    setStatus(processStatus, `✅ Processed ${data.notes_length} chars of notes.`);
  } catch (err) {
    setStatus(processStatus, "❌ " + err.message, true);
  } finally {
    processBtn.disabled = false;
  }
});

// ---------- 2. Export ----------
exportBtn.addEventListener("click", async () => {
  if (!currentMeeting) return;
  try {
    const res = await fetch(API + "/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        meeting_id: currentMeeting.meeting_id,
        title: currentMeeting.title,
        summary: currentMeeting.summary,
        action_items: currentMeeting.action_items,
        follow_ups: currentMeeting.follow_ups,
        next_steps: currentMeeting.next_steps,
      }),
    });
    if (!res.ok) throw new Error("Export failed");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentMeeting.title}_${currentMeeting.meeting_id.slice(0, 8)}.txt`;
    document.body.appendChild(a); a.click(); a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert("Export failed: " + err.message);
  }
});

// ---------- 3. Search ----------
async function runSearch() {
  const q = searchInput.value.trim();
  if (!q) return setStatus(searchResult, "Type a question first.", true);
  setStatus(searchResult, "Searching past meetings...");
  searchBtn.disabled = true;
  try {
    const res = await fetch(API + "/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Search failed");
    setStatus(searchResult, data.answer);
  } catch (err) {
    setStatus(searchResult, "❌ " + err.message, true);
  } finally {
    searchBtn.disabled = false;
  }
}
searchBtn.addEventListener("click", runSearch);
searchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") runSearch();
});

// ---------- 4. List meetings ----------
async function loadMeetings() {
  meetingsList.innerHTML = "Loading...";
  try {
    const res = await fetch(API + "/meetings");
    const data = await res.json();
    if (!data.meetings || data.meetings.length === 0) {
      meetingsList.innerHTML = "<p class='muted'>No meetings stored yet.</p>";
      return;
    }
    meetingsList.innerHTML = data.meetings.map((m) => `
      <div class="meeting-item">
        <div class="title">${m.title || "(no title)"}</div>
        <div class="meta">ID: <code>${m.meeting_id}</code> · ${m.date || ""}</div>
      </div>
    `).join("");
  } catch (err) {
    meetingsList.innerHTML = "<p class='muted'>Failed to load meetings.</p>";
  }
}
refreshBtn.addEventListener("click", loadMeetings);
