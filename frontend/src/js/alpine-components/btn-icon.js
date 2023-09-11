// Btn-icon Usage
// <button x-btn-icon:[left|right]="icon-name">Button label</button>

export default function (Alpine) {
  Alpine.directive(
    "btn-icon",
    (el, { value, modifiers, expression }, { effect, evaluate }) => {
      const sizeClass =
        Array.from(el.classList.values()).find((value) =>
          ICON_SIZES.hasOwnProperty(value)
        ) || "btn-md";

      const icon = document.createElement("div");
      icon.classList.add(...ICON_SIZES[sizeClass]);
      icon.setAttribute("x-heroicon:solid.20", expression);

      if (value === "right") {
        icon.classList.add(...ICON_SPACING_RIGHT[sizeClass]);
        el.append(icon);
      } else {
        icon.classList.add(...ICON_SPACING_LEFT[sizeClass]);
        icon.setAttribute("x-heroicon:solid.20", expression);
        el.prepend(icon);
      }
    }
  );
}

const ICON_SIZES = {
  "btn-xs": ["h-4", "w-4"],
  "btn-sm": ["h-4", "w-4"],
  "btn-md": ["h-5", "w-5"],
  "btn-lg": ["h-6", "w-6"],
  "btn-xl": ["h-6", "w-6"],
};

const ICON_SPACING_LEFT = {
  "btn-xs": ["-ml-0.5", "mr-2"],
  "btn-sm": ["-ml-1", "mr-2"],
  "btn-md": ["-ml-1", "mr-2"],
  "btn-lg": ["-ml-1", "mr-3"],
  "btn-xl": ["-ml-1", "mr-3"],
};

const ICON_SPACING_RIGHT = {
  "btn-xs": ["-mr-0.5", "ml-2"],
  "btn-sm": ["-mr-1", "ml-2"],
  "btn-md": ["-mr-1", "ml-2"],
  "btn-lg": ["-mr-1", "ml-3"],
  "btn-xl": ["-mr-1", "ml-3"],
};
