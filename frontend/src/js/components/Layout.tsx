import React from "react";
import useMessages from "@/lib/use-messages";
import { Toaster } from "@/components/shadcn/toaster";

export default function Layout({ children }: { children: React.ReactNode }) {
  useMessages();

  return (
    <>
      <main>{children}</main>
      <Toaster />
    </>
  );
}
