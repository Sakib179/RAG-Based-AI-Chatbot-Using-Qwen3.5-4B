import axios from "axios";

export function getErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.message === "string") return data.message;
    if (typeof data?.detail === "string") return data.detail;
    if (!error.response) return "Unable to reach the backend. Check that it is running and try again.";
    return fallback;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
