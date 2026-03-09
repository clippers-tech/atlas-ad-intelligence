// Convenience re-export of the AccountContext hook.
// Prefer importing directly from @/contexts/AccountContext for new code;
// this wrapper exists so feature hooks can use a single consistent import path.

export { useAccountContext as useAccount } from "@/contexts/AccountContext";
