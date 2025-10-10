import React from "react";
import { usePage, router } from "@inertiajs/react";
import { useEffect } from "react";
import { toast } from "sonner";
import { User } from "@/types/User";
import { Toaster } from "@/components/ui/sonner";

/**
 * This is the layout for application pages. It can include things like a sidebar or navbar.
 */
export function ApplicationLayout({ children }: { children: React.ReactNode }) {
  const page = usePage<{ user: User }>();

  return (
    <Layout>
      {/* Enclosing div with padding can be removed once sidebar etc is added */}
      <div className="p-8">{children}</div>
    </Layout>
  );
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

  // Show toast messages
  useEffect(() => {
    page.props.messages.forEach((message) => {
      const toastMessage = message.description
        ? `${message.title}\n${message.description}`
        : message.title;

      switch (message.level) {
        case "success":
          toast.success(toastMessage);
          break;
        case "error":
          toast.error(toastMessage);
          break;
        case "warning":
          toast.warning(toastMessage);
          break;
        case "info":
          toast.info(toastMessage);
          break;
        default:
          toast(toastMessage);
      }
    });
  }, [page.props.messages]);

  // Dismiss toast messages on navigation
  useEffect(() => {
    const unsubscribe = router.on("success", () => {
      toast.dismiss();
    });

    return unsubscribe;
  }, []);

  return (
    <>
      <main>{children}</main>
      <Toaster />
    </>
  );
}
