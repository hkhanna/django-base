import React from "react";
import { usePage } from "@inertiajs/react";
import { useEffect } from "react";
import { User } from "@/types/User";

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

  {
    /* 
  useEffect(() => {
    page.props.messages.forEach((message) =>
      toast[message.level](message.title, { description: message.description })
    );
  }, [page.props.messages]);
  FIXME */
  }

  return (
    <>
      <main>{children}</main>
      {/* <Toaster richColors /> FIXME */}
    </>
  );
}
