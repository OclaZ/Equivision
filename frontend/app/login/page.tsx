import { AuthForm } from "@/components/ui/auth-form";

export default function LoginPage() {
  return (
    <div className="flex w-full min-h-screen justify-center items-center bg-[var(--color-bg)]">
      <AuthForm mode="login" />
    </div>
  );
}
