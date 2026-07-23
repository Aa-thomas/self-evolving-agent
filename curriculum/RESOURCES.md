# Harness Engineering Resources

## Knowledge

- [Local curriculum: Harness Engineering Curriculum](./Harness%20Engineering%20curriculum%20-%20rewritten.md)
  Primary learning plan for this workspace. Use for project scope, stop conditions, must-not-build lists, and evidence requirements.
- [OpenAI docs: Function calling](https://platform.openai.com/docs/guides/function-calling)
  Use for the core tool-calling flow: model emits a tool call, application code executes it, then returns tool output to the model.
- [Python docs: Classes](https://docs.python.org/3/tutorial/classes.html)
  Use for class syntax, instance attributes, `__init__`, and method calls such as `model.complete(messages)`.
- [Python docs: typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
  Use for expressing "any object with a `.complete(messages) -> str` method" without forcing inheritance.
- [OpenAI docs: Agents SDK](https://platform.openai.com/docs/guides/agents)
  Use later for framework anatomy: where an SDK places agents, tools, state, guardrails, and traces.
- [Anthropic engineering: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
  Use for the principle of starting with the simplest viable workflow and adding agentic complexity only when the task needs it.
- [OpenAI docs: Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
  Use for the objective → dataset → metric → comparison workflow, task-specific eval design, and the distinction between interpretable case evidence and a score alone.

## Wisdom (Communities)

- [OpenAI Developer Community](https://community.openai.com/)
  Use for practical API/tool-calling questions once a small reproducible example exists.
- [Latent Space Discord](https://www.latent.space/p/discord)
  Use for applied AI engineering discussion and feedback on agent/eval design.

## Gaps

- Add one high-quality source focused specifically on versioned causal trace schemas and replay design.
