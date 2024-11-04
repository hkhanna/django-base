import React from "react";
import { Head } from "@/components/Head";
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
import { Layout } from "@/components/Layout";
import { Logo } from "@/components/Logo";
import { ContinueWithGoogle } from "@/components/SocialAuth";

type SocialAuth = {
  google: boolean;
  google_authorization_uri: string;
};

export default function Login({ social_auth }: { social_auth: SocialAuth }) {
  const { data, setData, post, processing, errors } = useForm({
    username: "",
    password: "",
    detected_tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    post("/user/login/", { forceFormData: true });
  };

  return (
    <Layout>
      <Head title="Login" />
      <div className="flex min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Logo />
          <h2 className="my-4 text-center text-3xl font-bold leading-9 tracking-tight text-zinc-800 dark:text-zinc-300">
            Sign in to your account
          </h2>
        </div>

        <Text className="text-center">
          Or <TextLink href="/user/signup/">sign up for free.</TextLink>
        </Text>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white dark:bg-zinc-900 dark:border dark:border-white/10 px-6 py-10 shadow sm:rounded-lg sm:px-12">
            {social_auth.google && (
              <>
                <ContinueWithGoogle
                  authorizationUri={social_auth.google_authorization_uri}
                  detectedTz={data.detected_tz}
                />
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="bg-white px-2 text-gray-500">
                      Or continue with
                    </span>
                  </div>
                </div>
              </>
            )}
            <form onSubmit={handleSubmit}>
              <Fieldset aria-label="Login form" className="space-y-5">
                <Field>
                  <Label>Email address</Label>
                  <Input
                    name="username"
                    type="email"
                    value={data.username}
                    onChange={(e) => setData("username", e.target.value)}
                    required
                    invalid={"username" in errors}
                  />
                  {errors.username && (
                    <ErrorMessage>{errors.username}</ErrorMessage>
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

                <div>
                  <Button
                    type="submit"
                    className="flex w-full justify-center"
                    disabled={processing}
                  >
                    Sign in
                  </Button>
                </div>
                <Text className="flex justify-center">
                  <TextLink href="/user/password-reset/">
                    Forgot password?
                  </TextLink>
                </Text>
              </Fieldset>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
}
