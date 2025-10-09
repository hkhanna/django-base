import React from "react";
import { Head } from "@/components/Head";
import { useForm } from "@inertiajs/react";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import { Layout } from "@/components/Layout";
import { FormInput } from "@/components/Form";
import { ContinueWithGoogle } from "@/components/SocialAuth";
import { Link } from "@/components/Link";

type SocialAuth = {
  google: boolean;
  google_authorization_uri: string;
};

export default function Signup({ social_auth }: { social_auth: SocialAuth }) {
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
                  <span className="bg-zinc-50 dark:bg-zinc-900 px-2 text-gray-500">
                    Or continue with
                  </span>
                </div>
              </div>
            </>
          )}
          <div className="bg-white dark:bg-zinc-900 dark:border dark:border-white/10 px-6 py-10 shadow-sm sm:rounded-lg sm:px-12">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 sm:gap-4">
                <FormInput
                  label="First name"
                  name="first_name"
                  value={data.first_name}
                  onChange={(e) => setData("first_name", e.target.value)}
                  required
                  errors={errors.first_name}
                />
                <FormInput
                  label="Middle initial"
                  className="noteworthy"
                  name="middle_initial"
                  value={data.middle_initial}
                  onChange={(e) => setData("middle_initial", e.target.value)}
                  errors={errors.middle_initial}
                />
                <FormInput
                  label="Last name"
                  name="last_name"
                  value={data.last_name}
                  onChange={(e) => setData("last_name", e.target.value)}
                  required
                  errors={errors.last_name}
                />
                <FormInput
                  label="Email address"
                  name="email"
                  type="email"
                  value={data.email}
                  onChange={(e) => setData("email", e.target.value)}
                  required
                  errors={errors.email}
                  className="col-span-2"
                />
                <FormInput
                  label="Password"
                  name="password"
                  type="password"
                  value={data.password}
                  onChange={(e) => setData("password", e.target.value)}
                  required
                  errors={errors.password}
                  className="col-span-2"
                />
              </div>
              {"__all__" in errors && (
                <p className="text-red-500">
                  {errors.__all__ as React.ReactNode}
                </p>
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
                account with your email address, you acknowledge that you have
                read and understood, and agree to the{" "}
                <Link href="/terms">Terms of Use</Link> and{" "}
                <Link href="/privacy">Privacy Policy</Link>.
              </p>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
}
