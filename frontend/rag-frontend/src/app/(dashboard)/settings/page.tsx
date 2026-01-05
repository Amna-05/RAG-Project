"use client";

import { useState } from "react";
import { User, Lock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import useAuthStore from "@/lib/store/authStore";
import { apiClient } from "@/lib/api/client";

/**
 * Settings Page
 *
 * Manage user account with backend integration
 */
export default function SettingsPage() {
  const { user } = useAuthStore();
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isLoadingPassword, setIsLoadingPassword] = useState(false);

  // Profile form
  const [fullName, setFullName] = useState(user?.full_name || "");

  // Password form
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    // Profile update feature will be available in a future version
    toast.info("Profile update coming soon!");
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }

    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setIsLoadingPassword(true);

    try {
      await apiClient.post("/auth/change-password", {
        old_password: oldPassword,
        new_password: newPassword,
      });

      toast.success("Password changed successfully! Please log in again.");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");

      // Redirect to login after password change
      setTimeout(() => {
        window.location.href = "/login";
      }, 1000);
    } catch (error: any) {
      console.error("Password change error:", error);
      const errorMessage = error.response?.data?.detail || error.message || "Failed to change password";
      toast.error(errorMessage);
    } finally {
      setIsLoadingPassword(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          Settings
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          Manage your account and preferences
        </p>
      </div>

      {/* Profile Section */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <User className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Profile
          </h2>
        </div>

        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {/* Username (Read-only) */}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={user?.username || ""}
                disabled
                className="bg-slate-100 dark:bg-slate-800"
              />
            </div>

            {/* Email (Read-only) */}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                value={user?.email || ""}
                disabled
                className="bg-slate-100 dark:bg-slate-800"
              />
            </div>
          </div>

          {/* Full Name */}
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <Input
              id="fullName"
              placeholder="John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          <Button disabled={isLoadingProfile} className="gap-2">
            {isLoadingProfile ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              "Save Profile"
            )}
          </Button>
        </form>
      </div>

      {/* Security Section */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30">
            <Lock className="h-5 w-5 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Security
          </h2>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4">
          {/* Old Password */}
          <div className="space-y-2">
            <Label htmlFor="oldPassword">Current Password</Label>
            <Input
              id="oldPassword"
              type="password"
              placeholder="••••••••"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              required
            />
          </div>

          {/* New Password */}
          <div className="space-y-2">
            <Label htmlFor="newPassword">New Password</Label>
            <Input
              id="newPassword"
              type="password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Minimum 8 characters
            </p>
          </div>

          {/* Confirm Password */}
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm New Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>

          <Button
            disabled={isLoadingPassword}
            className="gap-2"
            variant="destructive"
          >
            {isLoadingPassword ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Changing...
              </>
            ) : (
              "Change Password"
            )}
          </Button>
        </form>
      </div>

      {/* Account Info */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-blue-50 dark:bg-blue-900/20 p-4">
        <p className="text-sm text-blue-900 dark:text-blue-200">
          <strong>Account created:</strong>{" "}
          {user?.created_at
            ? new Date(user.created_at).toLocaleDateString()
            : "Unknown"}
        </p>
      </div>
    </div>
  );
}
