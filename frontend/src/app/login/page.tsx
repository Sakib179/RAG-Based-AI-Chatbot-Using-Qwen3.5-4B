"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage } from "@/utils/errors";
import { useState } from "react";

const loginSchema = z.object({ email: z.string().email("Enter a valid email address."), password: z.string().min(8, "Password must be at least 8 characters.") });
type LoginValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginValues>();

  const onSubmit = async (values: LoginValues) => {
    setError("");
    const parsed = loginSchema.safeParse(values);
    if (!parsed.success) { setError(parsed.error.issues[0]?.message ?? "Check your details."); return; }
    try { await login(parsed.data.email, parsed.data.password); router.replace("/chat"); } catch (reason) { setError(getErrorMessage(reason, "Unable to sign in. Please try again.")); }
  };

  return <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 dark:bg-slate-950"><Card className="w-full max-w-md p-8"><div className="mb-8"><div className="mb-5 text-2xl text-teal-600">✦</div><h1 className="text-2xl font-bold text-slate-900 dark:text-white">Welcome back</h1><p className="mt-2 text-sm text-slate-500">Sign in to continue to your knowledge workspace.</p></div><form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate><label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Email<Input type="email" autoComplete="email" className="mt-2" {...register("email")} />{errors.email && <span className="mt-1 block text-xs text-rose-600">{errors.email.message}</span>}</label><label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Password<Input type="password" autoComplete="current-password" className="mt-2" {...register("password")} />{errors.password && <span className="mt-1 block text-xs text-rose-600">{errors.password.message}</span>}</label>{error && <p role="alert" className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-950/30 dark:text-rose-300">{error}</p>}<Button type="submit" className="w-full" disabled={isSubmitting}>{isSubmitting ? "Signing in…" : "Sign in"}</Button></form><p className="mt-6 text-center text-sm text-slate-500">New here? <Link href="/register" className="font-semibold text-teal-600 hover:text-teal-700">Create an account</Link></p></Card></main>;
}
