# Learner-Facing HTML Lesson Standard

## Purpose

Every file in `lessons/` is a learner-facing HTML lesson, not a reference card or a thin wrapper around an exercise. It must build the engineering judgment needed for AI Engineer, Applied AI Engineer, and Forward Deployed Engineer work.

This standard applies to all new and materially rewritten lessons. It supplements `MISSION.md` and the general teaching skill.

## Required shape

Each lesson teaches one tightly scoped concept, but teaches it deeply enough to use outside the lesson. It must include:

1. **Mission and role framing** — state why the concept matters in a production-shaped AI system and connect it to a realistic engineering responsibility.
2. **Concrete system walkthrough** — use a running example, code path, message flow, trace, request, or other artifact from this curriculum. Do not teach only through definitions.
3. **Prediction before explanation** — ask the learner to predict behavior, identify an invariant, or choose an intervention before showing the answer.
4. **Failure case** — show at least one plausible bad input, failed trajectory, incident, or security/reliability problem. Explain where the harness or service must intervene and why.
5. **Evidence and observability** — identify the test, eval, trace, metric, log, or reproducible command that would establish confidence in the behavior.
6. **Engineering tradeoff** — name a real choice such as strictness versus recovery, latency versus validation, flexibility versus permissions, or product speed versus auditability. Explain the appropriate choice for the scenario.
7. **Meaningful practice with feedback** — require an answer that demonstrates reasoning, such as classifying an input, ordering a trajectory, diagnosing a trace, selecting a test, or explaining a design decision. Keyword-presence checks alone are not sufficient feedback.
8. **Transfer prompt** — end with a brief question that asks how the primitive would change in a different customer, data, or operational setting.

## Depth without sprawl

Keep one central concept per lesson and use progressive disclosure:

1. Establish the system context and the invariant.
2. Walk through the happy path.
3. Introduce a realistic failure.
4. Let the learner make and check a decision.
5. Connect the result to runnable evidence and the next lesson.

This is in-depth instruction without turning one page into an entire project. Supporting details belong in linked references, code artifacts, traces, or follow-on lessons.

## Role-oriented framing

The lesson should answer these questions plainly:

- What breaks for a user, customer, or operator if this primitive is wrong?
- How would an engineer detect and reproduce that failure?
- What evidence would be convincing in a design review, customer demo, or incident follow-up?
- What tradeoff does the engineer own?

Use the role connection that genuinely fits the lesson. Do not add generic career language where it does not clarify the engineering decision.

## Artifact integrity

Every linked code artifact, test, trace, eval, and command must exist and work before the lesson is published. A lesson must not promise a capability that the curriculum repository does not yet provide.

When the lesson teaches a contract or invariant, its practice and linked proof must test the same behavior. If the implementation changes, update the lesson in the same change.

Every lesson must also have an entry in `learning-flow.json`. The manifest is the machine-readable contract for prerequisites, implementation evidence, unlocks, and the appropriate teaching form.

## Micro-world decision gate

Use the smallest teaching form that exposes the concept. A quiz tests judgment, a playground tries isolated inputs, and a micro-world exposes an evolving system with hidden state and causal consequences.

A micro-world is eligible only when:

1. the goal is a mental model rather than fact recall;
2. important behavior is hidden, dynamic, spatial, or branching;
3. learner actions reveal meaningful cause and effect; and
4. the world is grounded in real code, traces, schemas, or tests.

Record the decision, score, rationale, scenario source, learner action, and static fallback in `learning-flow.json`. A full micro-world requires a score of at least six. Do not add one when an annotated example or small playground teaches the same thing.

## Author checklist

Before publishing, verify:

- The page has all eight required elements above.
- The learner must reason about behavior; they cannot pass by repeating vocabulary.
- Every internal link and runnable proof is valid.
- The lesson has a primary-source recommendation and links to relevant reference material.
- The page makes a tangible contribution to the primitive -> micro-system -> benchmarked harness progression.
- The learning-flow entry is valid, and any micro-world is justified and grounded in a real artifact.
- The lesson is readable as a standalone page, while still linking forward to the next skill.
