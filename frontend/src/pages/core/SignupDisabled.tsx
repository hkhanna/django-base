import React from "react";
import { Head } from "@/components/Head";
import { Layout } from "@/components/Layout";
import { Logo } from "@/components/Logo";

export default function SignupDisabled() {
  return (
    <Layout>
      <Head title="Signup Is Closed" />
      <div className="flex min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Logo />
          <h2 className="my-4 text-center text-3xl font-bold leading-9 tracking-tight text-zinc-800 dark:text-zinc-300">
            Sign up is closed.
          </h2>
        </div>

        <p className="text-center">Come back another time.</p>
      </div>
    </Layout>
  );
}
