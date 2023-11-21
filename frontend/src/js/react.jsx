import React from "react";
import ReactDOMClient from "react-dom/client";

window.ReactDOMClient = ReactDOMClient;
window.React = React;

export const Test = ({hi}) => (
  <div>
    <h1>Hello, {hi} world!</h1>
  </div>
);

window.Test = Test