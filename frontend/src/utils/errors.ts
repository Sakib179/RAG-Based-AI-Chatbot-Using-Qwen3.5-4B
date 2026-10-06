export function getErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (typeof error === "object" && error !== null) {
    const candidate = error as { isAxiosError?: boolean; response?: { data?: { message?: string } } };
    if (candidate.response?.data?.message) return candidate.response.data.message;
    if (candidate.isAxiosError) return fallback;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
