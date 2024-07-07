import { router } from "@inertiajs/react";
import { Button } from "@/components/catalyst/button";

export default function OrgRequired({
  user,
  contact_email,
}: {
  user: { email: string; display_name: string };
  contact_email?: string;
}) {
  return (
    <>
      <main className="grid min-h-full place-items-center bg-white px-6 py-24 sm:py-32 lg:px-8">
        <div className="text-center">
          <p className="text-base font-semibold text-zinc-600">
            Organization Not Found
          </p>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-zinc-900 sm:text-5xl">
            We're missing something.
          </h1>
          <p className="mt-6 text-base leading-7 text-zinc-600">
            You've accessed a page that is part of an organization, but you
            currently aren't a member of any organizations.
          </p>

          <p className="mt-6 text-base leading-7 text-zinc-600">
            You are logged in as{" "}
            <span className="text-zinc-900">
              {user.email} ({user.display_name})
            </span>
            .
          </p>

          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Button outline onClick={() => router.post("/user/logout/")}>
              Sign out
            </Button>
            {contact_email && (
              <Button noInertia plain href={`mailto:${contact_email}`}>
                Email support <span aria-hidden="true">&rarr;</span>
              </Button>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
