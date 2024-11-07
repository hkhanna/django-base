import React from "react";
import { Head } from "@/components/Head";
import { useForm, usePage } from "@inertiajs/react";
import { Button } from "@/components/ui/button";
import { Layout } from "@/components/Layout";
import { Logo } from "@/components/Logo";
import { FormInput } from "@/components/Form";

export default function PasswordResetConfirm({
  validlink,
}: {
  validlink: boolean;
}) {
  const page = usePage();
  const { data, setData, post, processing, errors } = useForm({
    new_password1: "",
    new_password2: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post(page.url, {
      forceFormData: true,
    });
  };

  return (
    <Layout>
      <Head title="Set New Password" />
      <div className="flex min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Logo />
          <h2 className="my-4 text-center text-3xl font-bold leading-9 tracking-tight text-zinc-800 dark:text-zinc-300">
            Password Reset
          </h2>
        </div>

        {validlink ? (
          <>
            <p className="text-center">Please choose a new password.</p>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
              <div className="bg-white dark:bg-zinc-900 dark:border dark:border-white/10 px-6 py-10 shadow sm:rounded-lg sm:px-12">
                <form onSubmit={handleSubmit} className="space-y-4">
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

                  {"__all__" in errors && (
                    <p className="text-sm text-red-500">
                      {errors.__all__ as React.ReactNode}
                    </p>
                  )}

                  <div>
                    <Button
                      type="submit"
                      className="flex w-full justify-center"
                      disabled={processing}
                    >
                      Confirm new password
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          </>
        ) : (
          <p className="text-center">This password reset link is invalid.</p>
        )}
      </div>
    </Layout>
  );
}
