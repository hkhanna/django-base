import React from "react";
import { Toaster } from "@/components/shadcn/toaster";
import { useToast } from "@/components/shadcn/use-toast";

export default function Layout({ children }: { children: React.ReactNode }) {
  const { toast } = useToast();

  return (
    <>
      <main>{children}</main>
      <Toaster />
    </>
  );
}
