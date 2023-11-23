import React from "react";
import Layout from "../components/Layout";
import { Head } from "@inertiajs/react";

export default function InertiaTest({ user }) {
  return (
    <Layout>
      <Head title="Welcome" />
      <h1>Welcome</h1>
      <p>Hello {user}, welcome to your first Inertia app!</p>
    </Layout>
  );
}
