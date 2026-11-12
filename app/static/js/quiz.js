(() => {
  "use strict";

  const timer = document.querySelector("#quiz-timer");
  const answerForm = document.querySelector("[data-answer-form]");
  const finalSubmit = document.querySelector("#final-submit");
  if (!timer || !answerForm || !finalSubmit) return;

  const status = document.querySelector("#save-status");
  let seconds = Number(timer.dataset.seconds);
  let saving = Promise.resolve();
  let submitted = false;

  const formatTime = (value) => {
    const mins = Math.floor(value / 60).toString().padStart(2, "0");
    const secs = (value % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
  };

  const sendSubmit = async () => {
    if (submitted) return;
    submitted = true;
    await saving;
    finalSubmit.requestSubmit();
  };

  timer.querySelector("strong").textContent = formatTime(seconds);
  const interval = window.setInterval(() => {
    seconds = Math.max(0, seconds - 1);
    timer.querySelector("strong").textContent = formatTime(seconds);
    if (seconds <= 60) timer.classList.add("timer-warning");
    if (seconds === 0) {
      window.clearInterval(interval);
      sendSubmit();
    }
  }, 1000);

  answerForm.addEventListener("change", (event) => {
    if (event.target.name !== "option_key") return;
    answerForm.querySelectorAll(".answer-option").forEach((label) => {
      label.classList.toggle("selected", label.contains(event.target));
    });
    status.textContent = "Saving…";
    status.dataset.error = "false";
    const formData = new FormData(answerForm);
    saving = saving.then(() => fetch(answerForm.action, {
      method: "POST",
      body: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    })).then(async (response) => {
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Your answer could not be saved.");
      status.textContent = "Answer saved.";
      status.dataset.error = "false";
    }).catch((error) => {
      status.textContent = error.message;
      status.dataset.error = "true";
    });
  });

  document.querySelectorAll('a[href^="/attempts/"]').forEach((link) => {
    link.addEventListener("click", async (event) => {
      event.preventDefault();
      await saving;
      window.location.assign(link.href);
    });
  });

  document.querySelector("[data-submit-attempt]")?.addEventListener("click", () => {
    if (window.confirm("Submit your answers now? You cannot change them after submission.")) {
      sendSubmit();
    }
  });

  finalSubmit.addEventListener("submit", () => window.clearInterval(interval));
})();
