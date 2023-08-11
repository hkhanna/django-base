// Defaults to Solid 24px
// There's no outline 20px, so we ensure outlines use 24px.

export default function (Alpine) {
  Alpine.directive(
    "heroicon",
    (el, { value, modifiers, expression }, { effect, evaluate }) => {
      const variant = value || "solid";
      const size =
        variant === "outline" ? "24" : modifiers.includes("20") ? "20" : "24";
      import(
        `../../../node_modules/heroicons/${size}/${variant}/${expression}.svg`
      ).then((svgString) => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgString.default, "image/svg+xml");
        replaceClasses(el, doc.documentElement);
        el.parentNode.replaceChild(doc.documentElement, el);
      });
    }
  );
}

function replaceClasses(sourceElement, targetElement) {
  // Clear the classes of the target element
  while (targetElement.classList.length > 0) {
    targetElement.classList.remove(targetElement.classList.item(0));
  }

  // Add the classes from the source element to the target element
  for (let i = 0; i < sourceElement.classList.length; i++) {
    targetElement.classList.add(sourceElement.classList[i]);
  }
}
