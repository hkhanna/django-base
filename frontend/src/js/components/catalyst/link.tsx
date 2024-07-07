import * as Headless from "@headlessui/react";
import { Link as InertiaLink, type InertiaLinkProps } from "@inertiajs/react";
import React, { forwardRef } from "react";

export const Link = forwardRef(function Link(
  { noInertia, ...props }: InertiaLinkProps & { noInertia?: boolean },
  ref: React.ForwardedRef<HTMLAnchorElement>
) {
  return (
    <Headless.DataInteractive>
      {noInertia ? (
        <a href={props.href} className={props.className} ref={ref}>
          {props.children}
        </a>
      ) : (
        <InertiaLink {...props} ref={ref} />
      )}
    </Headless.DataInteractive>
  );
});
