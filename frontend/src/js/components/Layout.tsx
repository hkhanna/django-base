import React from "react";
import { usePage } from "@inertiajs/react";
import { useEffect } from "react";
import { User } from "@/types/User";
import { Navbar } from "@/components/catalyst/navbar";
import { Avatar } from "@/components/catalyst/avatar";
import {
  Sidebar as CatalystSidebar,
  SidebarBody,
  SidebarItem,
  SidebarLabel,
  SidebarSection,
  SidebarFooter,
} from "@/components/catalyst/sidebar";
import { SidebarLayout } from "@/components/catalyst/sidebar-layout";
import {
  Dropdown,
  DropdownButton,
  DropdownDivider,
  DropdownItem,
  DropdownLabel,
  DropdownMenu,
} from "@/components/catalyst/dropdown";
import {
  ChevronUpIcon,
  UserGroupIcon,
  Cog8ToothIcon,
  ArrowRightStartOnRectangleIcon,
} from "@heroicons/react/20/solid";
import { Logo } from "./Logo";

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

export function ApplicationLayout({ children }: { children: React.ReactNode }) {
  const page = usePage<{ user: User }>();

  return (
    <Layout>
      <SidebarLayout
        sidebar={<Sidebar user={page.props.user} />}
        navbar={<Navbar />}
      >
        {children}
      </SidebarLayout>
    </Layout>
  );
}

function Sidebar({ user }: { user: User }) {
  const page = usePage();
  const path = new URL(page.url).pathname;

  const firstInitial = user.first_name.charAt(0);
  const lastInitial = user.last_name.charAt(0);
  const initials = `${firstInitial}${lastInitial}`;

  return (
    <CatalystSidebar>
      <SidebarBody>
        <div className="mb-2 flex">
          <Logo />
        </div>
        <SidebarSection>
          <SidebarItem
            href="/user/settings/profile/"
            current={path.startsWith("/user/settings/profile/")}
          >
            <UserGroupIcon />
            <SidebarLabel>Profile (Replace Me)</SidebarLabel>
          </SidebarItem>
          <SidebarItem
            href="/user/settings/password/"
            current={path.startsWith("/user/settings/password/")}
          >
            <Cog8ToothIcon />
            <SidebarLabel>Password (Replace Me)</SidebarLabel>
          </SidebarItem>
        </SidebarSection>
      </SidebarBody>
      <SidebarFooter>
        <Dropdown>
          <DropdownButton as={SidebarItem}>
            <span className="flex min-w-0 items-center gap-3">
              <Avatar initials={initials} className="size-10" square alt="" />
              <span className="min-w-0">
                <span className="block truncate text-sm/5 font-medium text-zinc-950 dark:text-white">
                  {user.display_name}
                </span>
                <span className="block truncate text-xs/5 font-normal text-zinc-500 dark:text-zinc-400">
                  {user.email}
                </span>
              </span>
            </span>
            <ChevronUpIcon />
          </DropdownButton>
          <DropdownMenu className="min-w-64" anchor="top start">
            <DropdownItem href="/user/settings/profile">
              <Cog8ToothIcon />
              <DropdownLabel>Settings</DropdownLabel>
            </DropdownItem>
            <DropdownDivider />
            <DropdownItem href="/user/logout">
              <ArrowRightStartOnRectangleIcon />
              <DropdownLabel>Sign out</DropdownLabel>
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
      </SidebarFooter>
    </CatalystSidebar>
  );
}
