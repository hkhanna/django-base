import React from "react";
import axios from "axios";
import { createInertiaApp } from "@inertiajs/react";
import { createRoot } from "react-dom/client";

document.addEventListener("DOMContentLoaded", () => {
  axios.defaults.xsrfHeaderName = "X-CSRFToken";
  createInertiaApp({
    resolve: (name) => {
      // `name` will be the path of the component defined in
      const pages = import.meta.glob("./pages/**/*.jsx", { eager: true });
      return pages[`./pages/${name}.jsx`];
    },
    setup({ el, App, props }) {
      createRoot(el).render(<App {...props} />);
    },
  });
});
