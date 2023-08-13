// Modal Usage
// <div x-modal:<show>.<submit>.<variant>.<formnovalidate>="{icon, title, submitLabel, submitName, submitValue, formaction}">Modal Body</div>
// show: name of Alpine variable that controls whether the modal is shown
// submit: if present, renders a submit-style modal. If this is not present, the rest of the arguments are ignored.
// variant: one of primary, secondary, or danger. Default is primary.
// formnovalidate: if present, adds the formnovalidate attribute to the submit button
// icon: name of the heroicon to use. Default is check-circle for primary, information for secondary, and exclamation-circle for danger.
// title: title of the modal
// submitLabel: label for the submit button. Default is "Submit".
// submitName: name attribute for the submit button (optional)
// submitValue: value attribute for the submit button (optional)
// formaction: formaction attribute for the submit button (optional)

const VARIANTS = {
  primary: {
    defaultIcon: "check-circle",
    iconBgColor: "bg-indigo-100",
    iconColor: "text-indigo-700",
  },
  secondary: {
    defaultIcon: "information",
    iconBgColor: "bg-blue-100",
    iconColor: "text-blue-500",
  },
  danger: {
    defaultIcon: "exclamation-circle",
    iconBgColor: "bg-red-100",
    iconColor: "text-red-600",
  },
};

export default function (Alpine) {
  Alpine.directive(
    "modal",
    (el, { value, modifiers, expression }, { effect, evaluate }) => {
      const modalDoc = renderModalDoc({
        show: value,
        body: el.innerHTML.toString().trim(),
      });

      if (modifiers.includes("submit")) {
        const { variant, defaultIcon, iconBgColor, iconColor, formnovalidate } =
          processModifiers(modifiers);

        const {
          icon,
          title,
          submitLabel,
          submitName,
          submitValue,
          formaction,
        } = evaluate(expression);

        modalDoc.getElementById("modal-body").outerHTML = renderSubmitModal({
          show: value,
          variant,
          icon: icon || defaultIcon,
          iconBgColor,
          iconColor,
          title,
          submitLabel,
          formnovalidate,
          formaction,
          submitName,
          submitValue,
        });
      }

      modalDoc.getElementById("modal-body").outerHTML = el.innerHTML;

      el.parentNode.replaceChild(modalDoc.body.firstChild, el);
    }
  );
}

function processModifiers(modifiers) {
  let props = { variant: "primary", ...VARIANTS.primary };

  if (modifiers.includes("secondary")) {
    props = { variant: "secondary", ...VARIANTS.secondary };
  }
  if (modifiers.includes("danger")) {
    props = { variant: "danger", ...VARIANTS.danger };
  }

  if (modifiers.includes("formnoaction")) {
    props.formnoaction = true;
  }

  if (modifiers.includes("formnovalidate")) {
    props.formnovalidate = true;
  }

  return props;
}

function renderSubmitModal({
  show,
  variant,
  icon,
  iconBgColor,
  iconColor,
  title,
  submitLabel,
  formnovalidate,
  formaction,
  submitName,
  submitValue,
}) {
  return `
  <div>
  <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full ${iconBgColor}">
    <div x-heroicon:outline=${icon} class="h-6 w-6 ${iconColor}" aria-hidden="true"></div>
  </div>
  <div class="mt-3 text-center sm:mt-5">
    <h3 class="text-lg leading-6 font-medium text-gray-900">
      ${title}
    </h3>
    <div class="mt-2">
      <div class="text-sm text-gray-800">
        <div id="modal-body"></div>
      </div>
    </div>
  </div>
</div>
  <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
    <button 
      x-btn:lg.${variant}
      type="submit" 
      class="w-full justify-center sm:col-start-2"
      ${submitName ? `name="${submitName}"` : ""}
      ${submitValue ? `value="${submitValue}"` : ""}
      ${formnovalidate ? "formnovalidate" : ""}
      ${formaction ? `formaction="${formaction}"` : ""}
    >
      ${submitLabel || "Submit"}
    </button>
    <button x-btn:lg.white type="button" x-on:click="${show} = false" class="mt-3 w-full justify-center sm:mt-0 sm:col-start-1">Cancel</button>
  </div>
  `;
}

function renderModalDoc(props) {
  const templ = `
    <div 
    x-data
    x-show="${props.show}"
    x-on:keyup.document.escape="${props.show} = false"
    x-cloak
    class="relative z-10"
    role="dialog"
    aria-modal="true"
  >
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
    <div class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end sm:items-center justify-center min-h-full p-4 text-center sm:p-0" aria-hidden="true"
        x-show="${props.show}"
        x-on:mousedown="${props.show} = false"
        x-transition:enter="ease-out duration-300"
        x-transition:enter-start="opacity-0"
        x-transition:enter-end="opacity-100"
        x-transition:leave="ease-in duration-200"
        x-transition:leave-start="opacity-100"
        x-transition:leave-end="opacity-0">

        <div
          x-on:mousedown.stop
          x-trap.noscroll="${props.show}"
          x-show="${props.show}"
          x-transition:enter="ease-out duration-300"
          x-transition:enter-start="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          x-transition:enter-end="opacity-100 translate-y-0 sm:scale-100"
          x-transition:leave="ease-in duration-200"
          x-transition:leave-start="opacity-100 translate-y-0 sm:scale-100"
          x-transition:leave-end="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          class="relative bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:max-w-lg w-full sm:p-6">

          <div class="absolute top-0 right-0 pt-4 pr-4">
            <button x-on:click="${props.show} = false" type="button" class="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
              <span class="sr-only">Close</span>
              <div x-heroicon:outline="x-mark" class="h-6 w-6" aria-hidden="true"></div>
            </button>
          </div>
          <div id="modal-body"></div>
        </div>
      </div>
    </div>
  </div>
  `;
  const parser = new DOMParser();
  const doc = parser.parseFromString(templ, "text/html");
  return doc;
}
