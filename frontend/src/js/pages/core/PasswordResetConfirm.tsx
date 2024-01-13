import React from "react";
import Head from "@/components/Head";
import {
  Field,
  Label,
  ErrorMessage,
  Fieldset,
} from "@/components/catalyst/fieldset";
import { Input } from "@/components/catalyst/input";
import { useForm, usePage } from "@inertiajs/react";
import { Text, TextLink } from "@/components/catalyst/text";
import { Button } from "@/components/catalyst/button";
import Layout from "@/components/Layout";

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
          <div className="flex flex-col items-center text-zinc-900 dark:text-white">
            <svg
              className="mx-auto h-10"
              fill="none"
              strokeWidth={1.5}
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m21 7.5-2.25-1.313M21 7.5v2.25m0-2.25-2.25 1.313M3 7.5l2.25-1.313M3 7.5l2.25 1.313M3 7.5v2.25m9 3 2.25-1.313M12 12.75l-2.25-1.313M12 12.75V15m0 6.75 2.25-1.313M12 21.75V19.5m0 2.25-2.25-1.313m0-16.875L12 2.25l2.25 1.313M21 14.25v2.25l-2.25 1.313m-13.5 0L3 16.5v-2.25"
              />
            </svg>
            <Text>django-base</Text>
          </div>
          <h2 className="my-4 text-center text-3xl font-bold leading-9 tracking-tight text-zinc-800 dark:text-zinc-300">
            Password Reset
          </h2>
        </div>

        {validlink ? (
          <>
            <Text className="text-center">Please choose a new password.</Text>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
              <div className="bg-white dark:bg-zinc-900 dark:border dark:border-white/10 px-6 py-10 shadow sm:rounded-lg sm:px-12">
                <form onSubmit={handleSubmit}>
                  <Fieldset
                    aria-label="Password reset form"
                    className="space-y-5"
                  >
                    <Field>
                      <Label>New password</Label>
                      <Input
                        name="new_password1"
                        type="password"
                        value={data.new_password1}
                        onChange={(e) =>
                          setData("new_password1", e.target.value)
                        }
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
                        onChange={(e) =>
                          setData("new_password2", e.target.value)
                        }
                        required
                        invalid={"new_password2" in errors}
                      />
                      {errors.new_password2 && (
                        <ErrorMessage>{errors.new_password2}</ErrorMessage>
                      )}
                    </Field>
                    {"__all__" in errors && (
                      <Field>
                        <ErrorMessage>
                          {errors.__all__ as React.ReactNode}
                        </ErrorMessage>
                      </Field>
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
                  </Fieldset>
                </form>
              </div>
            </div>
          </>
        ) : (
          <Text className="text-center">
            This password reset link is invalid.
          </Text>
        )}
      </div>
    </Layout>
  );
}
