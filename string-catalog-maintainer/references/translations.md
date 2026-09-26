# Locale Repair and Translation

- Do not stop after `--seed-missing-locales`; seeding only copies source-locale structure and marks entries as `new`.
- Use `translation_tasks` as the required worklist for missing locales, `state != translated`, empty values, and source-copy translated values.
- Before finalizing translations, check the supplied terminology requirements, existing translations, and official localized feature names.
- Treat source-copy tasks for intentional proper nouns, product names, symbols, and acronyms as review-only and report them as intentionally unchanged when appropriate.
- Create a translation patch JSON with a top-level `translations` list. Each entry must include `catalog`, `key`, `locale`, `path`, and either `value` for `stringUnit` or `values` for `stringSet`.
- Validate first with `--translation-patch <patch.json>` and no `--apply-translations`.
- Apply only after validation passes: `--translation-patch <patch.json> --apply-translations`.
- Preserve placeholders exactly. The script rejects placeholder mismatches such as missing `%lld`, `%1$@`, `%@`, or `${applicationName}`.
