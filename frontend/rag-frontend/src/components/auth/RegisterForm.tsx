"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/hooks/useAuth";

/**
 * Registration validation schema
 */
const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, "Username must be at least 3 characters")
      .max(20, "Username must be less than 20 characters")
      .regex(/^[a-zA-Z0-9_]+$/, "Username can only contain letters, numbers, and underscores"),
    email: z.string().email("Invalid email address"),
    full_name: z.string().optional(),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"], // Error appears on confirmPassword field
  });

type RegisterFormData = z.infer<typeof registerSchema>;

/**
 * Register form component
 */
export function RegisterForm() {
  const { register: registerUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setIsLoading(true);
      // Remove confirmPassword before sending to API
      const { confirmPassword, ...registerData } = data;
      await registerUser(registerData);
      // Hook handles redirect and error handling
    } catch (error: any) {
      // Handle backend validation errors
      const errorData = error.response?.data;

      if (errorData?.detail) {
        // Parse backend error messages
        const detail = errorData.detail.toLowerCase();

        if (detail.includes("username") && detail.includes("exist")) {
          setError("username", {
            type: "manual",
            message: "This username is already taken",
          });
        } else if (detail.includes("email") && detail.includes("exist")) {
          setError("email", {
            type: "manual",
            message: "This email is already registered",
          });
        }
      }

      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Create an account
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Start chatting with your documents
        </p>
      </div>

      {/* Username */}
      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input
          id="username"
          placeholder="johndoe"
          {...register("username")}
          disabled={isLoading}
          className={errors.username ? "border-red-500" : ""}
        />
        {errors.username && (
          <p className="text-sm text-red-500">{errors.username.message}</p>
        )}
      </div>

      {/* Email */}
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="john@example.com"
          {...register("email")}
          disabled={isLoading}
          className={errors.email ? "border-red-500" : ""}
        />
        {errors.email && (
          <p className="text-sm text-red-500">{errors.email.message}</p>
        )}
      </div>

      {/* Full Name (Optional) */}
      <div className="space-y-2">
        <Label htmlFor="full_name">
          Full Name <span className="text-slate-400">(optional)</span>
        </Label>
        <Input
          id="full_name"
          placeholder="John Doe"
          {...register("full_name")}
          disabled={isLoading}
        />
      </div>

      {/* Password */}
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          placeholder="••••••••"
          {...register("password")}
          disabled={isLoading}
          className={errors.password ? "border-red-500" : ""}
        />
        {errors.password && (
          <p className="text-sm text-red-500">{errors.password.message}</p>
        )}
      </div>

      {/* Confirm Password */}
      <div className="space-y-2">
        <Label htmlFor="confirmPassword">Confirm Password</Label>
        <Input
          id="confirmPassword"
          type="password"
          placeholder="••••••••"
          {...register("confirmPassword")}
          disabled={isLoading}
          className={errors.confirmPassword ? "border-red-500" : ""}
        />
        {errors.confirmPassword && (
          <p className="text-sm text-red-500">{errors.confirmPassword.message}</p>
        )}
      </div>

      {/* Submit button */}
      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating account...
          </>
        ) : (
          "Create account"
        )}
      </Button>

      {/* Login link */}
      <p className="text-center text-sm text-slate-600 dark:text-slate-400">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400"
        >
          Log in
        </Link>
      </p>
    </form>
  );
}