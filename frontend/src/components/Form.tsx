import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import * as React from "react";

import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const FormInput = ({
  label,
  name,
  errors,
  className,
  inputClassName,
  ...props
}: {
  label: string;
  name: string;
  errors: any;
  className?: string;
  inputClassName?: string;
} & InputProps) => {
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={name}>{label}</Label>
      <Input
        {...props}
        className={cn(
          errors && "border-red-500 ring-2 ring-red-500",
          inputClassName
        )}
      />
      {errors && <p className="text-sm text-red-500">{errors}</p>}
    </div>
  );
};
export { FormInput };
