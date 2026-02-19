# transctl

> A pragmatic localization CLI ⚙️

`transctl` is a command-line tool for managing application translation workflows. It scans source files, extracts translatable content, translates it using a configured machine translation provider, and writes translated output files according to your project structure.

The tool maintains a local manifest and translation memory to avoid unnecessary retranslations across runs.

---

## Installation

Requires **Python ≥ 3.11**.

Install from PyPI:

```bash
pip install transctl
```

---

## Quick Start

Initialize a configuration file:

```bash
transctl init
```

Run the translation workflow:

```bash
transctl run
```

That’s the minimal happy path.

Use:

```bash
transctl --help
```

to explore additional commands.

---

## What It Does

`transctl`:

- Scans configured resource directories
- Extracts translatable content from files
- Translates content into one or more target locales
- Writes translated output files (never overwrites the source file)
- Skips unchanged files using a generated `manifest.json`
- Maintains a local SQLite-based translation memory
- Supports optional glossary injection
- Supports placeholder protection using `{{placeholder}}` syntax

---

## Avoiding Unnecessary Retranslations

Two mechanisms are used:

### 1. Translation Manifest (`manifest.json`)

After each run, a `manifest.json` file is generated automatically.  
It tracks file state to skip unchanged files in subsequent runs.

If the manifest is deleted or purged, files may be reprocessed.

---

### 2. Local Translation Memory (SQLite)

A local SQLite database stores translated segments to prevent repeated translation of identical content across runs.

- Automatically created and maintained
- Oldest entries may be pruned when the file grows too large
- Can be purged manually via `transctl purge`

If deleted, memory will rebuild over time.

---

## Configuration

The `.transctl.toml` file is required for operation.

If `transctl init` is executed and a configuration file already exists, no changes are made.

---

### Example Configuration

```toml
[locale]
source = "en"
targets = [
    "fr",
]

[engine]
provider = "deepl"

[resources.html]
dirs = [
    { path = "templates/*", layout = "along-sided" }
]

[resources.json]
dirs = [
    { path = "locales/[source].*.json"}
]
```

---

### Locale

```toml
[locale]
source = "en"
targets = ["fr"]
```

- `source` — source language  
- `targets` — one or more target languages  

---

### Engine

```toml
[engine]
provider = "deepl"
```

Supported providers:

- `deepl`
- `azure`

Engine-specific parameters can be provided interactively or via CLI flags.

**Note**: The `auth_key` of all engines must be provided as an environment variable.


#### DeepL

Required parameters: None

Example (non-interactive):

```bash
transctl init -y \
  -e deepl
```


#### Azure

Required parameters:

- `region` — Azure resource region

Example (non-interactive):

```bash
transctl init -y \
  -e azure \
  --param region=$AZURE_REGION
```

---

### Resources

Resources define what files should be translated.

Currently supported:

- HTML
- JSON

Example:

```toml
[resources.json]
dirs = [
    { path = "locales/*", layout = "along-sided" },
]
```

---

### Layout Behavior

`layout` determines where translated files are written.

Allowed values:

- `along-sided`
- `by-language`

If omitted, the default behavior is equivalent to `along-sided`.
Note that `layout=""` is not valid and will result in an error.

#### along-sided

If the original file is:

```
i18n.json
```

The translated file becomes:

```
fr_i18n.json
```

---

#### by-language

Keeps the original filename but creates a language directory:

```
locales/en/i18n.json
→
locales/fr/i18n.json
```

---

## Placeholder Protection

To prevent specific content from being translated, wrap it in:

```
{{placeholder}}
```

Anything inside `{{}}` is preserved.

---

## Glossary Support

A glossary file can be provided as a simple JSON key-value mapping.

Example:

```json
{
  "Key": "Value"
}
```

