# Optional Claude adapter guidance

Read this guide only for requested Claude setup or adapter maintenance. Ordinary
Codex development follows the shared global contract and the skill repository's
README. This guide owns provider-specific explanations; shared instructions do
not need to route through a Claude setup workspace.

## Scope and ownership

The supported local surface is Claude Desktop local Code. Chat, Cowork, cloud,
and account-synced skills have separate loading and distribution rules. Do not
claim they are configured by a local adapter. Application installation and
sign-in remain user-operated unless explicitly authorized.

| Asset | Source of truth | Claude adapter |
| --- | --- | --- |
| Shared behavior | Existing global AGENTS contract | Import in the user-level CLAUDE file |
| Maintained skills and their private records | `~/.agents/skills` | Managed links under `~/.claude/skills` |
| Invocation policy | Each skill's `agents/openai.yaml` | Derived `skillOverrides` |
| Product contracts | Repository README and relevant durable docs/instructions | Follow loaded instructions and task-relevant references |
| Runtime capabilities | Current host tool inventory | Claude-owned connections and permissions |
| Model and effort | Current user selection and execution settings | Independent client selection |

Keep credentials, permissions, automatic memories, histories, app-owned plugins,
and provider caches with their owner. Sharing instructions does not grant access
to another client's runtime or private records. Do not copy personal principles
into provider memory or publish local setup records.

## Imports and discovery

Maintain a small Claude-owned adapter for its import syntax, permission controls,
available capabilities, and skill invocation syntax. Import shared rules rather
than maintaining a second copy. Respect already-loaded repository instructions;
read applicable instructions manually only when missing. Do not add product
repository CLAUDE files merely to copy shared guidance or replace retired AGENTS.

Keep one maintained skill checkout. Link its selected skill directories into the
Claude discovery root instead of copying them. Claude can report the link path
as the skill directory: edits through it affect the source. Record durable paths
using the maintained source root. Sibling resources and scripts work through
the link. Map an explicit `/skill-name` invocation to the shared `$skill-name`
intent; read the complete selected SKILL file.

Preserve `allow_implicit_invocation: false`. The existing host reconciler derives
`user-invocable-only` overrides from that policy. Do not create a second policy
list or make an explicit-only skill implicit to repair discovery.

Resolve the installed reconciler from the host's adapter configuration before
running it. Its implementation can remain host-local; this reference owns the
maintained procedure. Inspect only the needed configuration keys. On an existing
host, find the command in `~/.claude/settings.json` under
`hooks.SessionStart[].hooks[].command`. The installed `hook_reconcile.sh` calls
its sibling `link_skills.py`; both files are required setup assets outside this
skill checkout. Confirm the resolved paths and read the helper before use.
Use its existing dry-run and check modes first:

```sh
python3 <resolved-reconciler-path>
python3 <resolved-reconciler-path> --check
```

Use `--apply` only for an authorized change after reviewing the dry run. Preserve
unmanaged destinations, account-synced skill folders, unrelated overrides,
permissions, and hooks. Keep generated state generated. For an authorized source
relocation, use the helper's explicit previous-source option and conflict checks.
Serialize reconciliation with shared skill/record edits. Reuse the existing Xcode
skill sync; do not create another export pipeline for Claude.

A shared-skill clone alone does not restore this adapter. Preserve the external
setup directory and the relevant Claude-owned import/SessionStart settings in a
private host backup. For restoration on the same host, recover those files and
paths, inspect the dry run, and apply only the authorized reconciliation. On a
new host, first restore or deliberately install that helper pair, adapt the
configured command to its actual location, and review the generated links and
explicit-only overrides before starting a local Code session. Do not copy account
state or permissions as part of this procedure. A missing helper is a setup
blocker; do not substitute a second policy generator or claim restoration complete.
Static checks and isolated fixtures need no Claude login or paid model run.

An existing SessionStart reconciler is a Claude-owned adapter. Leave it alone
unless that hook is part of the requested change. The reconciler must preserve
keys it does not own and reject ambiguous policy parsing rather than relaxing
invocation restrictions. Test its implementation when changing it; document
maintenance alone does not require applying settings or firing the hook.

## Client-specific settings

Translate a setting only when its semantics match. Keep models and reasoning
levels independent between clients, and preserve current user choices. The
[runner reference](automatic-dispatch.md) owns dispatch defaults, actual model
flags, authentication preflight, and limits. Historical model IDs and usage
measurements remain records rather than current defaults.

Avoid broad user-scope directory grants derived from per-workspace trust. Use
the current host's approval controls; a one-off grant is not a permanent rule.
Do not mechanically copy sandbox options, deny rules, plugins, notification
settings, or complete MCP configuration between clients.

Existing local settings can suppress automatic commit/session attribution and
preserve skill descriptions in the discovery listing. Follow the current
repository commit style; attribution must not introduce an unintended trailer.
Keep any observed private-path restrictions in the client configuration. Do not
publish owner-specific paths or infer new permission rules from this guide.

For Apple work, use available native capabilities and shared device/session
ownership rules. Matching a connection's command/arguments alone does not prove
the agent is approved or can use the required capability. Preserve current
user-authorized client tools and verify actual access only when needed. Do not
change Xcode or Simulator state merely to validate a documentation edit.

## Verify the adapter when requested

With the user operating a signed-in Desktop local Code session in the intended
repository or worktree, confirm the imported contract, skill discovery,
explicit-only invocation, applicable repository instruction loading, and required
runtime capabilities. Restart a session when it retained old instructions.

Keep setup verification separate from a successful implementation/review round.
Read-back and synthetic tests do not prove app behavior, remaining account quota,
or a completed automatic handoff. Preserve dated setup snapshots and reports as
history; do not load them as general development requirements.

## Official references

- [Desktop shared configuration](https://code.claude.com/docs/en/desktop#shared-configuration)
- [Imports and repository instructions](https://code.claude.com/docs/en/memory#agentsmd)
- [Skills and invocation policies](https://code.claude.com/docs/en/skills)
- [MCP adapters](https://code.claude.com/docs/en/mcp)
