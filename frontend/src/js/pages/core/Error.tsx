import { Button } from "@/components/catalyst/button";

export default function Error({
  status_code,
  support_email,
}: {
  status_code: number;
  support_email?: string;
}) {
  const title = {
    403: "Forbidden",
    404: "Page Not Found",
    500: "Server Error",
  }[status_code];

  const description = {
    403: "Sorry, you are not authorized to access this page.",
    404: "Sorry, the page you are looking for could not be found.",
    500: "Whoops, something went wrong on our servers.",
  }[status_code];

  return (
    <>
      <main className="grid min-h-full place-items-center bg-white px-6 py-24 sm:py-32 lg:px-8">
        <div className="text-center">
          <p className="text-base font-semibold text-zinc-600">{status_code}</p>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-zinc-900 sm:text-5xl">
            {title}
          </h1>
          <p className="mt-6 text-base leading-7 text-zinc-600">
            {description}
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Button href="/" color="zinc">
              Go back home
            </Button>
            {support_email && (
              <Button noInertia plain href={`mailto:${support_email}`}>
                Email support <span aria-hidden="true">&rarr;</span>
              </Button>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
