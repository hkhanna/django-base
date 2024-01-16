import React from "react";
import useMessages from "@/lib/use-messages";

export default function Layout({ children }: { children: React.ReactNode }) {
  useMessages();

  return (
    <>
      <main>{children}</main>
    </>
  );
}
