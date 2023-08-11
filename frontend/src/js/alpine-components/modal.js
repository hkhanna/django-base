export default function (Alpine) {
  Alpine.directive(
    "modal",
    (el, { value, modifiers, expression }, { effect, evaluate }) => {
      console.log(el.innerHTML.toString().trim());
      const innerHTML = render({
        show: expression,
        body: el.innerHTML.toString().trim(),
      });

      el.innerHTML = innerHTML;
    }
  );
}

function render(props) {
  let templ = `
    <div 
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
        `;

  if (props.body.length > 0) {
    templ += `${props.body}`;
  }
  templ += `
        </div>
      </div>
    </div>
  </div>
  `;

  return templ;
}
