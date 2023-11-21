import React from "react";
import ReactDOMClient from "react-dom/client";

export const Example = ({ prop1 }) => (
  <div className="text-gray-700 text-sm">
    This is a React component. Prop: {prop1}
  </div>
);

const Components = {
  Example,
};

const component_json = JSON.parse(
  document.getElementById("django_react_templatetags_components").textContent
);
component_json.forEach((component) => {
  const container = document.getElementById(component.identifier);
  const root = ReactDOMClient.createRoot(container);
  root.render(
    React.createElement(Components[component.name], component.json_obj)
  );
});
