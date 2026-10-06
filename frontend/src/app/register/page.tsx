"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage } from "@/utils/errors";

const registerSchema = z.object({ email: z.string().email("Enter a valid email address."), password: z.string().min(8, "Password must be at least 8 characters.") });
type RegisterValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser } = useAuth();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterValues>();

  const onSubmit = async (values: RegisterValues) => {
    setError(""); setNotice("");
    const parsed = registerSchema.safeParse(values);
    if (!parsed.success) { setError(parsed.error.issues[0]?.message ?? "Check your details."); return; }
    try { const result = await registerUser(parsed.data.email, parsed.data.password); if (result.needsEmailConfirmation) { setNotice("Check your email to confirm your account, then sign in."); } else router.replace("/chat"); } catch (reason) { setError(getErrorMessage(reason, "Unable to create your account. Please try again.")); }
  };

  return <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 dark:bg-slate-950"><Card className="w-full max-w-md p-8"><div className="mb-8"><div className="mb-5 text-2xl text-teal-600">✦</div><h1 className="text-2xl font-bold text-slate-900 dark:text-white">Create your account</h1><p className="mt-2 text-sm text-slate-500">Start asking questions of your private knowledge base.</p></div><form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate><label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Email<Input type="email" autoComplete="email" className="mt-2" {...register("email")} />{errors.email && <span className="mt-1 block text-xs text-rose-600">{errors.email.message}</span>}</label><label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Password<Input type="password" autoComplete="new-password" className="mt-2" {...register("password")} />{errors.password && <span className="mt-1 block text-xs text-rose-600">{errors.password.message}</span>}</label>{error && <p role="alert" className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-950/30 dark:text-rose-300">{error}</p>}{notice && <p role="status" className="rounded-xl bg-teal-50 px-3 py-2 text-sm text-teal-700 dark:bg-teal-950/30 dark:text-teal-300">{notice}</p>}<Button type="submit" className="w-full" disabled={isSubmitting}>{isSubmitting ? "Creating account…" : "Create account"}</Button></form><p className="mt-6 text-center text-sm text-slate-500">Already registered? <Link href="/login" className="font-semibold text-teal-600 hover:text-teal-700">Sign in</Link></p></Card></main>;
}
