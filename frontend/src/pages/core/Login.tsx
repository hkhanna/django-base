import React from "react";
import { Head } from "@/components/Head";
import { useForm } from "@inertiajs/react";
import { Button } from "@/components/ui/button";
import { Layout } from "@/components/Layout";
import { Logo } from "@/components/Logo";
import { FormInput } from "@/components/Form";
import { ContinueWithGoogle } from "@/components/SocialAuth";
import { Link } from "@/components/Link";

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

        <p className="text-center">
          Or <Link href="/user/signup/">sign up for free.</Link>
        </p>

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
            <form onSubmit={handleSubmit} className="space-y-4">
              <FormInput
                label="Email address"
                name="username"
                type="email"
                value={data.username}
                onChange={(e) => setData("username", e.target.value)}
                required
                errors={errors.username}
              />

              <FormInput
                label="Password"
                name="password"
                type="password"
                value={data.password}
                onChange={(e) => setData("password", e.target.value)}
                required
                errors={errors.password}
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
                  Sign in
                </Button>
              </div>
              <p className="text-center">
                <Link href="/user/password-reset/">Forgot password?</Link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
}
