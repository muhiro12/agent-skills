# Diagnostic Scenarios

These are evaluation designs and candidate remedies, not reports of completed
experiments or Apple-confirmed bugs. Use synthetic inputs representing the
feature's requirements, record the actual configuration and result, and avoid
turning one application's product choices into universal requirements.

## Source omissions and rewritten fields

For source-faithful extraction, include ordered instructions, warnings, paired
labels/values, and ambiguous quantities. Compare acquired text, raw generated
fields, and post-processing separately. A fact missing from acquisition cannot
be recovered reliably by changing generation instructions.

If exact fields are required, compare prompt/schema changes with deterministic
extraction or validation against recognized source fields. Bind any correction
to the source revision; edited input may invalidate the match. A validator test
proves correction behavior, not improved raw model output. This method does not
validate the truth of the source or apply automatically to creative generation.
See [generation guidance](generation-and-state.md#prompts-and-guided-generation).

## Missing values and a lost one-period boundary

Build cases with absent targets/dates, ambiguous references, and a change limited
to one period. Specify reference time, time zone, unknown representations, and
start/end semantics. Score unsupported additions and missing boundaries even
when output satisfies the schema. Compare repeated runs and unseen examples.

A product can obtain a value through another input path when that fits its
requirements, but this bypass is not a model fix. Do not require manual selection
or confirmation in unrelated features. See [semantic evaluation](evaluation-and-debugging.md#semantic-evaluation).

## PCC availability without execution entitlement

Compare SDK availability, reported runtime capability, signed entitlements,
provisioning, and actual execution in the intended target. A command-line probe
may have different authorization from the app. Diagnose the first failing layer
without claiming that a capability result proves execution access, or that a
probe failure establishes unavailability in every target.

Follow [PCC access guidance](models-and-availability.md#private-cloud-compute).
Adding an entitlement string is not evidence of a grant. Do not manufacture
ungranted access or change the product's model merely to make a probe pass.

## Model errors hidden by a fallback parser

Inspect broad catch paths that return parsed or cached output after generation
fails. If a fallback is intended, preserve enough outcome information to tell
fallback recovery from model success. Exercise cancellation, unavailable-model,
and request-error paths separately. Verify that late results do not overwrite
newer input. A synthetic error tests the adapter path, not every live service
failure. See [session lifetime](generation-and-state.md#session-lifetime-and-cancellation).

## Whole-page input and context overflow

Use a synthetic document with relevant content plus increasing irrelevant text.
Compare source token counts, full request budget, and fresh versus accumulated
sessions. Reduce irrelevant material or partition meaningful sections, then
verify retained relationships and output fidelity. Do not claim this experiment
has succeeded until it runs in the target configuration.

Use the model's current capacity instead of a fixed token constant. A fresh
session cannot solve an individually oversized source. See [context recovery](context-and-language.md#reduce-or-partition-the-actual-source).

## Locale-based output language

Evaluate input language, explicit output-language instructions, app locale, and
structured output independently. Include a requested language different from the
device language and mixed-language input. Keep source identifiers unchanged
when the feature requires fidelity rather than translation.

Measure the actual output; language support and a small successful sample do
not guarantee instruction following. No blanket translation of Swift identifiers
is required. See [language guidance](context-and-language.md#output-language).
