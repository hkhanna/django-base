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

export default function PasswordChange() {
  const { data, setData, post, processing, errors, reset } = useForm({
    new_password1: "",
    new_password2: "",
    old_password: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post("/user/settings/password/", {
      forceFormData: true,
      onSuccess: () => {
        reset();
      },
    });
  };

  return (
    <SettingsLayout active="/user/settings/password/">
      <Head title="Account Settings" />
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium">Password</h3>
          <Text>Change your password.</Text>
        </div>
        <Separator />
        <form onSubmit={handleSubmit}>
          <Fieldset aria-label="Password change form">
            <FieldGroup>
              <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 sm:gap-4">
                <Field>
                  <Label>New password</Label>
                  <Input
                    name="new_password1"
                    type="password"
                    value={data.new_password1}
                    onChange={(e) => setData("new_password1", e.target.value)}
                    required
                    invalid={"new_password1" in errors}
                  />
                  {errors.new_password1 && (
                    <ErrorMessage>{errors.new_password1}</ErrorMessage>
                  )}
                </Field>
                <Field>
                  <Label>New password (again)</Label>
                  <Input
                    name="new_password2"
                    type="password"
                    value={data.new_password2}
                    onChange={(e) => setData("new_password2", e.target.value)}
                    required
                    invalid={"new_password2" in errors}
                  />
                  {errors.new_password2 && (
                    <ErrorMessage>{errors.new_password2}</ErrorMessage>
                  )}
                </Field>
                <Field>
                  <Label>Current password</Label>
                  <Input
                    name="old_password"
                    type="password"
                    value={data.old_password}
                    onChange={(e) => setData("old_password", e.target.value)}
                    required
                    invalid={"old_password" in errors}
                  />
                  {errors.old_password && (
                    <ErrorMessage>{errors.old_password}</ErrorMessage>
                  )}
                </Field>
              </div>

              <Button type="submit" disabled={processing}>
                Change password
              </Button>
            </FieldGroup>
          </Fieldset>
        </form>
      </div>
    </SettingsLayout>
  );
}
