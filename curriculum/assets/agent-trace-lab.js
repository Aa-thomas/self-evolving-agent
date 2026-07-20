class AgentTraceLab {
  constructor(root) {
    this.root = root;
    this.mode = root.dataset.mode || "predict";
    this.scenarioIndex = 0;
    this.questionIndex = 0;
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
    const question = scenario.questions[this.questionIndex];
    const choices = this.shuffle(question.choices, `${scenario.id}:${question.id}`);
    this.root.innerHTML = `
      <div class="trace-lab-header"><div><p class="trace-lab-kicker">Trace Lab · ${this.scenarioIndex + 1} of ${this.scenarios.length}</p><h3>${this.escape(scenario.title)}</h3></div>
      <select data-scenario aria-label="Choose trace scenario">${this.scenarios.map((item, index) => `<option value="${index}" ${index === this.scenarioIndex ? "selected" : ""}>${this.escape(item.title)}</option>`).join("")}</select></div>
      <p>Inspect this causal artifact before committing a diagnosis.</p>
      <dl class="trace-artifact">
        <dt>Assistant output</dt><dd><code>${this.escape(scenario.assistant_output)}</code></dd>
        <dt>Parse result</dt><dd><code>${this.escape(JSON.stringify(scenario.parse_result))}</code></dd>
        <dt>Validation result</dt><dd><code>${this.escape(JSON.stringify(scenario.validation_result))}</code></dd>
        <dt>Protocol registry</dt><dd><code>${this.escape(scenario.protocol_registry.join(", "))}</code></dd>
        <dt>Runtime handlers</dt><dd><code>${this.escape(scenario.runtime_handlers.join(", ") || "none")}</code></dd>
        <dt>Harness decision</dt><dd><code>${this.escape(JSON.stringify(scenario.harness_decision))}</code></dd>
      </dl>
      <fieldset data-case-id="${this.escape(`${scenario.id}:${question.id}`)}" data-answer="${this.escape(question.answer)}"><legend>${this.escape(question.question)}</legend>
        ${choices.map((choice) => `<label><input type="radio" name="trace-choice" value="${this.escape(choice)}"> ${this.escape(choice)}</label>`).join("")}
        <label>Why? <textarea data-rationale placeholder="Name the evidence and responsible boundary."></textarea></label>
      </fieldset>
      <div class="trace-lab-actions"><button type="button" data-check>Commit diagnosis</button><button type="button" data-next disabled>${this.questionIndex === scenario.questions.length - 1 ? "Next scenario" : "Next question"}</button></div>
      <p class="trace-feedback" data-feedback aria-live="polite"></p>
      <p class="trace-source">Grounded in <code>${this.escape(scenario.source_test)}</code></p>`;
    this.root.querySelector("[data-scenario]").addEventListener("change", (event) => {
      this.scenarioIndex = Number(event.target.value);
      this.questionIndex = 0;
      this.render();
    });
    this.root.querySelector("[data-check]").addEventListener("click", () => this.check(scenario, question));
    this.root.querySelector("[data-next]").addEventListener("click", () => this.next());
  }

  check(scenario, question) {
    const selected = this.root.querySelector('input[type="radio"]:checked');
    const rationale = this.root.querySelector("[data-rationale]");
    const feedback = this.root.querySelector("[data-feedback]");
    if (!selected || !rationale.value.trim()) {
      feedback.textContent = "Choose a diagnosis and explain the evidence before committing.";
      return;
    }
    const passed = selected.value === question.answer;
    feedback.textContent = `${passed ? "Correct. " : "Revisit the first responsible boundary. "}${question.explanation}`;
    feedback.classList.toggle("good", passed);
    this.root.querySelector("[data-next]").disabled = false;
    document.dispatchEvent(new CustomEvent("learning:case-attempt", {
      detail: { kind: "case", case_id: `${scenario.id}:${question.id}`, selected: selected.value, expected: question.answer, rationale: rationale.value.trim(), passed },
    }));
  }

  next() {
    const scenario = this.scenarios[this.scenarioIndex];
    if (this.questionIndex < scenario.questions.length - 1) this.questionIndex += 1;
    else {
      this.scenarioIndex = (this.scenarioIndex + 1) % this.scenarios.length;
      this.questionIndex = 0;
    }
    this.render();
  }

  shuffle(choices, seed) {
    const result = [...choices];
    let state = [...seed].reduce((value, char) => value + char.charCodeAt(0), 1);
    for (let index = result.length - 1; index > 0; index -= 1) {
      state = (state * 1664525 + 1013904223) >>> 0;
      const swap = state % (index + 1);
      [result[index], result[swap]] = [result[swap], result[index]];
    }
    return result;
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
