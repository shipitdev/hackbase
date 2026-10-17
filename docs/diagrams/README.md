# Saved design drawings

These drawings were rendered with the Excalidraw MCP during planning and saved locally for future orchestrator sessions. The `.excalidraw` files are the editable reference; SVG/PNG files are convenient previews. They describe a proposed system, not implemented behavior.

| Drawing | Editable file | Preview |
|---|---|---|
| Application system | [system-design.excalidraw](system-design.excalidraw) | [SVG](system-design.svg) · [PNG](system-design.png) |
| Sol/Luna build workflow | [build-orchestration.excalidraw](build-orchestration.excalidraw) | [SVG](build-orchestration.svg) · [PNG](build-orchestration.png) |
| Chat UI layout | [copilot-layout.excalidraw](copilot-layout.excalidraw) | [SVG](copilot-layout.svg) · [PNG](copilot-layout.png) |

Open an editable file in Excalidraw to pan, zoom and change it. For an orchestrator with image viewing, open the PNG for a quick look; read the matching design document for exact rules.

- [System explanation](../system-design.md)
- [Build orchestration](../orchestration.md)
- [UI behavior and states](../ui-layout.md)
- [Shared contracts](../contracts.md)

## Excalidraw MCP references

| Drawing | Last rendered checkpoint |
|---|---|
| System | `8ba004cfa5384a0fb3` |
| Build workflow | `62ef794758ee42c9b8` |
| Chat layout | `4e2ed7c376dd464184` |

Checkpoint IDs help identify the widgets in this session; local files are the durable reference. Future widget edits are not automatically synchronized into these files. If editing a live widget, first read its current state using an available widget-context tool so user edits are preserved; if that tool is unavailable, use the local file as the explicit source and create a fresh view. Save updated native files/previews and update this index when accepting a design change.

The native files contain standard Excalidraw elements, without MCP camera commands. SVG/PNG previews were generated from the same saved scene geometry and checked for text fitting. They are not screenshots of a running application.

## Implemented video reference

[Video architecture — editable Excalidraw](video-system.excalidraw) · [widescreen SVG](video-system.svg) · [plain-language pitch script](../../submission/pitch-script.md). This newer drawing describes the implemented final-release flow, with database cylinders, five tools, private/shared stores and validated native OpenUI. It supersedes the old planning system drawing for the video.

MCP checkpoint `397bfffa662d43ee82`; local files remain the durable references.

Text-field repair: current MCP checkpoint `9c29955606604823a6`; standalone annotations now include full native text dimensions so they remain visible when the scene is imported.
