# Task 1 - Risposte dalla documentazione ufficiale di Claude Code

Data lettura: 2026-10-09. Le citazioni sono copiate alla lettera dal markdown grezzo delle pagine (non da riassunti).

Pagine lette:
- HOOKS: https://code.claude.com/docs/en/hooks
- DEPS: https://code.claude.com/docs/en/plugin-dependencies (i link interni della documentazione puntano a `/docs/en/plugins/dependencies`, stessa pagina)
- REF: https://code.claude.com/docs/en/plugins-reference (titolo "Plugin manifest reference")
- CLI: https://code.claude.com/docs/en/plugins/cli-reference (per `claude plugin validate` e `claude plugin tag`)
- TOOLS: https://code.claude.com/docs/en/tools-reference
- SDK: https://code.claude.com/docs/en/agent-sdk/typescript (solo per i nomi dei campi di NotebookEdit)

---

## D1 - dependencies di plugin.json

### D1.a Le `version` si risolvono sui tag git? Sì.
DEPS, "Declare a dependency with a version constraint", riga `version` della tabella:
> "A [semantic-version range](https://github.com/npm/node-semver#ranges) such as `~2.1.0`, `^2.0`, `>=1.4`, or `=2.1.0`. The dependency installs at the highest git tag that satisfies this range, so the dependency's maintainer must [tag releases](#tag-plugin-releases-for-version-resolution)."

DEPS, "Release a plugin that others depend on":
> "A constraint resolves against git tags on the repository that hosts the plugin."

Limite per sorgenti non git (DEPS, "Constrain a dependency that has a non-git source"):
> "Tag-based resolution applies only to git-backed sources. For a dependency with an `npm`, `archive`, or `command` [plugin source](/docs/en/plugins/marketplace-reference#plugin-sources), the constraint doesn't control which version is fetched. It's still checked when the plugin loads, and the dependent plugin is disabled if the installed version doesn't satisfy it."

Pre-release (DEPS):
> "A range doesn't match pre-release versions such as `2.0.0-beta.1` unless you opt in with a pre-release suffix such as `^2.0.0-0`."

### D1.b Forma del tag: `<plugin-name>--v<version>` (quindi `superpowers--v6.4.1`, NON `v6.4.1`)
DEPS, "Create a release tag":
> "Tag each release as `<plugin-name>--v<version>`, where `<version>` matches the `version` field in that commit's `plugin.json`. The plugin-name prefix lets one marketplace repository host several plugins with independent version histories."

DEPS, "How a constraint resolves against tags":
> "the dependency installs from the highest `secrets-vault--v` tag that satisfies `~2.1.0` on the repository that hosts `secrets-vault`."

Un tag nudo `v6.4.1`: la documentazione non lo dice (il prefisso `<plugin-name>--v` è l'unica forma documentata).

Quale repository va taggato (DEPS):
> "**`github`, `url`, or `git-subdir` source**: the plugin's own repository, so the plugin's author creates the tags"
> "**Relative path such as `./plugins/secrets-vault`**: the marketplace repository, so the marketplace maintainer creates the tags"

Comando di tag (DEPS): `claude plugin tag --push`.
> "The command builds the tag name from the plugin's manifest."
Verifiche del comando (DEPS): "Validates the plugin", "Checks that `plugin.json` and the marketplace entry agree on the version, when the plugin directory is inside a marketplace checkout", "Requires a clean working tree under the plugin directory", "Refuses if the tag already exists".
Tag manuale ammesso (DEPS), alla sola condizione di tenere allineate le versioni:
> "You can also run `git tag secrets-vault--v2.1.0` directly, as long as you keep the `version` in `plugin.json` and in the marketplace entry in sync yourself."

Se nessun tag soddisfa l'intervallo (DEPS):
> "**Plugin with its own repository**: the install fails with a message containing `Dependency "secrets-vault@your-marketplace" has no git tag satisfying`."
> "**Plugin referenced by a relative path**: the install uses the marketplace's current copy instead, and the constraint is checked when the plugin loads. If that copy is outside the range, the dependent plugin stays disabled and `claude plugin list` shows `Requires "secrets-vault@your-marketplace" ~2.1.0, installed 3.0.0`."

### D1.c Dipendenza da un altro marketplace: serve `allowCrossMarketplaceDependenciesOn`? Sì (nome esatto confermato).
DEPS, "Depend on a plugin from another marketplace":
> "By default, Claude Code doesn't install a dependency from a different marketplace than the declaring plugin's own, unless the user already has that dependency installed and enabled at the same scope."
> "To allow the install, add the target marketplace's name to `allowCrossMarketplaceDependenciesOn` in the root marketplace's `marketplace.json`. The root marketplace is the one that hosts the plugin the user is installing. Only the root marketplace's allowlist applies."
> "If `allowCrossMarketplaceDependenciesOn` is missing or doesn't include the target marketplace, Claude Code doesn't install the dependency. [...] When it's declared in `plugin.json`, the install completes without the dependency and your plugin then fails to load."
> "The allowlist check doesn't apply to a dependency that is already enabled."

Esempio della pagina: `"allowCrossMarketplaceDependenciesOn": ["your-shared-marketplace"]` come chiave di primo livello di `marketplace.json`, accanto a `name` e `owner`.

### D1.d Comando che valida plugin.json senza installare: `claude plugin validate`
REF, "Validate the manifest":
> "`claude plugin validate` is the authoritative check for a manifest. Run it from your shell against the plugin directory:"
> `claude plugin validate ./my-plugin`

CLI, "plugin validate":
> "Validate a plugin manifest, a marketplace manifest, or the skills, agents, and commands in a directory, and exit with a code a CI job can act on."
Opzioni: `--strict` ("Treat warnings as errors, so unrecognized fields and missing metadata that the runtime tolerates fail the run") e `--json` ("Output the validation report as one JSON object with the same exit codes. Requires Claude Code v2.1.259 or later"). Esiste anche `/plugin validate <path>` in sessione.

Esiti (REF): "`Validation passed`", "`Validation passed with warnings`", "`Validation failed`". Campo top-level sconosciuto: "the field is stripped and the plugin loads. `claude plugin validate` reports each unrecognized top-level field as a warning".
Se `validate` controlli anche che le dipendenze siano risolvibili o presenti: la documentazione non lo dice.

### D1.e Forma esatta di una voce di `dependencies`
REF, tabella Fields: "`dependencies` | Array of strings or objects | Plugins that must be enabled for this one to work"; sezione `dependencies`:
> "Each entry is `"name"`, `"name@marketplace"`, or `{ "name": "...", "marketplace": "...", "version": "..." }`. Bare names resolve against this plugin's own marketplace."

DEPS, tabella dei campi dell'oggetto ("each a string"):
> `name`: "The dependency's plugin name, as it appears in its marketplace entry. Claude Code looks it up in the same marketplace as the declaring plugin unless you set `marketplace`. Required."
> `version`: (citazione in D1.a)
> `marketplace`: "A different marketplace to resolve `name` in. An allowlist controls cross-marketplace dependencies [...]"

Esempio ufficiale (DEPS):
    "dependencies": [
      "audit-logger",
      { "name": "secrets-vault", "version": "~2.1.0" }
    ]
Esempio cross-marketplace (DEPS, nella voce di marketplace.json): `{ "name": "audit-logger", "marketplace": "your-shared-marketplace" }`.

Altre frasi utili:
- "An entry can be a string: the plugin name alone [...] or `"name@marketplace"` to resolve it in another marketplace. With a bare string, your plugin depends on whatever version that plugin's marketplace provides."
- Sviluppo locale: "`claude --plugin-dir ./my-dependency --plugin-dir ./my-plugin`" e "a [version constraint] isn't checked against a local copy."
- Più vincoli sulla stessa dipendenza: "the dependency resolves to the highest version that satisfies all of their ranges"; se incompatibili: "Installing plugin B fails with a `has conflicting version requirements` message."
- Le dipendenze possono stare anche nella voce di marketplace (`plugins[].dependencies`), non solo in plugin.json.

---

## D2 - Hook: additionalContext, exit 2, systemMessage

### D2.a Eventi per cui `hookSpecificOutput.additionalContext` entra nel contesto del modello
HOOKS, "Add context for Claude":
> "The `additionalContext` field passes a string from your hook into Claude's context window. Claude Code wraps the string in a [system reminder](/docs/en/glossary#system-reminder) and inserts it into the conversation at the point where the hook fired."
> "Return `additionalContext` inside `hookSpecificOutput` alongside the event name"
> "Where the reminder appears depends on the event:"
> "* SessionStart and SubagentStart: at the start of the conversation, before the first prompt"
> "* UserPromptSubmit and UserPromptExpansion: alongside the submitted prompt"
> "* PreToolUse, PostToolUse, PostToolUseFailure, and PostToolBatch: next to the tool result"
> "* Stop and SubagentStop: at the end of the turn. The conversation continues so Claude can act on the feedback."
> "* PostModelSwitch: with the next request after the switch."

Risposta per gli eventi chiesti: PreToolUse sì, PostToolUse sì, SessionStart sì, SubagentStart sì, UserPromptExpansion sì, UserPromptSubmit sì (in più: PostToolUseFailure, PostToolBatch, Stop, SubagentStop, PostModelSwitch).
Conferme per evento:
- PreToolUse: "`additionalContext` | String added to Claude's context alongside the tool result. Ignored when `permissionDecision` is `"defer"`."
- SubagentStart: "String added to the subagent's context at the start of its conversation, before its first prompt." (contesto del subagente, non del genitore)
- SessionStart: "String added to Claude's context at the start of the conversation, before the first prompt."
- Eccezioni (non entra): Setup ("On every exit code, Claude Code discards a Setup hook's [JSON output fields](#json-output), such as `systemMessage`, `continue`, and `hookSpecificOutput.additionalContext`"); un UserPromptSubmit in timeout ("its output, including any `additionalContext`, is discarded").
- Limite: "A hook's `additionalContext`, `systemMessage`, and `initialUserMessage` strings, and its plain stdout, are capped at 10,000 characters"; oltre il limite "Claude Code writes the text to a file in the session directory and passes Claude the file path with a preview of up to the first 2,000 characters instead."
- Più hook: "When several hooks return `additionalContext` for the same event, Claude receives all of the values."

### D2.b SubagentStop, uscita 2
HOOKS, tabella "Exit code 2 behavior per event": "`SubagentStop` | Yes | Prevents the subagent from stopping".
Sezione SubagentStop:
> "Returning `decision: "block"` with a `reason` keeps the subagent running and delivers `reason` to the subagent as its next instruction. A hook that blocks by exiting 2 delivers its stderr message the same way."
Quindi sì: impedisce la chiusura e lo stderr arriva al subagente.

### D2.c PostToolUse, uscita 2
Tabella: "`PostToolUse` | No | Shows stderr to Claude; the tool already ran". Anche:
> "To surface a warning to Claude from a `PostToolUse` or `PostToolUseFailure` hook, exit 2 instead so [Claude sees the stderr](#exit-code-2-behavior-per-event) even though the tool already ran."
Sì, stderr mostrato al modello (ma non blocca).

### D2.d PreToolUse, uscita 2
Tabella: "`PreToolUse` | Yes | Blocks the tool call". Sezione PreToolUse decision control:
> "A hook that blocks by exiting 2 routes the same way as `"deny"`: Claude sees the stderr message as the denial reason."
Sì, blocca e il modello vede stderr. Sezione "Exit code 2": "Exit 2's block is the one outcome JSON can't override." E: "Without valid JSON on stdout, Claude Code treats exit code 1 as a non-blocking error and proceeds with the action" (per imporre una policy serve `exit 2`).
Per contrasto, uscita 0 con stderr: "Stderr from a hook that exits 0 goes to the debug log only, never the transcript, and Claude never sees it."

### D2.e `systemMessage`
HOOKS, tabella "JSON output":
> "`systemMessage` | none | Warning message shown to the user. In [Agent SDK](/docs/en/agent-sdk/overview) and [`--output-format stream-json`](/docs/en/headless) output, it can arrive as an [`SDKInformationalMessage`](/docs/en/agent-sdk/typescript#sdkinformationalmessage)"
> "To surface a message to the user on any platform, return [`systemMessage`](#json-output) in JSON output. Some events discard it or deliver it elsewhere, and each [event's section](#hook-events) says so."
Quindi è per l'utente, NON per il modello (per il modello usare `additionalContext`). Eventi che lo scartano: Setup, InstructionsLoaded, MessageDisplay, Notification, ConfigChange. Per hook in background:
> "Claude Code delivers the `additionalContext` and `systemMessage` fields from the hook's JSON response to Claude on the next conversation turn. Unlike a synchronous hook's `systemMessage`, neither field is shown to you."

---

## D3 - Strumenti MultiEdit / NotebookEdit e campi di tool_input

### D3.a MultiEdit
La documentazione non lo dice: il nome `MultiEdit` non compare né nella pagina hooks, né nella tabella strumenti di TOOLS, né nel riferimento Agent SDK TypeScript (ricerca testuale su tutte e tre senza risultati). Non è nell'elenco degli strumenti attuali; tenerlo in un matcher non fa danni, ma non è documentato.

### D3.b NotebookEdit: esiste
TOOLS, tabella strumenti: "`NotebookEdit` | Modifies Jupyter notebook cells. See [NotebookEdit tool behavior](#notebookedit-tool-behavior) | Yes" (terza colonna: richiede permesso).
HOOKS, sui matcher regex: "`Edit.*` matches both `Edit` and `NotebookEdit`; wrap the pattern in `^` and `$`, as in `^Edit$`, when you need a whole-string match."
TOOLS: "Permission rules use the `Edit(...)` path format. A rule like `Edit(notebooks/**)` covers NotebookEdit calls on files in that directory."

Campi di `tool_input` di NotebookEdit: NON documentati nella pagina hooks (che elenca Bash, Write, Edit, Read, ecc.). Sono nel riferimento Agent SDK TypeScript, https://code.claude.com/docs/en/agent-sdk/typescript, sezione NotebookEdit:
    type NotebookEditInput = {
      notebook_path: string;
      cell_id?: string;
      new_source: string;
      cell_type?: "code" | "markdown";
      edit_mode?: "replace" | "insert" | "delete";
    };
Quindi il campo è `notebook_path`, non `file_path`. Che l'input arrivato all'hook abbia esattamente questa forma, la pagina hooks non lo dice (è la forma dell'input dello strumento nell'SDK). La garanzia di percorso assoluto vale solo per tre strumenti, HOOKS: "For the file tools `Write`, `Edit`, and `Read`, `tool_input.file_path` is always absolute" (NotebookEdit non è citato).

### D3.c `tool_input` di Write ed Edit (HOOKS, "PreToolUse input")
Write ("Creates or overwrites a file."):
- `file_path` | string | "Absolute path to the file to write"
- `content` | string | "Content to write to the file"

Edit ("Replaces a string in an existing file."):
- `file_path` | string | "Absolute path to the file to edit"
- `old_string` | string | "Text to find and replace"
- `new_string` | string | "Replacement text"
- `replace_all` | boolean (esempio `false`) | "Whether to replace all occurrences"

Anche: "Claude Code expands `~` and relative paths before hooks run, so a hook that matches on paths can't be bypassed via `~` or a relative spelling of the same path". Su Windows il percorso arriva con backslash: "A comparison written with forward slashes, such as a `/src/` check, never matches a backslash path".

---

## Note
- Il fetch di `/docs/en/plugin-dependencies` funziona; la REF collega la stessa pagina come `/docs/en/plugins/dependencies` (non verificato se quest'ultimo URL risponde direttamente).
- Tutto il resto non citato sopra: la documentazione non lo dice.
