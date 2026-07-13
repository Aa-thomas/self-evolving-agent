class AgentTraceLab {
  constructor(root) {
    this.root = root;
    this.mode = root.dataset.mode || "predict";
    this.scenarioIndex = 0;
    this.stepIndex = 0;
    this.scenarios = [];
  }

  async start() {
    try {
      const response = await fetch("../traces/agent-loop-scenarios.json");
      if (!response.ok) throw new Error("Trace scenarios unavailable");
      this.scenarios = (await response.json()).scenarios;
      this.render();
    } catch {
      this.root.innerHTML = '<p class="trace-lab-error">The interactive trace is unavailable. Use the static walkthrough below.</p>';
    }
  }

  render() {
    const scenario = this.scenarios[this.scenarioIndex];
    const step = scenario.steps[this.stepIndex];
    const modePrompt = this.mode === "trace"
      ? "Use the visible trace fields to diagnose the next decision."
      : this.mode === "eval"
        ? "Decide whether this trajectory preserves the harness contract."
        : "Predict before revealing the harness transition.";
    this.root.innerHTML = `
      <div class="trace-lab-header">
        <div><p class="trace-lab-kicker">Trace Lab · ${this.scenarioIndex + 1} of ${this.scenarios.length}</p><h3>${this.escape(scenario.title)}</h3></div>
        <select data-scenario aria-label="Choose trace scenario">
          ${this.scenarios.map((item, index) => `<option value="${index}" ${index === this.scenarioIndex ? "selected" : ""}>${this.escape(item.title)}</option>`).join("")}
        </select>
      </div>
      <p>${modePrompt}</p>
      <ol class="trace-timeline" aria-label="Agent trace timeline">
        ${scenario.steps.map((item, index) => `<li class="${index === this.stepIndex ? "current" : index < this.stepIndex ? "complete" : "pending"}"><span>${index + 1}</span>${this.escape(index <= this.stepIndex ? item.label : "Hidden next state")}</li>`).join("")}
      </ol>
      <div class="trace-state"><p>${this.escape(step.stage.replaceAll("_", " "))}</p><code>${this.escape(step.detail)}</code></div>
      <fieldset><legend>${this.escape(step.question)}</legend>
        ${step.choices.map((choice, index) => `<label><input type="radio" name="trace-choice-${this.scenarioIndex}-${this.stepIndex}" value="${index}"> ${this.escape(choice)}</label>`).join("")}
      </fieldset>
      <div class="trace-lab-actions"><button type="button" data-check>Check prediction</button><button type="button" data-next disabled>${this.stepIndex === scenario.steps.length - 1 ? "Next scenario" : "Next transition"}</button></div>
      <p class="trace-feedback" data-feedback aria-live="polite"></p>
      <p class="trace-source">Grounded in <code>${this.escape(scenario.source)}</code></p>
      <details class="trace-static"><summary>Static scenario summary</summary><ol>${scenario.steps.map((item) => `<li><strong>${this.escape(item.label)}</strong> — ${this.escape(item.explanation)}</li>`).join("")}</ol></details>`;
    this.root.querySelector("[data-scenario]").addEventListener("change", (event) => {
      this.scenarioIndex = Number(event.target.value);
      this.stepIndex = 0;
      this.render();
    });
    this.root.querySelector("[data-check]").addEventListener("click", () => this.check(step));
    this.root.querySelector("[data-next]").addEventListener("click", () => this.next());
  }

  check(step) {
    const selected = this.root.querySelector('input[type="radio"]:checked');
    const feedback = this.root.querySelector("[data-feedback]");
    if (!selected) {
      feedback.textContent = "Choose a transition before checking.";
      return;
    }
    const passed = Number(selected.value) === step.answer;
    feedback.textContent = `${passed ? "Correct. " : "Revisit the harness boundary. "}${step.explanation}`;
    feedback.classList.toggle("good", passed);
    this.root.querySelector("[data-next]").disabled = !passed;
    document.dispatchEvent(new CustomEvent("learning:practice-attempt", {
      detail: {
        passed,
        kind: "trace-lab",
        scenario: this.scenarios[this.scenarioIndex].id,
        step: this.stepIndex,
        selected: Number(selected.value),
        expected: step.answer,
      },
    }));
  }

  next() {
    const scenario = this.scenarios[this.scenarioIndex];
    if (this.stepIndex < scenario.steps.length - 1) this.stepIndex += 1;
    else {
      this.scenarioIndex = (this.scenarioIndex + 1) % this.scenarios.length;
      this.stepIndex = 0;
    }
    this.render();
  }

  escape(value) {
    const node = document.createElement("span");
    node.textContent = String(value);
    return node.innerHTML;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-agent-trace-lab]").forEach((root) => new AgentTraceLab(root).start());
});
