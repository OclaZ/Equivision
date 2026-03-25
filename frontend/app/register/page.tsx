import { AuthForm } from "@/components/ui/auth-form";

export default function RegisterPage() {
  return (
    <div className="flex w-full min-h-screen justify-center items-center bg-[var(--color-bg)]">
      <AuthForm mode="register" />
    </div>
  );
}
