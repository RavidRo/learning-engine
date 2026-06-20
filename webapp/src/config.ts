export const clerkPublishableKey = (): string | null => {
  const key = import.meta.env["VITE_CLERK_PUBLISHABLE_KEY"];
  return typeof key === "string" && key.trim() !== "" ? key.trim() : null;
};
