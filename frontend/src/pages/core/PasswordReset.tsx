import React from "react";
import { Head } from "@/components/Head";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useForm } from "@inertiajs/react";
import { Link } from "@/components/Link";
import { Layout } from "@/components/Layout";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";

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

        <p className="text-center">
          Or{" "}
          <Link href="/user/login/">
            login if you already know your password.
          </Link>
        </p>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white dark:bg-zinc-900 dark:border dark:border-white/10 px-6 py-10 shadow sm:rounded-lg sm:px-12">
            {success ? (
              <p className="leading-7 [&:not(:first-child)]:mt-6">
                If an account exists with that email address, we sent you an
                email with a link to reset your password.
              </p>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label
                    htmlFor="email"
                    className={errors.email && "text-red-500"}
                  >
                    Email address
                  </Label>
                  <Input
                    name="email"
                    type="email"
                    value={data.email}
                    onChange={(e) => setData("email", e.target.value)}
                    className={
                      errors.email && "border-red-500 ring-2 ring-red-500"
                    }
                    required
                  />
                  {errors.email && (
                    <p className="text-sm text-red-500">{errors.email}</p>
                  )}
                </div>
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
                    Send password reset email
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
