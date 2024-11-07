import React from "react";
import { Head } from "@/components/Head";
import { SettingsLayout } from "@/components/SettingsLayout";
import { useForm } from "@inertiajs/react";
import { Button } from "@/components/ui/button";
import { FormInput } from "@/components/Form";
import { Separator } from "@/components/ui/separator";

export default function Profile({
  initial,
}: {
  initial: {
    first_name: string;
    last_name: string;
    display_name: string;
    email: string;
  };
}) {
  const { data, setData, post, processing, errors } = useForm({
    first_name: initial.first_name,
    last_name: initial.last_name,
    display_name: initial.display_name,
    email: initial.email,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post("/user/settings/profile/", {
      forceFormData: true,
      // If there's no errors, refresh the state to get normalized fields.
      // If there are errors, don't refresh the state because we need to display the errors.
      preserveState: (page) => !!Object.keys(page.props.errors).length,
    });
  };

  return (
    <SettingsLayout active="/user/settings/profile/">
      <Head title="Profile Settings" />
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Profile</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            This is how others will see you on the site.
          </p>
        </div>
        <Separator />
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <FormInput
              label="First name"
              name="first_name"
              value={data.first_name}
              onChange={(e) => setData("first_name", e.target.value)}
              required
              errors={errors.first_name}
            />
            <FormInput
              label="Last name"
              name="last_name"
              value={data.last_name}
              onChange={(e) => setData("last_name", e.target.value)}
              required
              errors={errors.last_name}
            />
          </div>

          <FormInput
            label="Display name"
            name="display_name"
            value={data.display_name}
            onChange={(e) => setData("display_name", e.target.value)}
            errors={errors.display_name}
            className="max-w-md"
          />

          <FormInput
            label="Email address"
            name="email"
            type="email"
            value={data.email}
            onChange={(e) => setData("email", e.target.value)}
            required
            errors={errors.email}
            className="max-w-md"
          />

          <Button type="submit" disabled={processing}>
            Update profile
          </Button>
        </form>
      </div>
    </SettingsLayout>
  );
}
