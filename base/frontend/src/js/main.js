import '../css/styles.css'
// This is the entry point for any JS you want to include.
// e.g., console.log("django_vite is working!")

// AlpineJS
import Alpine from 'alpinejs'
import focus from '@alpinejs/focus'
Alpine.plugin(focus)
window.Alpine = Alpine
Alpine.start()

// Utility functions
// Add a Django Form to a Formset
window.addForm = (selector, totalFormSelector) => {
  let totalFormEl = document.querySelector(totalFormSelector)
  let templateEl = document.querySelector(selector)

  // Clone the node
  let cloned = templateEl.content.cloneNode(true)

  // Replace __prefix__ with the incremented total form count
  for(let child of cloned.querySelectorAll("label,input")) {
    child.outerHTML = child.outerHTML.replaceAll("__prefix__", totalFormEl.value)
  }
  // Insert the updated node
  templateEl.after(cloned)

  // Increment the total form count
  totalFormEl.value++
}
