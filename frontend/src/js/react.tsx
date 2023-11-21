import React from "react";
import ReactDOMClient from "react-dom/client";

// -- Import and add components -- //
import { Example } from "./components/Example.tsx";

export const Components = {
  Example,
};
// -- End of components -- // 

const component_json = JSON.parse(
  document.getElementById("django_react_templatetags_components")?.textContent || "{}"
);
component_json.forEach((component) => {
  const container = document.getElementById(component.identifier);
  const root = ReactDOMClient.createRoot(container);
  root.render(
    React.createElement(Components[component.name], component.json_obj)
  );
});
