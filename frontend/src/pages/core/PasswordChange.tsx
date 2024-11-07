import React from "react";
import { Head } from "@/components/Head";
import { SettingsLayout } from "@/components/SettingsLayout";
import { useForm } from "@inertiajs/react";
import { Button } from "@/components/ui/button";
import { FormInput } from "@/components/Form";
import { Separator } from "@/components/ui/separator";

export default function PasswordChange({
  has_password,
}: {
  has_password: boolean;
}) {
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
          <h1 className="text-2xl font-semibold">Password</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            {has_password ? "Change your password." : "Set a password."}
          </p>
        </div>
        <Separator />
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <FormInput
              label="New password"
              name="new_password1"
              type="password"
              value={data.new_password1}
              onChange={(e) => setData("new_password1", e.target.value)}
              required
              errors={errors.new_password1}
            />
            <FormInput
              label="New password (again)"
              name="new_password2"
              type="password"
              value={data.new_password2}
              onChange={(e) => setData("new_password2", e.target.value)}
              required
              errors={errors.new_password2}
            />
          </div>

          {has_password && (
            <FormInput
              label="Current password"
              name="old_password"
              type="password"
              value={data.old_password}
              onChange={(e) => setData("old_password", e.target.value)}
              required
              errors={errors.old_password}
              className="max-w-md"
            />
          )}

          <Button type="submit" disabled={processing}>
            {has_password ? "Change password" : "Set password"}
          </Button>
        </form>
      </div>
    </SettingsLayout>
  );
}
