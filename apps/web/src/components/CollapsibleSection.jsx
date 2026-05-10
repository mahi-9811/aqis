import { useState } from "react";

export default function CollapsibleSection({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="surface collapsible">
      <button className="collapse-toggle" type="button" onClick={() => setOpen((value) => !value)}>
        <span>{title}</span>
        <span>{open ? "Hide" : "Show"}</span>
      </button>
      {open ? <div className="collapse-content">{children}</div> : null}
    </section>
  );
}
