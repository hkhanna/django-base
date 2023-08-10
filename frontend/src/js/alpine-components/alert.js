export default function (Alpine) {
  Alpine.directive("alert", (el, { expression }, { effect, evaluate }) => {
    const headline = expression;
    el.classList.add(
      ..."relative w-full rounded-lg border bg-white p-4 [&>svg]:absolute [&>svg]:text-foreground [&>svg]:left-4 [&>svg]:top-4 [&>svg+div]:translate-y-[-3px] [&:has(svg)]:pl-11 text-nuetral-900".split(
        " "
      )
    );

    const innerHtml = `
      <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" x2="20" y1="19" y2="19"></line></svg>
      <h5 class="mb-1 font-medium leading-none tracking-tight">${headline}</h5>
      <div class="text-sm opacity-70">${el.innerHTML.toString()}</div>
    `;

    el.innerHTML = innerHtml;
  });
}
