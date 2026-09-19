# Bounded Apogee Incident Notes

These are historical routing clues, not permanent limitations or instructions
to patch dependencies. Recheck linked Issues and the installed executable.
Last checked: 2026-09-19; Issues 15 and 16 are closed, and published 1.3.0
completed verified screenshot replacement in an adopter.

## Asset Upload Response and Delayed Read-Back

[Apogee Issue 15](https://github.com/muhiro12/Apogee/issues/15) recorded two
observations with 1.2: an Apple upload URL lacked the assumed `Expires` query
parameter, and `COMPLETE` could appear before checksum read-back stabilized.
The published 1.3.0 path handles these cases; do not treat the old incident as
an outstanding blocker or apply a disposable dependency patch.

For a recurrence, retain private recovery records and report the installed
version and sanitized failure. Inspect completed writes before retrying.
Do not repeatedly reserve new images or weaken URL/checksum checks.

## Existing Images Without Exact Originals

[Apogee Issue 16](https://github.com/muhiro12/Apogee/issues/16) is implemented
in 1.3.0. Its explicit `--allow-unrecoverable-replacement` option permits
upload-first replacement when old and new images fit within the set capacity.
It also requires destructive confirmation and a fresh matching plan token.
New images must be COMPLETE with matching checksums before old images are deleted.

The recovery journal marks affected sets unrecoverable and does not fabricate a
restore layout. This protects new uploads before deletion but cannot restore
the previous composition. Follow the authorization guidance in
[screenshot preparation](screenshots.md); a processed Store reference image
is not an exact recovery original. Sets that exceed capacity still require
verified originals. Preserve the journal and inspect remote state after errors.

## Long-Running Upload Progress

[Apogee Issue 17](https://github.com/muhiro12/Apogee/issues/17) requests progress
reporting separate from final JSON. With 1.3.0, a redirected JSON result may stay
empty while a large upload is still running. Silence alone is not failure;
use bounded process waits and retain the existing recovery journal rather than
starting a competing apply. Recheck the issue before assuming this gap remains.
