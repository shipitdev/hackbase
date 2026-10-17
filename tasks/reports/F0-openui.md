# Worker report: F0 — OpenUI compatibility spike

**Worker/model/effort:** GPT-6 Luna / medium (explicit assignment)
**Status:** blocked
**Interface revision:** P0 in `docs/05-frontend-openui.md`

## Delivered

Created `frontend/package.json` with only the approved React/OpenUI/Zod/tsx dependencies as a provisional manifest. No schema, generated prompt, parser check or renderer proof was added because dependencies could not be confirmed locally.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| OpenUI official API reference review | pass | `createParser(schema, rootName)` returns a root tree, unresolved/orphaned/incomplete/errors, query/mutation statements and state declarations; enough surface exists to enforce the planned static-tree restrictions. `defineComponent`, `createLibrary`, `toJSONSchema`, `prompt` and `Renderer` are documented. |
| `cd frontend && npm install --save-exact` | blocked / status unavailable | The single permitted install attempt yielded no output or exit status within the tool's 30-second window. No `package-lock.json` or `node_modules` appeared afterward. The tool did not expose a resumable command session, so the package/network error cannot be stated more precisely. |
| `npm run check:openui` | not run | Dependencies and the lockfile are absent. |

## Limits and decisions needed

No OpenUI package versions or built-in widget exports were verified from an installed package. No compilation, parser assertions, SSR rendering, or proof of rejecting malformed/dynamic programs is claimed. Retry the install in an environment that can return a completed npm result, then finish P0 against the resolved versions. Official API references reviewed: `https://www.openui.com/docs/api-reference/react-lang`, `https://www.openui.com/docs/openui-lang/defining-components`, `https://www.openui.com/docs/openui-lang/syntax`, and `https://www.openui.com/docs/openui-lang/renderer`.

## Handoff

Only `frontend/package.json` was changed. No full frontend or backend contract changes were made. Sol confirmed the npm blocker with a bounded metadata request: getaddrinfo ENOTFOUND registry.npmjs.org. Sol removed the check:openui command because its script does not exist yet. Status remains blocked: no package versions, parser execution or rendered output verified.
