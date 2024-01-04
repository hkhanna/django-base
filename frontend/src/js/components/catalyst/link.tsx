import { DataInteractive as HeadlessDataInteractive } from "@headlessui/react";
import { Link as InertiaLink, type InertiaLinkProps } from "@inertiajs/react";
import React from "react";

export const Link = React.forwardRef(function Link(
  { refresh, ...props }: InertiaLinkProps & { refresh?: boolean },
  ref: React.ForwardedRef<HTMLAnchorElement>
) {
  return (
    <HeadlessDataInteractive>
      {refresh ? (
        <a href={props.href} className={props.className} ref={ref}>
          {props.children}
        </a>
      ) : (
        <InertiaLink {...props} ref={ref} />
      )}
    </HeadlessDataInteractive>
  );
});
