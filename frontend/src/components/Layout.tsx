import React from "react";
import { usePage, router } from "@inertiajs/react";
import { useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { User } from "@/types/User";
import { Toaster } from "@/components/ui/toaster";

/**
 * This is the layout for application pages. It can include things like a sidebar or navbar.
 */
export function ApplicationLayout({ children }: { children: React.ReactNode }) {
  const page = usePage<{ user: User }>();

  return <Layout>{children}</Layout>;
}

/**
 * This is the base layout. It's used for all pages, including pages like login and signup that are not
 * "application" pages. The latter would have things like sidebars etc.
 */
export function Layout({ children }: { children: React.ReactNode }) {
  const page = usePage<{
    messages: {
      title: string;
      description?: string;
      level: "success" | "info" | "warning" | "error";
    }[];
  }>();

  const { toast, dismiss } = useToast();

  // Show toast messages
  useEffect(() => {
    page.props.messages.forEach((message) =>
      toast({
        title: message.title,
        description: message.description,
        variant: message.level === "error" ? "destructive" : "default",
      })
    );
  }, [page.props.messages]);

  // Dismiss toast messages on navigation
  useEffect(() => {
    const unsubscribe = router.on("navigate", () => {
      dismiss();
    });

    return unsubscribe;
  }, [dismiss]);

  return (
    <>
      <main>{children}</main>
      <Toaster />
    </>
  );
}
