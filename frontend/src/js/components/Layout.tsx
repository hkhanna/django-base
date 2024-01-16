import React from "react";
import { usePage } from "@inertiajs/react";
import { useEffect } from "react";
import { toast } from "sonner";
import { Toaster } from "@/components/shadcn/sonner";

export default function Layout({ children }: { children: React.ReactNode }) {
  const page = usePage<{
    messages: {
      text: string;
      level: "success" | "info" | "warning" | "error";
    }[];
  }>();

  useEffect(() => {
    page.props.messages.forEach((message) =>
      toast[message.level](message.text)
    );
  }, [page.props.messages]);

  return (
    <>
      <main>{children}</main>
      <Toaster />
    </>
  );
}
