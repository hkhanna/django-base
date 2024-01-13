import React from "react";
import Head from "@/components/Head";
import {
  Field,
  Label,
  ErrorMessage,
  Fieldset,
  FieldGroup,
} from "@/components/catalyst/fieldset";
import { Input } from "@/components/catalyst/input";
import { useForm } from "@inertiajs/react";
import { Text, TextLink } from "@/components/catalyst/text";
import { Button } from "@/components/catalyst/button";
import Layout from "@/components/Layout";
import { Separator } from "@/components/shadcn/separator";
import { cn } from "@/lib/shadcn";

export default function UserProfile({
  initial,
}: {
  initial: { first_name: string; last_name: string; email: string };
}) {
  const { data, setData, post, processing, errors } = useForm({
    first_name: initial.first_name,
    last_name: initial.last_name,
    email: initial.email,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post("/user/settings/profile/", { forceFormData: true });
  };

  return (
    <SettingsLayout>
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">Profile</h3>
          <Text>This is how others will see you on the site.</Text>
        </div>
        <Separator />
        <form onSubmit={handleSubmit}>
          <Fieldset aria-label="Profile form">
            <FieldGroup>
              <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 sm:gap-4">
                <Field>
                  <Label>First name</Label>
                  <Input
                    name="first_name"
                    value={data.first_name}
                    onChange={(e) => setData("first_name", e.target.value)}
                    required
                    invalid={"first_name" in errors}
                  />
                  {errors.first_name && (
                    <ErrorMessage>{errors.first_name}</ErrorMessage>
                  )}
                </Field>
                <Field>
                  <Label>Last name</Label>
                  <Input
                    name="last_name"
                    value={data.last_name}
                    onChange={(e) => setData("last_name", e.target.value)}
                    required
                    invalid={"last_name" in errors}
                  />
                  {errors.last_name && (
                    <ErrorMessage>{errors.last_name}</ErrorMessage>
                  )}
                </Field>
              </div>
              <div className="grid grid-cols-1 gap-8 sm:grid-cols-3 sm:gap-4">
                <Field className="col-span-2">
                  <Label>Email address</Label>
                  <Input
                    name="email"
                    type="email"
                    value={data.email}
                    onChange={(e) => setData("email", e.target.value)}
                    required
                    invalid={"email" in errors}
                  />
                  {errors.email && <ErrorMessage>{errors.email}</ErrorMessage>}
                </Field>
              </div>
              <Button type="submit" disabled={processing}>
                Update profile
              </Button>
            </FieldGroup>
          </Fieldset>
        </form>
      </div>
    </SettingsLayout>
  );
}

function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <Layout>
      <Head title="Profile" />
      <div className="space-y-6 p-10 pb-16">
        <div className="space-y-0.5">
          <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
          <Text>Manage your account settings and set e-mail preferences.</Text>
        </div>
        <Separator className="my-6" />
        <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
          <aside className="-mx-4 lg:w-1/5">
            <SettingsSidebarNav active="/user/settings/profile/" />
          </aside>
          <div className="flex-1 lg:max-w-2xl">{children}</div>
        </div>
      </div>
    </Layout>
  );
}

const sidebarItems = [
  { name: "Profile", href: "/user/settings/profile/" },
  { name: "Account", href: "/user/settings/account/" },
];

export function SettingsSidebarNav({ active }: { active?: string }) {
  return (
    <nav className={cn("flex space-x-2 lg:flex-col lg:space-x-0 lg:space-y-1")}>
      {sidebarItems.map((item) => (
        <Button
          plain
          nocenter
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
