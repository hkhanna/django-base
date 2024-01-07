import { useRemember } from "@inertiajs/react";
import { usePage } from "@inertiajs/react";
import { useToast } from "@/components/shadcn/use-toast";

export default function useMessages() {
  const page = usePage<{
    messages: { [key: string]: { text: string; level: string } };
  }>();

  // HACK: I don't love this, but it's the only way I can think of to deal with Inertia's
  // flaky window.history.state restoring on back_forward navigations.
  // Without this, old messages re-appear because Inertia likes to restore old
  // props, overwriting the new ones. This would result in an old message
  // being re-displayed after it's already been displayed during a back_forward
  // navigation.
  // On the other hand, maybe that's ok? It's not the worst thing if someone
  // sees a message twice if they navigate externally and come back.
  //
  // An unresolved problem is that useRemember seems to have a bug that causes
  // an console error. I actually suspect it's that bug that's giving me the behavior
  // I'm looking for: not restoring the window.history.state.props.messages.
  // It's kind of a mess. I'm going to think more about this.

  const [seenMessageIds, setSeenMessageIds] = useRemember<string[]>([]);
  const { toast } = useToast();

  const unseen = Object.keys(page.props.messages).filter(
    (key) => !seenMessageIds.includes(key)
  );

  if (unseen.length > 0) {
    unseen.forEach((id) => {
      const variant =
        page.props.messages[id].level === "error" ? "destructive" : "default";
      toast({ description: page.props.messages[id].text, variant });
    });
    setSeenMessageIds([...seenMessageIds, ...unseen]);
  }
}
