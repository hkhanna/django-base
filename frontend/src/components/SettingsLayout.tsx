import React from "react";
import { Button } from "@/components/ui/button";
import { ApplicationLayout } from "@/components/Layout";
import { Separator } from "@/components/ui/separator";
import { Link as InertiaLink } from "@inertiajs/react";
import { cn } from "@/lib/utils";

const sidebarItems = [
  { name: "Profile", href: "/user/settings/profile/" },
  { name: "Password", href: "/user/settings/password/" },
];

export function SettingsLayout({
  active,
  children,
}: {
  active: string;
  children: React.ReactNode;
}) {
  return (
    <ApplicationLayout>
      <div className="space-y-6 pb-16">
        <div className="space-y-0.5">
          <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Settings
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Manage your account settings and set e-mail preferences.
          </p>
        </div>
        <Separator />
        <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
          <aside className="-mx-4 lg:w-1/5">
            <SettingsSidebarNav active={active} />
          </aside>
          <div className="flex-1 lg:max-w-2xl">{children}</div>
        </div>
      </div>
    </ApplicationLayout>
  );
}

function SettingsSidebarNav({ active }: { active?: string }) {
  return (
    <nav className="flex space-x-2 lg:flex-col lg:space-x-0 lg:space-y-1">
      {sidebarItems.map((item) => (
        <Button
          variant="link"
          className={cn(
            "justify-start!",
            item.href === active &&
              "bg-zinc-100 dark:bg-zinc-800 hover:no-underline"
          )}
          key={item.name}
          asChild
          data-active={item.href === active ? true : undefined}
        >
          <InertiaLink href={item.href}>{item.name}</InertiaLink>
        </Button>
      ))}
    </nav>
  );
}
