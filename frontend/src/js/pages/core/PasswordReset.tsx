import React from "react";
import Head from "@/components/Head";
import {
  Field,
  Label,
  ErrorMessage,
  Fieldset,
} from "@/components/catalyst/fieldset";
import { Input } from "@/components/catalyst/input";
import { useForm } from "@inertiajs/react";
import { Text, TextLink } from "@/components/catalyst/text";
import { Button } from "@/components/catalyst/button";
import Layout from "@/components/Layout";
import Logo from "@/components/Logo";

export default function PasswordReset() {
  const { data, setData, post, processing, errors } = useForm({
    email: "",
  });
  const [success, setSuccess] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post("/user/password-reset/", {
      forceFormData: true,
      onSuccess: () => {
        setSuccess(true);
      },
    });
  };

  return (
    <Layout>
      <Head title="Password Reset" />
      <div className="flex min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Logo />
          <h2 className="my-4 text-center text-3xl font-bold leading-9 tracking-tight text-zinc-800 dark:text-zinc-300">
            Password Reset
          </h2>
        </div>

        <Text className="text-center">
          Or{" "}
          <TextLink href="/user/login/">
            login if you already know your password.
          </TextLink>
        </Text>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white dark:bg-zinc-900 dark:border dark:border-white/10 px-6 py-10 shadow sm:rounded-lg sm:px-12">
            {success ? (
              <Text className="font-medium">
                If an account exists with that email address, we sent you an
                email with a link to reset your password.
              </Text>
            ) : (
              <form onSubmit={handleSubmit}>
                <Fieldset
                  aria-label="Password reset form"
                  className="space-y-5"
                >
                  <Field>
                    <Label>Email address</Label>
                    <Input
                      name="email"
                      type="email"
                      value={data.email}
                      onChange={(e) => setData("email", e.target.value)}
                      required
                      invalid={"email" in errors}
                    />
                    {errors.email && (
                      <ErrorMessage>{errors.email}</ErrorMessage>
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
                      Send password reset email
                    </Button>
                  </div>
                </Fieldset>
              </form>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
