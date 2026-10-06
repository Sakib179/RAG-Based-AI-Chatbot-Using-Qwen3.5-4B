import { forwardRef, type HTMLAttributes } from "react";

export const ScrollArea = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  function ScrollArea({ className = "", ...props }, ref) {
    return <div ref={ref} className={`overflow-y-auto ${className}`} {...props} />;
  },
);

ScrollArea.displayName = "ScrollArea";
