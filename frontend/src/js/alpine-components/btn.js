// Pass the variant as the value, e.g., x-btn:primary
// disabled can be passed as a modifier or in the expression

/*
 * We do styling of the button via this Alpine directive.
 * It would be more accessible to non-JS enabled browsers if we used
 * tailwind @apply, so this is a tradeoff we're making for better DX.
 * If it becomes an issue, we can always switch to @apply and remove the styling
 * here.
 */

export default function (Alpine) {
  Alpine.directive(
    "btn",
    (el, { value, modifiers, expression }, { effect, evaluate }) => {
      const data = expression ? evaluate(expression) : {};

      let classes = [
        "inline-flex",
        "relative",
        "items-center",
        "font-medium",
        "focus:outline-none",
      ];

      const variant = value || "primary";
      classes = classes.concat(VARIANTS[variant].common);

      const disabled = modifiers.includes("disabled") || data.disabled;
      if (disabled) {
        classes = classes.concat(VARIANTS[variant].disabled);
      } else {
        classes = classes.concat(VARIANTS[variant].enabled);
      }

      const size = getSize(modifiers);
      classes = classes.concat(SIZES[size]);

      el.classList.add(...classes);
    }
  );
}

function getSize(modifiers) {
  if (modifiers.includes("xs")) {
    return "xs";
  } else if (modifiers.includes("sm")) {
    return "sm";
  } else if (modifiers.includes("md")) {
    return "md";
  } else if (modifiers.includes("lg")) {
    return "lg";
  } else if (modifiers.includes("xl")) {
    return "xl";
  }

  return "md";
}

const VARIANTS = {
  primary: {
    common: [
      "text-white",
      "border",
      "border-transparent",
      "shadow-sm",
      "rounded-md",
    ],
    enabled: [
      "bg-indigo-600",
      "hover:bg-indigo-500",
      "focus:ring-2",
      "focus:ring-offset-2",
      "focus:ring-indigo-500",
    ],
    disabled: ["cursor-default", "bg-indigo-300"],
  },
  secondary: {
    common: ["border", "border-transparent", "shadow-sm", "rounded-md"],
    enabled: [
      "text-indigo-700",
      "bg-indigo-100",
      "hover:bg-indigo-200",
      "focus:ring-2",
      "focus:ring-offset-2",
      "focus:ring-indigo-500",
    ],
    disabled: ["cursor-default", "text-indigo-300", "bg-indigo-100"],
  },
  white: {
    common: ["border", "bg-white", "shadow-sm", "rounded-md"],
    enabled: [
      "border-gray-300",
      "text-gray-700",
      "hover:bg-gray-50",
      "focus:ring-2",
      "focus:ring-offset-2",
      "focus:ring-indigo-500",
    ],
    disabled: ["cursor-default", "border-gray-200", "text-gray-400"],
  },
  danger: {
    common: [
      "border",
      "border-transparent",
      "text-white",
      "shadow-sm",
      "rounded-md",
    ],
    enabled: [
      "bg-red-600",
      "hover:bg-red-500",
      "focus:ring-2",
      "focus:ring-offset-2",
      "focus:ring-indigo-500",
    ],
    disabled: ["cursor-default", "bg-red-400"],
  },
};

const SIZES = {
  xs: ["text-xs", "leading-4", "px-2.5", "py-1.5"],
  sm: ["text-sm", "leading-5", "px-3", "py-2"],
  md: ["text-sm", "leading-5", "px-4", "py-2"],
  lg: ["text-base", "leading-6", "px-4", "py-2"],
  xl: ["text-base", "leading-6", "px-5", "py-3"],
};

const ICON_SIZES = {
  xs: "h-4 w-4",
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
  xl: "h-6 w-6",
};

const ICON_SPACING_LEFT = {
  xs: ["-ml-0.5", "mr-2"],
  sm: ["-ml-1", "mr-2"],
  md: ["-ml-1", "mr-2"],
  lg: ["-ml-1", "mr-3"],
  xl: ["-ml-1", "mr-3"],
};

const ICON_SPACING_RIGHT = {
  xs: ["-mr-0.5", "ml-2"],
  sm: ["-mr-1", "ml-2"],
  md: ["-mr-1", "ml-2"],
  lg: ["-mr-1", "ml-3"],
  xl: ["-mr-1", "ml-3"],
};
