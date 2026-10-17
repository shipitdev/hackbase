import "./openui-bootstrap";
import React from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider } from "@openuidev/react-ui";
import "@openuidev/react-ui/layered/styles/index.css";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider mode="light"><App /></ThemeProvider>
  </React.StrictMode>,
);
