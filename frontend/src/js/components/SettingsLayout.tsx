import React from "react";
import { Text } from "@/components/catalyst/text";
import { Button } from "@/components/catalyst/button";
import { ApplicationLayout } from "@/components/Layout";
import { Divider } from "@/components/catalyst/divider";

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
          <Text>Manage your account settings and set e-mail preferences.</Text>
        </div>
        <Divider />
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
          plain
          className="!justify-start"
          key={item.name}
          href={item.href}
          data-active={item.href === active ? true : undefined}
        >
          {item.name}
        </Button>
      ))}
    </nav>
  );
}
