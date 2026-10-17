// shortcut: OpenUI 1.0.1 ignores the public enabled=false opt-out; check this flag on upgrade.
// Stop its automatic inspector before importing OpenUI: the toggle covers mobile Send.
Reflect.set(globalThis, Symbol.for("openui.devtools.autoMount"), true);
