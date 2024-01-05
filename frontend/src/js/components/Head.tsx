import { Head } from "@inertiajs/react";

// If you use the title prop, it will add the app name to the end.
// If you don't want the app name, you can use a title child instead.
export default function ({
  title,
  children,
}: {
  title?: string;
  children?: React.ReactNode;
}) {
  return <Head title={title && `${title} - django-base`}>{children}</Head>;
}
