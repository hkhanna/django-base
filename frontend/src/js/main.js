import "../css/styles.css";
import "../css/fonts.css";
import Alpine from "alpinejs";
import alpineui from "@alpinejs/ui";
import focus from "@alpinejs/focus";
import "htmx.org";

// This is the entry point for any JS you want to include.
// This file should be loaded after any vite assets that are needed by Alpine.
// Add Javascript here.

// AlpineJS
Alpine.plugin(focus);
Alpine.plugin(alpineui);
window.Alpine = Alpine;
Alpine.start();
