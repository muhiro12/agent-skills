# Device-session ownership

Use this for Simulator runtime work through the active Xcode MCP. Direct Preview
rendering and build-only verification do not need an interaction session. Resolve
only the needed action schemas; do not assume volatile action or parameter names.

## Assign a device to the work

- Use dedicated Simulators per app, with distinguishable app/device-family labels.
  Reuse the app's assigned UUID across tasks, captures, and resumption. Resolve
  an existing app-specific device before creating one; do not create devices per
  task, retry, or child agent. Serialize work for the same app instead of creating
  another device to work around its active session.
- Other apps use their own devices. For package runtime validation, use devices
  assigned to that package's example/test host. If validating through a real
  consumer app, use that app's assigned device and coordinate with its current
  owner; do not take over an unrelated app's device. Preview-only work needs no
  interaction session, but still serializes shared Xcode selection.
- Honor an explicitly requested device, runtime, or existing data state. A fresh
  Simulator cannot prove recovery of an existing store, account, or purchase.
  If that device is occupied, coordinate or wait; report the evidence gap rather
  than silently replacing the target or its data.
- Inspect available device types, runtimes, and scheme eligibility. Prefer MCP
  provisioning if available. If its inventory has no provisioning capability,
  use official Apple Simulator tooling only for the missing setup, then return
  to Xcode MCP for build, install/run, interaction, and evidence. Do not clone
  private app/account data, install runtimes, or erase devices as incidental setup.
- Keep the app-to-device UUID assignment, runtime, current session owner, and
  workspace in the private handoff or verification record. Carry the assignment
  across tasks and recheck it on resumption. A display name is a label, not proof
  of ownership or an unambiguous selector. Create only the device families required
  by the evidence; companion pairs belong to the same app.

## Open, use, and close the interaction session

1. Match the workspace and scheme. Record selection before changing it and choose
   an eligible destination. A destination-picker handle and a device UUID are
   different selectors: use the exact value required by each current schema.
2. Pass the assigned UUID explicitly to the interaction-start capability. Do not
   omit the selector or use a broad device name. Give every new start attempt a
   fresh human-readable identifier with a unique suffix; do not reuse a recently
   closed identifier. Keep the returned session key private and use that key for
   subsequent actions. Confirm the returned device UUID matches the assignment.
3. Reuse that active interaction session during a contiguous verification phase.
   Independent code work can proceed while MCP prepares the device. Follow current
   screenshots, hierarchy, and generated input guidance; do not replace necessary
   UI observation with stale coordinates or truncated evidence.
4. End only this task's session in cleanup, including after errors when a key was
   returned. Stop verification-only runs that this task owns. Do not keep an
   interaction session open across unrelated work merely to preserve continuity;
   retain the Simulator and task record for resumption instead.

Separate devices do not isolate the active scheme, test plan, or destination of a
shared Xcode workspace. Serialize changes and build/install actions on that shared
state. Use an independently addressed worktree workspace only when the integration
supports it. Restore this task's changed selection without overwriting a later
user or other owner's choice. A private task record is not a cross-process lock.

## Recover from a specific failure

- **Device already in use:** do not terminate an unknown session. Confirm the app
  assignment and active session owner. If this is another app's device, select
  this app's own device. If it is this app's device, wait for the current owner or
  an explicit handoff. Close a stale session only when this task owns it and no
  operation still uses it; do not create extra same-app devices to bypass the owner.
- **Identifier already used:** generate a new start identifier. If an earlier
  attempt may still be active, resolve its ownership before starting another.
- **Multiple devices match:** resolve the exact UUID from the eligible device
  inventory and pass it explicitly. Do not retry the same fuzzy selector.
- **Previous start failed or device unavailable:** retain the failure, resolve
  this task's partial session when possible, and check readiness/eligibility once.
  Retry after a relevant state change, with a fresh identifier. Do not restart
  shared services or repeatedly issue the same failing request.

For ongoing setup/build work use completion notifications or 30-60 second waits
within host/tool limits. UI transitions still follow the live tool's readiness
contract; do not add fixed sleeps to every tap. Inspect compact results first and
load detailed logs when a failure or decision requires them.

Retain the app's Simulator and data across tasks; do not automatically erase or
delete it. Shut down only an idle device whose current session this task owns,
when appropriate and no other operation needs it.
Report the actual device/runtime, evidence data state, and unresolved ownership
or cleanup problems without publishing private session keys.
