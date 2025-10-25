import { LoginButton } from './components/LoginButton';
import { Footer } from './components/Footer';
import { withAuth } from '@workos-inc/authkit-nextjs';
import { redirect } from 'next/navigation';

export default async function Home() {
  const { user } = await withAuth();
  
  if (!user) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <div className="flex-1 flex flex-col items-center justify-center gap-8 px-8">
          <h1 className="text-4xl font-bold text-foreground text-center leading-tight">Sign in or create your account</h1>
          <LoginButton />
        </div>
        <Footer />
      </div>
    );
  }
  
  // Redirect authenticated users to dashboard
  redirect('/dashboard');
}
