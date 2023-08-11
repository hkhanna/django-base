import CheckCircleIcon from "heroicons/24/solid/check-circle.svg";
import XMark from "heroicons/20/solid/x-mark.svg";

const COLORS = {
  success: {
    bg: "bg-green-100",
    iconSvg: CheckCircleIcon,
    icon: "text-green-500",
    headline: "text-green-800",
    body: "text-green-700",
    button:
      "bg-green-100 text-green-700 hover:bg-green-100 focus:ring-green-600",
  },
  warning: {
    bg: "bg-yellow-50",
    iconSvg: "exclamation-circle",
    icon: "text-yellow-400",
    headline: "text-yellow-800",
    body: "text-yellow-600",
    button:
      "bg-yellow-50 text-yellow-700 hover:bg-yellow-50 focus:ring-yellow-600",
  },
  info: {
    bg: "bg-blue-100",
    iconSvg: "information-circle",
    icon: "text-blue-500",
    headline: "text-blue-700",
    body: "text-blue-600",
    button: "bg-blue-100 text-blue-700 hover:bg-blue-100 focus:ring-blue-600",
  },
  error: {
    bg: "bg-red-50",
    iconSvg: "x-circle",
    icon: "text-red-400",
    headline: "text-red-800",
    body: "text-red-700",
    button: "bg-red-50 text-red-800 hover:bg-red-50 focus:ring-red-700",
  },
};

const render = (props) => {
  let templ = `
  <div class="rounded-md ${props.colors.bg} p-4" x-data="{ open: true }" x-show="open">
    <div class="flex items-start">
      <div class="flex-shrink-0">
        <svg class="h-5 w-5 ${props.colors.icon} xmlns="http://www.w3.org/2000/svg">
          <use xlink:href="${props.colors.iconSvg}"></use>
        </svg>
      </div>
      <div class="ml-3">
        <h3 class="text-sm font-medium ${props.colors.headling}">
          ${props.headline}
        </h3>
      </div>
    `;
  if (props.dismissable) {
    templ += `
        <div class="ml-auto pl-3">
          <div class="-mx-1.5 -my-1.5">
            <button type="button" class="inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 ${props.colors.button}" x-on:click="open = !open">
              <span class="sr-only">Dismiss</span>
              <img src=${XMark} class="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>
        `;
  }
  templ += "</div>";

  if (props.body.length > 0) {
    templ += `
      <div class="ml-8 mt-2 text-sm ${props.colors.body}">
        ${props.body}
      </div>
      `;
  }

  templ += "</div>";
  return templ;
};

export default function (Alpine) {
  Alpine.directive(
    "alert",
    (el, { value, modifiers, expression }, { effect, evaluate }) => {
      const headline = expression;

      const colors = COLORS[value] || COLORS.info;

      el.innerHTML = render({
        colors: colors,
        headline: headline,
        body: el.innerHTML.toString().trim(),
        dismissable: modifiers.includes("dismissable"),
      });
    }
  );
}
