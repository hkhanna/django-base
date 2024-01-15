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
import { TextLink } from "@/components/catalyst/text";
import Logo from "@/components/Logo";
import { Button } from "@/components/catalyst/button";
import Layout from "@/components/Layout";

export default function Signup() {
  const { data, setData, post, processing, errors } = useForm({
    email: "",
    first_name: "",
    middle_initial: "",
    last_name: "",
    password: "",
    detected_tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post("/user/signup/", { forceFormData: true });
  };

  return (
    <Layout>
      <Head title="Sign Up" />
      <div className="flex min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Logo />
          <h2 className="my-4 text-center text-3xl font-bold leading-9 tracking-tight text-zinc-800 dark:text-zinc-300">
            Sign Up
          </h2>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white dark:bg-zinc-900 dark:border dark:border-white/10 px-6 py-10 shadow sm:rounded-lg sm:px-12">
            <form onSubmit={handleSubmit}>
              <Fieldset aria-label="Signup form" className="space-y-5">
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
                    <Field className="noteworthy">
                      <Label>Middle initial</Label>
                      <Input
                        name="middle_initial"
                        value={data.middle_initial}
                        onChange={(e) =>
                          setData("middle_initial", e.target.value)
                        }
                        invalid={"middle_initial" in errors}
                      />
                      {errors.middle_initial && (
                        <ErrorMessage>{errors.middle_initial}</ErrorMessage>
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
                  <Field>
                    <Label>Password</Label>
                    <Input
                      name="password"
                      type="password"
                      value={data.password}
                      onChange={(e) => setData("password", e.target.value)}
                      required
                      invalid={"password" in errors}
                    />
                    {errors.password && (
                      <ErrorMessage>{errors.password}</ErrorMessage>
                    )}
                  </Field>

                  {"__all__" in errors && (
                    <Field>
                      <ErrorMessage>
                        {errors.__all__ as React.ReactNode}
                      </ErrorMessage>
                    </Field>
                  )}

                  <Button
                    type="submit"
                    className="flex w-full justify-center"
                    disabled={processing}
                  >
                    Create account
                  </Button>
                  <p className="text-sm sm:text-xs text-zinc-500 dark:text-zinc-400">
                    By clicking "Continue with Google" above or by creating an
                    account with your email address, you acknowledge that you
                    have read and understood, and agree to the{" "}
                    <TextLink refresh href="/terms">
                      Terms of Use
                    </TextLink>{" "}
                    and{" "}
                    <TextLink refresh href="/privacy">
                      Privacy Policy
                    </TextLink>
                    .
                  </p>
                </FieldGroup>
              </Fieldset>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
}
