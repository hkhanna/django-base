import Layout from "@/components/Layout";
import Logo from "@/components/Logo";
import markdownit from "markdown-it";

const md = markdownit();

export default function PrivacyPolicy() {
  return (
    <Layout>
      <div className="bg-zinc-50 dark:bg-zinc-900 px-6 py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-base leading-7 text-zinc-700">
          <Logo />
          <p className="mt-6 text-base font-semibold leading-7 text-indigo-600 dark:text-indigo-400">
            Last updated on January 1, 1970
          </p>
          <h1 className="mt-2 mb-6 text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
            Privacy Policy
          </h1>
          <div
            className="prose prose-zinc dark:prose-invert"
            dangerouslySetInnerHTML={{ __html: md.render(privacy) }}
          />
        </div>
      </div>
    </Layout>
  );
}

const privacy = `
## Introduction
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin finibus varius est vitae euismod.
Cras at orci in eros imperdiet facilisis id vel eros. Mauris pretium urna est, vitae aliquet felis cursus in.
Fusce felis mauris, facilisis sed erat quis, sagittis commodo nisi. Morbi a hendrerit nibh, ac feugiat turpis.
Nam ac lacus semper, consectetur elit eu, eleifend est. Mauris facilisis mauris a iaculis laoreet.

## Lorem Ipsum
Quisque eget justo sem. Morbi efficitur tellus quis mi dignissim maximus. Donec vel sem nunc.
Ut placerat arcu at nisi cursus mattis. Vivamus vel magna at nisi dignissim hendrerit.
Curabitur venenatis ultricies lorem ac tincidunt. Morbi venenatis velit a suscipit sodales.
Mauris cursus sit amet ante a convallis. Duis blandit tellus eget convallis faucibus.
Quisque ullamcorper tellus sed metus rhoncus ornare. Vivamus sit amet vehicula nibh.
Sed vel tortor vestibulum, molestie tellus in, condimentum leo.
Etiam eleifend, mi at consequat luctus, metus libero egestas nibh, ac pharetra nibh risus in lacus.
Vivamus in nibh sollicitudin, rutrum erat ut, congue orci.

Phasellus dictum eu enim vel laoreet. Nam iaculis libero et dolor sagittis feugiat. Curabitur ac eros augue.
Aenean sit amet nibh lobortis lectus rutrum ornare sit amet vel nunc. Nam id molestie libero.
Nulla sed feugiat ipsum. Nunc at vehicula velit. Nullam tincidunt auctor quam, a volutpat mi dictum non.
Sed eget interdum nulla. Phasellus interdum mauris vitae venenatis luctus. Etiam euismod orci ac dignissim tempus.

## Contact Information
Proin a nunc id lorem pharetra consequat a tristique neque. Ut non velit tincidunt urna condimentum commodo.
Morbi sollicitudin vulputate lectus sed lacinia. Ut quis tellus nec nisi laoreet sollicitudin. Integer viverra viverra lobortis.
Proin ac enim ac felis accumsan accumsan. Fusce hendrerit nibh turpis, eu condimentum nisl blandit ut.
Donec vestibulum accumsan blandit. Aliquam imperdiet quis purus nec tincidunt. Proin tincidunt dolor a facilisis pharetra.
`;
