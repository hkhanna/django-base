import '../css/styles.css'
import Alpine from 'alpinejs'
import focus from '@alpinejs/focus'

// This is the entry point for any JS you want to include.
// This file should be loaded after any vite assets that are needed by Alpine.
// Add Javascript here.

// AlpineJS
Alpine.plugin(focus)
window.Alpine = Alpine
Alpine.start()