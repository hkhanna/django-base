import { cn } from "@/lib/utils";
import { Link as InertiaLink, type InertiaLinkProps } from "@inertiajs/react";
import React, { forwardRef } from "react";

export const Link = forwardRef(function Link(
  props: InertiaLinkProps,
  ref: React.ForwardedRef<HTMLAnchorElement>
) {
  const noInertia =
    props.href.startsWith("http") || props.href.startsWith("mailto");

  const { className, ...restProps } = props;

  return noInertia ? (
    <a
      href={props.href}
      className={cn(
        "font-medium text-primary underline underline-offset-4",
        className
      )}
      ref={ref}
    >
      {props.children}
    </a>
  ) : (
    <InertiaLink
      {...restProps}
      className={cn(
        "font-medium text-primary underline underline-offset-4",
        className
      )}
      ref={ref}
    />
  );
});
