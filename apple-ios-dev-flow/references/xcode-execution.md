## Xcode Execution

1. Resolve needed capabilities by narrowly filtered tool names, then inspect only
   their schemas. Reuse confirmed schemas within the task; rediscover after a
   relevant failure or runtime change. Match the workspace to the repository.
   For Simulator runtime work, follow [device-session ownership](../../xcode-ui-smoke-auditor/references/device-session-ownership.md).
2. Before switching, capture the original scheme, destination, and active test
   plan when relevant. Use discovered eligible values. A scheme switch may
   change the destination; recheck before proceeding.
3. Keep stateful Xcode operations serial for the shared workspace and Simulator.
   Independent source analysis can run alongside them. Do not interrupt another
   task's build or session to obtain your own evidence.
4. Follow the active integration's lifecycle and generated device guidance.
   Inspect current screenshots, hierarchy, and logs for runtime claims. End
   interaction sessions and stop runs started only for verification.
5. Restore the scheme, its test plan if changed, then destination, and confirm
   restoration. Do not overwrite a later user selection; report any unresolved
   final state.

When a capability is absent or fails, record the observed gap and use a relevant
repository fallback or official Apple tool that covers the same evidence within
the user's authorization. Do not invent adapters, weaken approval controls, or
claim equivalent coverage from an unrelated screenshot. Request input only when
an actual missing decision or permission prevents the next necessary action.
