import "@/css/styles.css";

import React from "react";
import axios from "axios";
import { createInertiaApp } from "@inertiajs/react";
import { createRoot } from "react-dom/client";
import * as Sentry from "@sentry/react";

const SENTRY_DSN = ""; // If set, will only be used in prod.

if (import.meta.env.PROD && SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    integrations: [Sentry.replayIntegration()],
    // Capture Replay for 10% of all sessions,
    // plus for 100% of sessions with an error
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}

document.addEventListener("DOMContentLoaded", () => {
  axios.defaults.xsrfHeaderName = "X-CSRFToken";
  axios.defaults.xsrfCookieName = "csrftoken";

  createInertiaApp({
    resolve: (name) => {
      // `name` will be the path of the component defined in
      const pages = import.meta.glob("./pages/**/*.{jsx,tsx}", { eager: true });
      return pages[`./pages/${name}.tsx`] || pages[`./pages/${name}.jsx`];
    },
    setup({ el, App, props }) {
      createRoot(el).render(<App {...props} />);
    },
  });
});
