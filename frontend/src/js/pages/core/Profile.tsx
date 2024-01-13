import React from "react";
import Head from "@/components/Head";
import { SettingsLayout } from "@/components/SettingsLayout";
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
import { Separator } from "@/components/shadcn/separator";

export default function Profile({
  initial,
}: {
  initial: { first_name: string; last_name: string; email: string };
}) {
  const { data, setData, post, processing, errors, reset } = useForm({
    first_name: initial.first_name,
    last_name: initial.last_name,
    email: initial.email,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post("/user/settings/profile/", {
      forceFormData: true,
      onSuccess: () => reset(), // Show the normalized email address
    });
  };

  return (
    <SettingsLayout active="/user/settings/profile/">
      <Head title="Profile Settings" />
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
