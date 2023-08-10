import "../css/styles.css";
import "../css/fonts.css";
import "htmx.org";
import Alpine from "alpinejs";
import alpineui from "@alpinejs/ui";
import focus from "@alpinejs/focus";
import alpineComponents from "./alpine-components";

// This is the entry point for any JS you want to include.
// This file should be loaded after any vite assets that are needed by Alpine.
// Add Javascript here.

// AlpineJS
Alpine.plugin(focus);
Alpine.plugin(alpineui);
Alpine.plugin(alpineComponents);
window.Alpine = Alpine;
Alpine.start();
